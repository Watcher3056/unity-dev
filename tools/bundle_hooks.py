#!/usr/bin/env python3
"""Compose the skill and pinned Graph hook responses within one self-contained plugin."""
import importlib.util
import io
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def run(name, raw):
    """One part's answer to the event: its printed JSON, {} when it says nothing or fails."""
    spec = importlib.util.spec_from_file_location(name, HERE / f"{name}.py")
    if spec is None:
        return {}
    stdin, stdout = sys.stdin, sys.stdout
    sys.stdin = io.TextIOWrapper(io.BytesIO(raw))
    sys.stdout = out = io.StringIO()
    try:
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        mod.main()
    except SystemExit:
        pass
    except Exception as e:  # a broken part must never stop the agent's work, nor the other part
        print(f"bundle hook {name}: {e}", file=sys.stderr)
    finally:
        sys.stdin, sys.stdout = stdin, stdout
    try:
        return json.loads(out.getvalue().strip() or "{}")
    except ValueError:
        return {}


def main():
    raw = sys.stdin.buffer.read()
    answers = [run(name, raw) for name in ("skills_part", "trace_hooks")]
    blocks = [a for a in answers if a.get("decision") == "block"]
    if blocks:
        print(json.dumps({"decision": "block", "reason": " ".join(a.get("reason", "") for a in blocks).strip()}))
        return
    notes = [((a.get("hookSpecificOutput") or {}).get("additionalContext") or "") for a in answers]
    event = next(((a.get("hookSpecificOutput") or {}).get("hookEventName") for a in answers if a.get("hookSpecificOutput")), None)
    said = [a.get("systemMessage") for a in answers if a.get("systemMessage")]
    out = {}
    if any(notes) and event:
        out["hookSpecificOutput"] = {"hookEventName": event, "additionalContext": "\n\n".join(n for n in notes if n)}
    if said:
        out["systemMessage"] = "\n".join(said)
    if out:
        print(json.dumps(out))


if __name__ == "__main__":
    main()
