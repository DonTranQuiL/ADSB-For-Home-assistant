#!/usr/bin/env python3
"""AI self-healing: reads failed_logs.txt and proposes a whole-file fix for the
broken file (integration, tests, ai_engineer or requirements only).

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


import re  # noqa: E402

try:
    with open("failed_logs.txt", encoding="utf-8", errors="replace") as fh:
        logs = fh.read()[-4000:]
except FileNotFoundError:
    print("No failed_logs.txt found. Exiting.")
    raise SystemExit(0) from None

comp = _component()
project = _project_name()

# Find the first existing file mentioned in the logs (ruff "--> path:", pytest
# "path.py:12", tracebacks 'File "path"'), preferring the integration/tests.
file_path = None
for cand in re.findall(r"([A-Za-z0-9_./\-]+\.(?:py|json|yaml|yml))", logs):
    cand = cand.lstrip("./")
    if "/github/workspace/" in cand:
        cand = cand.split("/github/workspace/", 1)[1]
    if os.path.isfile(cand) and not cand.startswith((".github/", ".git/")):
        file_path = cand
        break

file_content = "File content could not be loaded."
if file_path:
    with open(file_path, encoding="utf-8") as fh:
        file_content = fh.read()

prompt = f"""
You are the AI Self-Healing Mechanic for '{project}'. Your persona is Snoop Dogg.
The CI pipeline just tripped up, but you stay relaxed and fix the engine while it's running.

The error occurred in this file: {file_path}

Here is the broken code:
{file_content}

Here is the error log:
{logs}

1. Drop a quick 1-2 sentence explanation of why it broke, in Snoop Dogg's smooth slang.
2. Provide the COMPLETELY FIXED file. Keep the code strictly professional.

IMPORTANT: Start your response with the exact line:
FILEPATH: {file_path}
Then your short explanation.
Then output the fixed file starting with CODE: and then a ```python block.
"""

try:
    response_text = _ask(prompt)
    print("\n--- AI MECHANIC REPORT ---")
    print(response_text)
    print("--------------------------\n")
    allowed = ["tests/", "ai_engineer/", "requirements"]
    if comp is not None:
        allowed.insert(0, f"{comp.as_posix()}/")
    patched = False
    for raw, content in _parse_files(response_text)[:1]:
        target = _safe_path(raw, tuple(allowed))
        if target:
            _write(target, content)
            patched = True
    if not patched:
        print("Failed to parse the patched code from the AI response.")
except SystemExit:
    raise
except Exception as exc:
    print(f"Repair failed: {exc}")
