#!/usr/bin/env python3
"""Build this skill for Codex or Claude Code; Unity-dev embeds its pinned Graph dependency."""
import argparse
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time
import tomllib

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "tools"))
import validate_skill
PRODUCT = json.loads((REPO / "product.json").read_text(encoding="utf-8"))
NAME = PRODUCT["name"]
SKILLS = [PRODUCT["skill"]]
if PRODUCT.get("graph"):
    import role_digests
HOST = "codex"
SKILL_SRC = {}
SKILL_HOOKS = REPO / "skills-plugin"
SKIP = shutil.ignore_patterns("__pycache__", "*.pyc")
PLACEHOLDER = re.compile(r"\{\{([a-z][a-z0-9-]*)\}\}")
MAX_SKILL_FILE = 26100
CHARS_PER_TOKEN = 3.0
TOKEN_CAP = 8700
OUT_ROOT = REPO / "dist"
CLAUDE_HOOK = ('for p in python3 python py; do c=$(command -v "$p" 2>/dev/null) || continue; '
               'case "$c" in *WindowsApps*) continue;; esac; exec "$c" "${CLAUDE_PLUGIN_ROOT}/scripts/SCRIPT"; done; exit 0')


def out_dir(name):
    return OUT_ROOT / name


def write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def retain(path):
    if path.exists():
        backup = path.parent / ".previous" / f"{path.name}-{time.time_ns()}"
        backup.parent.mkdir(parents=True, exist_ok=True)
        path.rename(backup)


def git(root, *args):
    result = subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True)
    if result.returncode:
        raise ValueError(result.stderr.strip() or "Git source unavailable")
    return result.stdout.strip()


def graph_pin():
    path = "vendor/flow-ai-graph"
    graph = REPO / path
    entry = git(REPO, "ls-files", "--stage", "--", path).split()
    if not graph.joinpath("tools/build_plugin.py").is_file() or len(entry) < 2 or entry[0] != "160000":
        raise ValueError("Graph submodule is missing; run git submodule update --init --recursive")
    expected = entry[1]
    if git(graph, "rev-parse", "HEAD") != expected:
        raise ValueError("Graph HEAD differs from the pinned gitlink; run git submodule update --init --recursive")
    if git(graph, "status", "--porcelain"):
        raise ValueError("Graph submodule is dirty; build the exact pinned Graph source")
    return graph, expected


def host_words():
    f = REPO / "hosts" / f"{HOST}.toml"
    if not f.exists():
        sys.exit(f"no {f.relative_to(REPO)}: the words of host '{HOST}' (hosts/: {', '.join(p.stem for p in (REPO / 'hosts').glob('*.toml'))})")
    return tomllib.loads(f.read_text(encoding="utf-8"))

def put_host_words(skill_dir, words, used):
    """Puts the host's words where the skill text has {{key}}. A line left with nothing but a list mark (the host has no
    such tool, its value is empty) goes away whole. Returns the problems: a key the host doesn't define, etc."""
    errors = []
    for f in sorted(skill_dir.rglob("*.md")):
        with open(f, encoding="utf-8", newline="") as fh:  # the file's own line endings stay
            text = fh.read()
        if "{{" not in text:
            continue
        out, where = [], f.relative_to(skill_dir.parent)
        for n, line in enumerate(text.splitlines(keepends=True), 1):
            keys = PLACEHOLDER.findall(line)
            missing = sorted({k for k in keys if k not in words})
            if missing:
                errors.append(f"{where}:{n}: hosts/{HOST}.toml has no {', '.join(missing)}")
            used.update(keys)
            line = PLACEHOLDER.sub(lambda m: words.get(m.group(1), m.group(0)), line)
            if keys and not line.strip(" \t\r\n-*"):
                continue
            if "{{" in line and not missing:
                errors.append(f"{where}:{n}: '{{{{' that isn't a {{{{key}}}} placeholder")
            out.append(line)
        with open(f, "w", encoding="utf-8", newline="") as fh:
            fh.write("".join(out))
    return errors

def other_hosts_words(words, host):
    """What names another host in a skill's text: its name and the code spans of its values (tool names, config paths,
    etc.), less the ones this host shares and plain one-word spans (`url`, `command`) that any text may use."""
    def spans(w):
        return {s for v in w.values() if isinstance(v, str) for s in re.findall(r"`([^`]+)`", v) if not re.fullmatch(r"[a-z]+", s)}
    mine, found = spans(words), {}
    for f in sorted((REPO / "hosts").glob("*.toml")):
        if f.stem != host:
            other = tomllib.loads(f.read_text(encoding="utf-8"))
            for s in spans(other) - mine:
                found.setdefault(f"`{s}`", f.name)
            if other.get("host") and other["host"] != words.get("host"):
                found.setdefault(other["host"], f.name)
    return found

def host_word_leaks(skills_dir, words, host):
    """Another host's words in a host's render of the skills: a rule that names a host's tool, config or limit belongs
    under a {{key}} (AGENTS.md rule 13). Printed as a warning, not failed: the author decides where the word goes."""
    found = other_hosts_words(words, host)
    out = []
    for f in sorted(skills_dir.rglob("*.md")):
        text = f.read_text(encoding="utf-8")
        for w, src in found.items():
            if re.search(r"(?<![\w-])" + re.escape(w) + r"(?![\w-])", text):
                out.append(f"{host} build, {f.relative_to(skills_dir)}: {w} is a word of hosts/{src}; put it under a {{{{key}}}} (AGENTS.md rule 13)")
    return out

def copy_skills(out):
    """The skills with the host's words in, their role sets and agent roles, and their hooks."""
    words, used = host_words(), set()
    skip = SKIP if HOST == "codex" else shutil.ignore_patterns("__pycache__", "*.pyc", "openai.yaml")  # Codex's own UI card
    for name in SKILLS:
        shutil.copytree(Path(SKILL_SRC[name]) if name in SKILL_SRC else REPO / "skills" / name, out / "skills" / name, ignore=skip)
        errors = put_host_words(out / "skills" / name, words, used)
        if errors:
            sys.exit(f"host words in {name}:\n  " + "\n  ".join(errors))
    unused = sorted(set(words) - used)
    if unused and not SKILL_SRC:
        print(f"hosts/{HOST}.toml: no skill uses {', '.join(unused)}")
    if not SKILL_SRC:
        for leak in host_word_leaks(out / "skills", words, HOST):
            print("host word: " + leak)
    for name in SKILLS:
        if (out / "skills" / name / "roles.json").exists():
            errors = role_digests.build(out / "skills" / name, out / "skills" / name / "roles", MAX_SKILL_FILE, out / "agents", HOST)
            if errors:
                sys.exit(f"role sets of {name}:\n  " + "\n  ".join(errors))
    shutil.copytree(SKILL_HOOKS / "scripts", out / "scripts", ignore=SKIP, dirs_exist_ok=True)

def write_hooks(out, sources=(), merged=None):
    """The plugin's hooks file from the Codex hooks files of its parts (one source each), merged event by event, or
    from an already merged table of events; for Claude Code, rewritten into its form."""
    merged = dict(merged or {})
    for src in sources:
        for event, groups in json.loads(src.read_text(encoding="utf-8"))["hooks"].items():
            merged.setdefault(event, []).extend(groups)
    data = claude_hooks(merged) if HOST == "claude" else {"hooks": merged}
    (out / "hooks").mkdir(exist_ok=True)
    (out / "hooks" / "hooks.json").write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

def bundle_events(skills_src, graph_src):
    """A benchmark arm's hook events: each event of the skills' hooks file as it is, and each event only the graph's
    file has as it is, so every entry stands where the user's trust for the plugin it came from puts it."""
    skills = json.loads(skills_src.read_text(encoding="utf-8"))["hooks"]
    graph = json.loads(graph_src.read_text(encoding="utf-8"))["hooks"]
    return {**{ev: groups for ev, groups in graph.items() if ev not in skills}, **skills}

def claude_hooks(src):
    """Hooks for Claude Code, from the Codex hooks (one source): the same events, matchers, scripts and timeouts."""
    out = {}
    for event, groups in src.items():
        for g in groups:
            hooks = []
            for h in g["hooks"]:
                script = re.search(r"'scripts','(\w+\.py)'", h["command"])
                if not script:
                    sys.exit(f"hooks.json: {event}: no script named in its command")
                hooks.append({"type": "command", "command": CLAUDE_HOOK.replace("SCRIPT", script.group(1)), "timeout": h.get("timeout", 15)})
            out.setdefault(event, []).append({**({"matcher": g["matcher"]} if g.get("matcher") else {}), "hooks": hooks})
    return {"hooks": out}

def size(f):
    """A skill file's size as rule 9 counts it: its text with LF line ends, as git keeps it (a Windows checkout's CR
    would add a byte per line that no rule wrote)."""
    return len(f.read_bytes().replace(b"\r\n", b"\n"))

def too_big():
    sizes = sorted(((size(f), f) for f in (out_dir(NAME) / "skills").rglob("*.md")), reverse=True)
    for n, f in sizes[:6]:
        print(f"  ~{n / CHARS_PER_TOKEN:5.0f} tokens  {f.relative_to(out_dir(NAME))}")
    big = [(f, n) for n, f in sizes if n > MAX_SKILL_FILE]
    for f, n in big:
        print(f"too big to read in one call: {f.relative_to(out_dir(NAME))} {n} chars (~{n / CHARS_PER_TOKEN:.0f} tokens, cap {TOKEN_CAP}); "
              "move rules to a file of their own")
    return bool(big) | too_big_elsewhere()

def too_big_elsewhere():
    # Check alternate host renders in memory; do not make or discard diagnostic copies.
    big = False
    for host in sorted((REPO / "hosts").glob("*.toml")):
        if host.stem == HOST:
            continue
        words = tomllib.loads(host.read_text(encoding="utf-8"))
        for name in SKILLS:
            for md in (REPO / "skills" / name).rglob("*.md"):
                text = md.read_text(encoding="utf-8")
                missing = set(PLACEHOLDER.findall(text)) - set(words)
                if missing:
                    print(f"Missing host words in {host.name}: {sorted(missing)}")
                    big = True
                    continue
                text = PLACEHOLDER.sub(lambda m: words[m[1]], text)
                if len(text.encode("utf-8")) > MAX_SKILL_FILE:
                    print(f"Oversize alternate host render: {host.name} {md.relative_to(REPO)}")
                    big = True
    return big


def build(args):
    global HOST, OUT_ROOT
    HOST = args.host
    if args.install and args.dist_root:
        raise ValueError("--dist-root stages packages; it cannot be combined with --install")
    if not re.fullmatch(r"(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)", args.version):
        raise ValueError("--version must have three numeric components")
    OUT_ROOT = Path(args.dist_root).resolve() if args.dist_root else REPO / "dist" / ("claude-check" if HOST == "claude" else "")
    dependency = graph_pin() if PRODUCT.get("graph") else None
    out = out_dir(NAME)
    retain(out)
    out.mkdir(parents=True)
    copy_skills(out)
    skill_hooks = SKILL_HOOKS / "hooks/hooks.json"
    if dependency:
        graph, pin = dependency
        intermediate = OUT_ROOT / ".graph-builds" / str(time.time_ns())
        subprocess.run([sys.executable, str(graph / "tools/build_plugin.py"), "--host", HOST,
                        "--dist-root", str(intermediate), "--version", args.version,
                        "--python-command", args.python_command], check=True)
        built_graph = intermediate / "flow-ai-graph"
        for item in ("server.py", "layers.py", "claude_logs.py", "generic_logs.py", "mcp_graph.py", "web", "addons", "scripts", "FORMAT.md"):
            source = built_graph / item
            if source.is_dir():
                shutil.copytree(source, out / item, dirs_exist_ok=True, ignore=SKIP)
            else:
                shutil.copy2(source, out / item)
        (out / "scripts/skill_hooks.py").rename(out / "scripts/skills_part.py")
        shutil.copy2(REPO / "tools/bundle_hooks.py", out / "scripts/skill_hooks.py")
        write_hooks(out, merged=bundle_events(skill_hooks, graph / "trace-viewer/hooks/hooks.json"))
        for config in (".mcp.json", "mcp.json"):
            if (built_graph / config).exists():
                shutil.copy2(built_graph / config, out / config)
    else:
        write_hooks(out, [skill_hooks])
    if too_big():
        raise ValueError("Skill file-size validation failed")
    for name in SKILLS:
        errors = validate_skill.validate(out / "skills" / name)
        if errors:
            raise ValueError("; ".join(errors))
    for name in ("LICENSE", "THIRD_PARTY_NOTICES.md", "README.md"):
        shutil.copy2(REPO / name, out / name)
    shutil.copytree(REPO / "docs", out / "docs", ignore=shutil.ignore_patterns("media"))
    common = {"name": NAME, "version": args.version, "description": PRODUCT["description"], "author": {"name": "Watcher3056"}}
    face = {"displayName": PRODUCT["displayName"], "shortDescription": PRODUCT["shortDescription"],
            "longDescription": PRODUCT["description"], "developerName": "Watcher3056",
            "category": "Developer Tools" if dependency else "Productivity", "capabilities": ["Read"]}
    overlay = dict(common)
    if HOST == "codex":
        overlay.update(skills="./skills/", hooks="./hooks/hooks.json", interface=face)
        if dependency:
            overlay["mcpServers"] = "./.mcp.json"
    else:
        overlay["keywords"] = [NAME]
    write(out / (".codex-plugin" if HOST == "codex" else ".claude-plugin") / "plugin.json", overlay)
    if HOST == "codex":
        write(out / "plugin.json", {"$schema": "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json", **common,
                                     "extensions": {"com.openai": {"interface": face, "hooks": "./hooks/hooks.json"}}})
    commit = git(REPO, "rev-parse", "HEAD")
    if git(REPO, "status", "--porcelain"):
        commit += "+uncommitted"
    sources = {"product": NAME, "git": commit}
    if dependency:
        sources["dependencies"] = {"flow-ai-graph": {"git": dependency[1], "license": "MIT"}}
    write(out / "SOURCES.json", sources)
    print(f"Built {out} version {args.version}")
    return out


def install(args, out):
    if HOST == "claude":
        destination = REPO / "dist/claude" / NAME
        retain(destination)
        shutil.copytree(out, destination)
    client = shutil.which(HOST) or HOST
    commands = [[client, "plugin", "marketplace", "add", str(REPO)],
                [client, "plugin", "add" if HOST == "codex" else "install", f"{NAME}@{NAME}"]]
    for command in commands:
        result = subprocess.run(command)
        if result.returncode:
            return result.returncode
    if HOST == "codex" and (out / "agents").is_dir():
        destination = Path(os.environ.get("CODEX_HOME") or Path.home() / ".codex").expanduser() / "agents"
        destination.mkdir(parents=True, exist_ok=True)
        for role in (out / "agents").glob("*.toml"):
            shutil.copy2(role, destination / role.name)
    return 0


def main():
    global HOST
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", choices=("codex", "claude"), default="codex")
    parser.add_argument("--dist-root")
    parser.add_argument("--version", default="1.0." + time.strftime("%Y%m%d%H%M%S", time.gmtime()))
    parser.add_argument("--python-command", default="py" if os.name == "nt" else "python3")
    parser.add_argument("--install", action="store_true")
    parser.add_argument("--words")
    args = parser.parse_args()
    HOST = args.host
    try:
        if args.words:
            problems = put_host_words(Path(args.words).resolve(), host_words(), set())
            if problems:
                raise ValueError("; ".join(problems))
            return 0
        out = build(args)
        return install(args, out) if args.install else 0
    except (ValueError, OSError, subprocess.CalledProcessError) as exc:
        parser.exit(1, str(exc) + "\n")


if __name__ == "__main__":
    raise SystemExit(main())
