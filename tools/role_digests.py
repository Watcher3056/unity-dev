"""Per-role rule sets of a skill: each sub-agent role reads only the rules it needs, built from the skill's own files.

The files each role reads come from the skill's "Skill files by role" table in SKILL.md (one source); the skill's
`roles.json` says only what a role leaves out. A file is cut into blocks at its headings, numbered pipeline items,
tagged paragraphs and tagged bullets; a role gets every block of its files except the ones excluded for it, so a rule
is never lost by forgetting to list it. The build fails when:
- an exclusion names no block (the skill changed and the map is stale);
- a block reaches no sub-agent and isn't marked main-only (an exclusion by mistake, or a decision nobody made);
- a part of a role's set is too big to read in one call.

roles.json:
{
  "roles": {"<role>": {"row": "<the role's first cell in the table>", "exclude": ["<file>#<block id>", ...]}, ...},
  "main_only": ["<file>#<block id>", ...]
}
A block id is the tag the block starts with ("PIPE-QA", "PM-DRIVER"), or else its heading text.
"""
import json
import re
from pathlib import Path

START = re.compile(r"^(#{1,4} .+|\d+\. \[[A-Z][A-Z0-9-]+\].*|\[[A-Z][A-Z0-9-]+\].*|- \[[A-Z][A-Z0-9-]+\].*|\*\*[A-Z][^*]*:\*\*\s*$)")
TAG = re.compile(r"\[([A-Z][A-Z0-9-]+)\]")
LINK = re.compile(r"\]\((references/[^)]+\.md)\)")


def blocks(path):
    """[(id, text)] in file order; the lines before the first block start belong to the first block."""
    out, cur_id, cur = [], None, []
    for line in path.read_text(encoding="utf-8").replace("\r\n", "\n").split("\n"):
        if START.match(line):
            if cur_id is not None or cur:
                out.append((cur_id or "(start)", "\n".join(cur)))
            m = TAG.search(line)
            cur_id = m.group(1) if m and line.lstrip("#- 0123456789.").startswith("[") else line.strip("#* ").strip().rstrip(":")
            cur = [line]
        else:
            cur.append(line)
    out.append((cur_id or "(start)", "\n".join(cur)))
    return out


def table_rows(skill):
    """{first cell: [files]} from the "Skill files by role" table; every role also reads the files of the line above it."""
    text = (skill / "SKILL.md").read_text(encoding="utf-8").replace("\r\n", "\n").split("\n")
    every = next((l for l in text if l.startswith("Every role reads")), "")
    common = ["SKILL.md"] + LINK.findall(every)
    rows = {}
    for l in text:
        m = re.match(r"^\|\s*([^|]+?)\s*\|(.+)\|\s*$", l)
        if m and LINK.search(m.group(2)) or (m and "nothing more" in m.group(2)):
            rows[m.group(1)] = common + LINK.findall(m.group(2))
    return rows


def build(skill, out_dir, max_chars, agents_dir=None, host="codex"):
    """Writes out_dir/<role>-<n>.md and out_dir/map.md, and with agents_dir one agent role per set for the host: Codex
    (agents_dir/<skill>-<role>.toml, developer_instructions = the whole set) or Claude Code (agents_dir/<skill>-<role>.md,
    the whole set as the sub-agent's system prompt); returns a list of errors (empty when fine)."""
    cfg = json.loads((skill / "roles.json").read_text(encoding="utf-8"))
    rows = table_rows(skill)
    errors, sets, all_blocks = [], {}, {}
    used_excl, main_only = set(), set(cfg.get("main_only", []))
    for role, spec in cfg["roles"].items():
        files = rows.get(spec["row"])
        if files is None:
            errors.append(f"roles.json: role {role}: no row '{spec['row']}' in the Skill files by role table")
            continue
        excl = set(spec.get("exclude", [])) | main_only
        chosen = []
        for f in files:
            for bid, text in blocks(skill / f):
                key = f"{f}#{bid}"
                all_blocks.setdefault(key, text)
                if key in excl:
                    used_excl.add(key)
                else:
                    chosen.append((f, key, text))
        sets[role] = (files, chosen)
    known = set(all_blocks)
    for key in sorted((main_only | {e for s in cfg["roles"].values() for e in s.get("exclude", [])}) - known):
        errors.append(f"roles.json: '{key}' names no block of a file these roles read")
    reached = {k for _, chosen in sets.values() for _, k, _ in chosen}
    for key in sorted(known - reached - main_only):
        errors.append(f"roles.json: '{key}' reaches no sub-agent and isn't in main_only: decide who needs it")
    out_dir.mkdir(parents=True, exist_ok=True)
    whole = {}
    for role, (files, chosen) in sets.items():
        parts, cur, size = [], [], 0
        for f, key, text in chosen:
            piece = (f, relink(f, text))
            if cur and size + len(piece[1]) > max_chars - 4000:  # room for the header, the markers and multi-byte chars
                parts.append(cur); cur, size = [], 0
            cur.append(piece); size += len(piece[1]) + 1
        parts.append(cur)
        for n, part in enumerate(parts, 1):
            body, last = [], None
            for f, text in part:
                if f != last:
                    body.append(f"\n<!-- from {f} -->\n"); last = f
                body.append(text)
            head = (f"# unity-dev rules for the {spec_name(cfg, role)} (part {n} of {len(parts)})\n\n"
                    f"Built from {', '.join(files)} for this role: the rules of other roles are left out. Read every part "
                    "in full, one per call. A link to a skill file points to the full file, for a rule this set doesn't hold.\n")
            text = head + "\n".join(body) + "\n"
            whole.setdefault(role, (files, []))[1].extend(body)
            if len(text.encode("utf-8")) > max_chars:
                errors.append(f"roles/{role}-{n}.md is {len(text.encode('utf-8'))} bytes, more than {max_chars}: a single block is too big")
            (out_dir / f"{role}-{n}.md").write_text(text, encoding="utf-8")
    write_map(out_dir / "map.md", cfg, sets, all_blocks, main_only)
    if agents_dir is not None:
        errors += (write_claude_agents if host == "claude" else write_agent_roles)(skill, cfg, whole, agents_dir)
    return errors


def write_claude_agents(skill, cfg, whole, agents_dir):
    """A Claude Code sub-agent per set, shipped in the plugin's agents/ folder: the main thread spawns it with
    subagent_type `<plugin>:<skill>-<role>`, and the file's body, its whole rule set, is its system prompt."""
    agents_dir.mkdir(parents=True, exist_ok=True)
    for role, (files, body) in whole.items():
        name, who = f"{skill.name}-{role}", spec_name(cfg, role)
        head = (f"# {skill.name} rules for the {who}\n\n"
                f"You are the {who} of the {skill.name} skill. These are your rules, built from {', '.join(files)} "
                "for this role: the rules of other roles are left out. They are already in your context: nothing to read for them. "
                "A link to a skill file points to the full file, for a rule this set doesn't hold; the skill's folder is named "
                "in the note you get at your start.\n")
        desc = (f"The {who} of the {skill.name} skill. Spawned only by the {skill.name} skill's main thread, with a brief; "
                "its rules come as its system prompt.")
        text = (f"---\nname: {name}\ndescription: {json.dumps(desc, ensure_ascii=False)}\nmodel: inherit\n---\n\n"
                + head + "\n".join(body) + "\n")
        (agents_dir / f"{name}.md").write_text(text, encoding="utf-8", newline="\n")
    return []


def write_agent_roles(skill, cfg, whole, agents_dir):
    """A Codex agent role per set: the main thread spawns a sub-agent with agent_type `<skill>-<role>`, and the role's
    developer_instructions put its whole rule set into its context before its first step, with nothing to read and
    no tool-output cap on the way (Codex: ~/.codex/agents/<name>.toml, or the agents/ folder of a Codex home)."""
    errors = []
    agents_dir.mkdir(parents=True, exist_ok=True)
    q = "'" * 3
    for role, (files, body) in whole.items():
        name = f"{skill.name}-{role}"
        head = (f"# {skill.name} rules for the {spec_name(cfg, role)}\n\n"
                f"You are the {spec_name(cfg, role)} of the {skill.name} skill. These are your rules, built from {', '.join(files)} "
                "for this role: the rules of other roles are left out. They are already in your context: nothing to read for them. "
                "A link to a skill file points to the full file, for a rule this set doesn't hold; the skill's folder is named "
                "in the note you get at your start.\n")
        text = head + "\n".join(body) + "\n"
        if q in text:
            errors.append(f"agent role {name}: the rules contain ''' and can't be a TOML literal string"); continue
        toml = (f'name = "{name}"\n'
                f'description = "{spec_name(cfg, role)} of the {skill.name} skill; its rules come as developer instructions."\n'
                f"developer_instructions = {q}\n{text}{q}\n")
        (agents_dir / f"{name}.toml").write_text(toml, encoding="utf-8", newline="\n")
    return errors


def spec_name(cfg, role):
    return cfg["roles"][role]["row"]


def relink(f, text):
    """Links inside the set point at the full files, from the roles/ folder."""
    if f == "SKILL.md":
        return LINK.sub(lambda m: f"](../{m.group(1)})", text).replace("](SKILL.md", "](../SKILL.md")
    return re.sub(r"\]\(([\w-]+\.md)\)", lambda m: f"](../references/{m.group(1)})", text)


def write_map(path, cfg, sets, all_blocks, main_only):
    roles = list(sets)
    lines = ["# Which rule reaches which role", "", "Built from roles.json; ✓ — in the role's set, · — left out. Main: the main thread reads the files themselves.", "",
             "| Block | main | " + " | ".join(roles) + " |", "| --- | --- | " + " | ".join("---" for _ in roles) + " |"]
    for key in all_blocks:
        cells = ["✓" if any(k == key for _, k, _ in sets[r][1]) else ("·" if any(key.split("#")[0] == f for f in sets[r][0]) else "") for r in roles]
        lines.append(f"| {key} | ✓ | " + " | ".join(cells) + " |")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
