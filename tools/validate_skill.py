"""Validate this project's skill metadata. Runs in a clean checkout, independent of installed agents."""
import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    raise SystemExit("Build dependency missing: run python -m pip install -r requirements-dev.txt") from None


def validate(folder):
    folder = Path(folder)
    try:
        text = (folder / "SKILL.md").read_text(encoding="utf-8")
    except OSError as exc:
        return [str(exc)]
    front = re.match(r"\A---\r?\n(.*?)\r?\n---(?:\r?\n|\Z)", text, re.S)
    if not front:
        return ["SKILL.md needs YAML frontmatter"]
    try:
        meta = yaml.safe_load(front[1])
    except yaml.YAMLError as exc:
        return [f"invalid frontmatter: {exc}"]
    if not isinstance(meta, dict):
        return ["frontmatter must be a mapping"]
    errors = []
    if set(meta) - {"name", "description", "license", "allowed-tools", "metadata"}:
        errors.append("unsupported frontmatter properties")
    name = meta.get("name")
    if not isinstance(name, str) or not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", name) or len(name) > 64:
        errors.append("name must be nonempty kebab-case, at most 64 characters")
    elif name != folder.name:
        errors.append("name must match the skill folder")
    desc = meta.get("description")
    if not isinstance(desc, str) or not desc.strip() or len(desc) > 1024 or any(c in desc for c in "<>"):
        errors.append("description must be nonempty text, at most 1024 characters, with no angle brackets")
    for md in folder.rglob("*.md"):
        body = md.read_text(encoding="utf-8")
        if re.search(r"\{\{[a-z][a-z0-9-]*\}\}", body):
            errors.append(f"unresolved host words in {md.relative_to(folder)}")
        if re.search(r"(?m)^\s*\[TODO:.*\]\s*$", body):
            errors.append(f"unfinished instructions in {md.relative_to(folder)}")
    return errors


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("Usage: python tools/validate_skill.py <built-skill-folder>")
    problems = validate(sys.argv[1])
    print("\n".join(problems) if problems else "valid")
    raise SystemExit(bool(problems))
