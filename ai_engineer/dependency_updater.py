#!/usr/bin/env python3
"""AI dependency updater: bumps the auto-detected integration's manifest
requirements (and matching requirements*.txt pins) to the latest PyPI release,
skipping packages whose version Home Assistant itself manages. Writes
pr_title.txt / pr_body.txt for the workflow's pull request.

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

import requests  # noqa: E402

HA_RAW = "https://raw.githubusercontent.com/home-assistant/core/dev/"
# Every package Home Assistant pins (core constraints + all integrations).
HA_PIN_FILES = ("homeassistant/package_constraints.txt", "requirements_all.txt")
REQ_RE = re.compile(
    r"^\s*([A-Za-z0-9][A-Za-z0-9._\-]*)(\[[^\]]*\])?\s*(==|>=|~=)\s*([0-9][^,;\s]*)"
)


def _norm(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


def _vtuple(version: str) -> tuple[int, ...] | None:
    if not re.fullmatch(r"\d+(\.\d+)*", version):
        return None  # skip pre-releases / unusual versions
    return tuple(int(p) for p in version.split("."))


comp = _component()
if comp is None:
    print("No integration found under custom_components/. Nothing to update.")
    raise SystemExit(0)
manifest_path = comp / "manifest.json"
manifest = _manifest()
requirements = manifest.get("requirements") or []
if not requirements:
    print(f"{manifest_path} has no requirements. Nothing to update.")
    raise SystemExit(0)

# Packages Home Assistant itself pins must follow HA (hassfest enforces this).
ha_pinned: set[str] = set()
try:
    for pin_file in HA_PIN_FILES:
        resp = requests.get(HA_RAW + pin_file, timeout=30)
        resp.raise_for_status()
        ha_pinned |= {
            _norm(m.group(1))
            for line in resp.text.splitlines()
            if (m := re.match(r"^\s*([A-Za-z0-9][\w.\-]*)\s*[=<>~]", line))
        }
except Exception as exc:
    print(f"Could not load Home Assistant pins ({exc}); not bumping anything.")
    raise SystemExit(0) from None
print(f"Loaded {len(ha_pinned)} Home Assistant-managed package pins.")

bumps: list[tuple[str, str, str]] = []
new_requirements: list[str] = []
for req in requirements:
    m = REQ_RE.match(req)
    if not m:
        new_requirements.append(req)
        continue
    name, extras, op, current = m.group(1), m.group(2) or "", m.group(3), m.group(4)
    if _norm(name) in ha_pinned:
        print(f"Skipping {name}: version is managed by Home Assistant.")
        new_requirements.append(req)
        continue
    try:
        info = requests.get(f"https://pypi.org/pypi/{name}/json", timeout=30)
        info.raise_for_status()
        latest = info.json()["info"]["version"]
    except Exception as exc:
        print(f"Could not check {name} on PyPI: {exc}")
        new_requirements.append(req)
        continue
    cur_t, new_t = _vtuple(current), _vtuple(latest)
    if cur_t is None or new_t is None or new_t <= cur_t:
        print(f"{name} is up to date ({current}; PyPI latest {latest}).")
        new_requirements.append(req)
        continue
    print(f"🚨 New version detected: {name} {current} -> {latest}")
    bumps.append((name, current, latest))
    new_requirements.append(f"{name}{extras}{op}{latest}")

if not bumps:
    print("All integration requirements are up to date.")
    raise SystemExit(0)

summary = ", ".join(f"{n} {o} → {v}" for n, o, v in bumps)
if DRY_RUN:
    print(f"[dry-run] would update {manifest_path} and requirements*.txt: {summary}")
    raise SystemExit(0)

text = manifest_path.read_text(encoding="utf-8")
for old, new in zip(requirements, new_requirements, strict=True):
    if old != new:
        text = text.replace(json.dumps(old), json.dumps(new))
manifest_path.write_text(text, encoding="utf-8")
print(f"✅ Updated {manifest_path}")

for req_file in sorted(Path(".").glob("requirements*.txt")):
    content = req_file.read_text(encoding="utf-8")
    updated = content
    for name, _old, latest in bumps:
        updated = re.sub(
            rf"(?im)^({re.escape(name)}(\[[^\]]*\])?\s*==\s*)[0-9][^\s;#]*",
            rf"\g<1>{latest}",
            updated,
        )
    if updated != content:
        req_file.write_text(updated, encoding="utf-8")
        print(f"✅ Updated {req_file}")

project = _project_name()
title = (
    f"⬆️ Bump {bumps[0][0]} from {bumps[0][1]} to {bumps[0][2]}"
    if len(bumps) == 1
    else f"⬆️ Bump {len(bumps)} integration dependencies"
)
body = f"Automated dependency update for {project}: {summary}."
try:
    if os.getenv("XAI_API_KEY") or os.getenv("OPENROUTER_API_KEY"):
        body = (
            _ask(
                f"You are the AI Staff Engineer for '{project}'. Your persona is Snoop Dogg.\n"
                f"You automatically bumped these packages in the manifest and requirements "
                f"files: {summary}.\nWrite a smooth, professional, yet Snoop-styled Pull "
                "Request description explaining the update. Do NOT use triple backticks "
                "or code blocks. Just output the raw text."
            )
            or body
        )
except Exception as exc:
    print(f"PR description generation failed, using plain text: {exc}")

with open("pr_body.txt", "w", encoding="utf-8") as fh:
    fh.write(body + "\n")
with open("pr_title.txt", "w", encoding="utf-8") as fh:
    fh.write(title)
