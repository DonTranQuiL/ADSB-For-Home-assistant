#!/usr/bin/env python3
"""AI test writer: turns merged_diff.txt into new pytest tests under tests/.

Generic DonTranQuiL template script, synced from ai-home-assistant-template.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

# --- shared helpers (kept inline so every synced script is self-contained) ---
DRY_RUN = "--dry-run" in sys.argv or os.getenv("AI_DRY_RUN") == "1"
if "--help" in sys.argv or "-h" in sys.argv:
    print(__doc__)
    print("Options: --dry-run (or AI_DRY_RUN=1) builds the prompt, calls no LLM,")
    print("writes nothing. AI_COMPONENT_DIR overrides integration auto-detection.")
    raise SystemExit(0)


def _component() -> Path | None:
    """Return the integration folder under custom_components/ (auto-detected)."""
    override = os.getenv("AI_COMPONENT_DIR")
    if override:
        path = Path(override)
        return path if path.is_dir() else None
    root = Path("custom_components")
    if not root.is_dir():
        return None
    found = sorted(p for p in root.iterdir() if (p / "manifest.json").is_file())
    if not found:
        return None
    if len(found) > 1:
        print(f"Several integrations found, using {found[0]}: {found}")
    return found[0]


def _manifest() -> dict:
    comp = _component()
    if comp is None:
        return {}
    try:
        return json.loads((comp / "manifest.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def _project_name() -> str:
    name = _manifest().get("name")
    if name:
        return str(name)
    repo = os.getenv("GITHUB_REPOSITORY") or os.getenv("REPO") or Path.cwd().name
    return repo.split("/")[-1].replace("-", " ").replace("_", " ").title()


def _llm_client():
    """xAI first (grok-4), then OpenRouter (deepseek/deepseek-v4.1-flash)."""
    from openai import OpenAI

    xai = os.getenv("XAI_API_KEY")
    if xai:
        return OpenAI(base_url="https://api.x.ai/v1", api_key=xai), "grok-4"
    or_key = os.getenv("OPENROUTER_API_KEY")
    if or_key:
        return (
            OpenAI(base_url="https://openrouter.ai/api/v1", api_key=or_key),
            "deepseek/deepseek-v4.1-flash",
        )
    print("No XAI_API_KEY or OPENROUTER_API_KEY — exiting cleanly.")
    raise SystemExit(0)


def _ask(prompt: str) -> str:
    if DRY_RUN:
        print(f"[dry-run] component={_component()} project={_project_name()!r}")
        print(f"[dry-run] prompt has {len(prompt)} chars; no LLM call made.")
        raise SystemExit(0)
    client, model = _llm_client()
    print(f"Using model {model}")
    completion = client.chat.completions.create(
        model=model, messages=[{"role": "user", "content": prompt}]
    )
    return (completion.choices[0].message.content or "").strip()


def _safe_path(raw: str, allowed: tuple[str, ...]) -> Path | None:
    """Accept only repo-relative paths under one of the allowed prefixes."""
    raw = raw.strip().strip("`").strip()
    if not raw:
        return None
    path = Path(raw)
    if path.is_absolute() or ".." in path.parts:
        print(f"Refusing unsafe path: {raw}")
        return None
    norm = path.as_posix()
    if not any(norm == a.rstrip("/") or norm.startswith(a) for a in allowed):
        print(f"Refusing path outside {allowed}: {raw}")
        return None
    return path


def _parse_files(text: str) -> list[tuple[str, str]]:
    """Parse FILEPATH: <path> ... CODE: ```lang ... ``` blocks."""
    fence = "`" * 3
    results: list[tuple[str, str]] = []
    target, code, in_code = None, [], False
    for line in text.splitlines():
        if line.startswith("FILEPATH:"):
            if target and code:
                results.append((target, "\n".join(code)))
            target, code, in_code = line.split(":", 1)[1].strip(), [], False
        elif not in_code and (line.startswith("CODE:") or line.startswith(fence)):
            in_code = True
        elif in_code and line.startswith(fence):
            if not code:
                continue  # opening fence right after CODE:
            in_code = False
            if target and code:
                results.append((target, "\n".join(code)))
                target, code = None, []
        elif in_code:
            code.append(line)
    if target and code:
        results.append((target, "\n".join(code)))
    return results


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.rstrip("\n") + "\n", encoding="utf-8")
    print(f"Wrote {path}")


# --- end shared helpers ---


try:
    with open("merged_diff.txt", encoding="utf-8", errors="replace") as fh:
        diff_text = fh.read()
except FileNotFoundError:
    print("No merged_diff.txt found. Exiting.")
    raise SystemExit(0) from None

if len(diff_text.strip()) < 10:
    print("Empty diff, nothing to test.")
    raise SystemExit(0)

comp = _component()
project = _project_name()
domain = comp.name if comp is not None else "the integration"
prompt = f"""
You are the AI Quality Assurance Engineer for '{project}' (Home Assistant custom
integration, domain `{domain}`). Your persona is Snoop Dogg.
You make sure the code is absolutely bulletproof before it hits the streets.

Here is the new code diff that needs testing:
{diff_text[-30000:]}

1. Write a quick intro in Snoop Dogg's voice explaining your test strategy.
2. Write robust `pytest` tests covering edge cases, standard usage and failures.
   Mock all network I/O; no live calls. Tests must be strictly professional.

IMPORTANT INSTRUCTIONS:
Start your response with the exact line:
FILEPATH: tests/test_generated.py
Then your intro. Then output the tests starting with CODE: and a python code block.

Sign off your intro exactly like this:
**By:** SnoopDogg
**Role:** AI QA Engineer for {project}
"""

try:
    response_text = _ask(prompt)
    files = _parse_files(response_text)
    wrote = False
    for raw, content in files:
        target = _safe_path(raw, ("tests/",))
        if target:
            _write(target, content)
            wrote = True
    if not wrote:
        print("Failed to extract FILEPATH or CODE from AI response.")
except SystemExit:
    raise
except Exception as exc:
    print(f"Test generation failed: {exc}")
