#!/usr/bin/env python3
"""Hooks of the unity-dev plugin: they keep a skill's rules in front of the agents that run it. They need nothing of
the graph (the ai-graph plugin): the task's skill comes from the trace the skill itself has its agents write, an agent's
name and role from the session logs.

- SubagentStart: names the skill files the sub-agent's role reads in full (its rule set from the build, else the skill's
  'Skill files by role' table), gives a tester the core of its Play Mode rules, and asks the sub-agent to save its brief
  and its final report as files.
- SubagentStop: a sub-agent that never read a file of its role is asked once to read it and check its work against it; a
  judge whose own trace holds no line with the bar's rows as attrs (RND-BAR) is asked once to write them.
- PostToolUse: a read of a skill file that came back cut is said at once. An R&D branch spawned by the main thread while
  the R&D stage has no direction sheet (RND-DIRS: the stage node's attrs, or the sheet file) is said at once. The first call after the client compacted an
  agent's context gets the agent's role files again, its brief (the main thread: the task's task.md and spec.md) and
  the tester's core rules: the rules it had read are only a summary after that, and a summary loses their exact words.
  The main thread doing a role's work, or waiting in short slices, while sub-agents are at work is told so at once.

Each hook returns at once unless a task of one of this plugin's skills is in progress in the session's project: the
skill's trace (.ai-profile/trace/<task>/main.jsonl) names the skill in its first line. Codex and Claude Code pass the
event as JSON on stdin with the same fields where it matters; the answer on stdout is JSON ("decision": "block" with a
"reason" asks the agent to go on). Where they differ (the plugin's folders, the session logs a sub-agent's name and role
come from), the Claude Code side is marked as such.
"""
import hashlib
import json
import os
import re
import sys
import time
from pathlib import Path

PORT = int(os.environ.get("AGENT_TRACE_PORT", "8765"))  # the graph's viewer, when it runs: who is at work
ACTIVE_FOR = 6 * 3600  # a trace untouched this long belongs to a finished task
TRACE = Path(".ai-profile") / "trace"  # where the skills have their agents write the task's trace (trace-agent.md)

CLAUDE = bool(os.environ.get("CLAUDE_PLUGIN_ROOT"))  # the hook runs in Claude Code, which sets its plugin's root


def plugin_root():
    return os.environ.get("PLUGIN_ROOT") or os.environ.get("CLAUDE_PLUGIN_ROOT")


def data_dir():
    return Path(os.environ.get("PLUGIN_DATA") or os.environ.get("CLAUDE_PLUGIN_DATA") or Path.home() / ".unity-dev")


def answer(obj=None):
    if obj:
        # ASCII JSON, non-ASCII as escapes: on Windows a hook's stdout is a pipe in the locale's code page, where
        # printing a character such as an arrow fails and the whole answer is lost.
        print(json.dumps(obj))
    sys.exit(0)


def context(text):
    """A PostToolUse answer that adds text to the agent's context, or none."""
    return {"hookSpecificOutput": {"hookEventName": "PostToolUse", "additionalContext": text}} if text else None


# ---------------------------------------------------------------- the task in progress and its skill
def project_of(cwd):
    p = Path(cwd or os.getcwd()).resolve()
    for d in [p, *p.parents]:
        if (d / TRACE).is_dir():
            return d
    return None


def active_trace(cwd):
    """The project's trace folder written most recently, if that was recent: the task in progress."""
    proj = project_of(cwd)
    if not proj:
        return None, None
    best, best_t = None, 0
    for d in (proj / TRACE).iterdir():
        if not d.is_dir():
            continue
        times = [f.stat().st_mtime for f in d.glob("*.jsonl")]
        if times and max(times) > best_t:
            best, best_t = d, max(times)
    if not best or time.time() - best_t > ACTIVE_FOR:
        return proj, None
    return proj, best


def read_lines(f):
    raw = f.read_bytes()
    text = raw.decode("utf-16") if raw[:2] in (b"\xff\xfe", b"\xfe\xff") else raw.decode("utf-8-sig", errors="replace")
    return text.splitlines(), b"\x00" in raw


def skill_roots():
    """Where the skills are: the plugin's own copy first, then the user's skill folders."""
    roots = [Path(plugin_root()) / "skills"] if plugin_root() else []
    return roots + [Path(os.environ.get("CODEX_HOME") or Path.home() / ".codex") / "skills", Path.home() / ".codex" / "skills",
                    Path.home() / ".claude" / "skills"]


def find_skill(skill):
    skill = str(skill or "").split(":")[-1]  # a plugin-qualified name (`<plugin>:<skill>`), as a Codex main thread may write it in the header
    if not skill or not re.fullmatch(r"[\w.-]+", skill):
        return None
    for root in skill_roots():
        if (root / skill / "SKILL.md").exists():
            return root / skill
        if root.name == skill and (root / "SKILL.md").exists():
            return root
    return None


def task_skill_dir(task_dir, agent_type=None):
    """The folder of the skill the task's trace follows (its header names it). A sub-agent spawned before the main thread
    wrote that header (its first agents may start before it) is placed by its own type, `<skill>-<set>`. None when no
    skill of these runs the task."""
    header = {}
    main = task_dir / "main.jsonl"
    if main.exists():
        for line in read_lines(main)[0][:3]:
            try:
                o = json.loads(line)
            except ValueError:
                continue
            if isinstance(o, dict) and "id" not in o:
                header.update(o)
    if header.get("skill"):
        return find_skill(header["skill"])
    kind = str(agent_type or "").split(":")[-1]  # a Claude Code plugin's agent comes as `<plugin>:<name>`
    for root in skill_roots():
        try:
            names = [d.name for d in root.iterdir() if (d / "SKILL.md").exists()]
        except OSError:
            continue
        for name in sorted(names, key=len, reverse=True):
            if kind.startswith(name + "-"):
                return root / name
    return None


# ---------------------------------------------------------------- Codex sessions
def sessions_dir():
    return Path(os.environ.get("CODEX_HOME") or Path.home() / ".codex") / "sessions"


def session_meta(path):
    try:
        with open(path, "rb") as fh:
            o = json.loads(fh.readline().decode("utf-8", errors="replace"))
        return o.get("payload") or {} if o.get("type") == "session_meta" else {}
    except (OSError, ValueError):
        return {}


def find_rollout(agent_id):
    if not agent_id:
        return None
    base = sessions_dir()
    for back in range(2):  # a sub-agent's log is in today's folder, or yesterday's just after midnight
        day = time.localtime(time.time() - back * 86400)
        d = base / time.strftime("%Y", day) / time.strftime("%m", day) / time.strftime("%d", day)
        hit = next(iter(d.glob(f"rollout-*{agent_id}.jsonl")), None) if d.is_dir() else None
        if hit:
            return hit
    return None


def agent_name(meta):
    path = meta.get("agent_path") or ((((meta.get("source") or {}).get("subagent") or {}).get("thread_spawn") or {}).get("agent_path")
                                      if isinstance(meta.get("source"), dict) else None)
    return str(path).rstrip("/").split("/")[-1] if path else None


# ---------------------------------------------------------------- Claude Code sessions
# A sub-agent's log is <session log without .jsonl>/subagents/agent-<id>.jsonl, with agent-<id>.meta.json next to it
# (its type and the description it was spawned with). Its task name is its work folder's, which its brief names.
BRIEF_PATH = re.compile(r"agents[/\\]+([^/\\\s\"'`]+)[/\\]+brief\.md")


def claude_agent_log(ev):
    """The Claude Code sub-agent's own log an event comes from; None for the main thread."""
    if ev.get("agent_transcript_path"):
        return Path(ev["agent_transcript_path"])
    log = Path(ev["transcript_path"]) if ev.get("transcript_path") else None
    if log is not None and log.parent.name == "subagents":
        return log
    if ev.get("agent_id") and log is not None:
        return log.with_suffix("") / "subagents" / f"agent-{ev['agent_id']}.jsonl"
    return None


def claude_agent(ev):
    """The sub-agent as the Codex side reads it from its log's header: its task name, the role type it was spawned
    with, when it started. None for the main thread."""
    log = claude_agent_log(ev)
    if log is None:
        return None
    try:
        meta = json.loads(log.with_suffix(".meta.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        meta = {}
    first, started = "", None
    try:
        with open(log, "rb") as fh:
            for raw in fh:
                o = json.loads(raw.decode("utf-8", errors="replace"))
                if o.get("type") == "user":
                    c = (o.get("message") or {}).get("content")
                    first = c if isinstance(c, str) else " ".join(b.get("text", "") for b in c or [] if isinstance(b, dict))
                    started = o.get("timestamp")
                    break
    except (OSError, ValueError):
        pass
    m = BRIEF_PATH.search(first)
    desc = re.sub(r"[^\w-]+", "_", str(meta.get("description") or "")).strip("_").lower()
    kind = str(meta.get("agentType") or ev.get("agent_type") or "")
    # at its start neither its log nor its meta file exists yet: the name stays unknown, and its brief names its folder
    name = meta.get("name") or (m.group(1) if m else None) or desc
    return {"agent_path": "/root/" + name if name else None, "agent_role": kind.split(":")[-1] or None,
            "timestamp": started, "log": str(log)}


def sub_agent_meta(ev):
    """The header of the log of the sub-agent an event names (agent_id, agent_transcript_path), in the Codex log's
    terms: agent_path, agent_role, timestamp. Empty when its log isn't found."""
    if CLAUDE:
        return claude_agent(ev) or {}
    return session_meta(ev.get("agent_transcript_path") or find_rollout(ev.get("agent_id")) or "")


def own_file(task_dir, name):
    """The agent's trace file: named after its task, often shortened ("runtime" for x_runtime)."""
    files = {f.stem: f for f in task_dir.glob("*.jsonl")}
    if name in files:
        return files[name]
    return next((f for stem, f in files.items() if name.endswith("_" + stem) or name.startswith(stem + "_")), None)


def caller_file(task_dir, ev):
    """The trace file the calling agent writes: main.jsonl for the main thread, its own file for a sub-agent
    (named after its task). None when the caller can't be told."""
    if CLAUDE:  # a sub-agent's calls come with its agent_id; the main thread's without
        if not ev.get("agent_id"):
            return "main.jsonl"
        name = agent_name(claude_agent(ev) or {})
        f = own_file(task_dir, name) if name else None
        return None if not name else f.name if f else f"{name}.jsonl"
    path = ev.get("transcript_path") or find_rollout(ev.get("session_id"))
    meta = session_meta(path) if path else {}
    if not meta:
        return None
    name = agent_name(meta)
    if not name:
        return "main.jsonl"
    f = own_file(task_dir, name)
    return f.name if f else f"{name}.jsonl"


# ---------------------------------------------------------------- an agent's role and its files
# A sub-agent's role, from its task name: the skill's "Skill files by role" table has a row per role. The order
# matters: a profile agent for testing is a profile agent ("profile_testing", "prof_testing"), not a tester; a spec critic
# ("spec_critic") is a spec critic, not an R&D critic.
ROLES = [("profile", r"prof", r"^\|\s*Profile agent"), ("scout", r"scout", r"^\|\s*Scout"),
         ("spec", r"(?:^|[_-])spec(?:[_-]|$)", r"^\|\s*Spec critic"),
         ("audience", r"audienc", r"^\|\s*Audience critic"), ("critic", r"critic", r"^\|\s*Critic"), ("judge", r"judge", r"^\|\s*Critic"),
         ("reviewer", r"review", r"^\|\s*Reviewer"), ("fact", r"fact|verif", r"^\|\s*Fact"),
         ("branch", r"rnd|branch", r"^\|\s*R&D branch"), ("recipe", r"recipe|mechanic", r"^\|\s*Recipe agent"),
         ("tool", r"(?:^|[_-])tools?(?:[_-]|$)", r"^\|\s*Recipe agent"),
         ("implementer", r"implement|integrat|(?:^|[_-])(?:impl|plan)(?:[_-]|$)", r"^\|\s*Implementer"),
         ("tester", r"test|qa|repro|play", r"^\|\s*Tester")]


def typed_role(agent_type, d):
    """The role a sub-agent was spawned with: the skill's agent roles are `<skill>-<set>` (tools/role_digests.py), and
    their developer instructions already hold the set, so nothing of it is read."""
    agent_type = str(agent_type or "").split(":")[-1]  # a Claude Code plugin's agent comes as `<plugin>:<name>`
    if d is None or not agent_type or not agent_type.startswith(d.name + "-"):
        return None
    role = agent_type[len(d.name) + 1:]
    return role if (d / "roles" / f"{role}-1.md").exists() else None


def role_of(name):
    return next((r for r, pat, _ in ROLES if re.search(pat, name or "", re.I)), None)


# A role's own rule set, when the plugin build made one (skills/<skill>/roles/<set>-<n>.md): the rules of its files that
# it needs. A judge reads the critics' set.
ROLE_SET = {"judge": "critic", "tool": "recipe"}
MAIN_ROW = r"^\|\s*Main thread"


def role_set(d, role):
    if d is None or role is None or not (d / "roles").is_dir():
        return []
    name = ROLE_SET.get(role, role)
    parts = [f for f in (d / "roles").glob(f"{name}-*.md") if re.fullmatch(rf"{name}-\d+\.md", f.name)]
    return sorted(parts, key=lambda f: int(f.stem.rsplit("-", 1)[1]))


def role_files(d, role):
    """The files a role reads: its rule set from the build, or else the skill's 'Skill files by role' section (the ones
    every role reads, then its row)."""
    if d is None:
        return []
    parts = role_set(d, role)
    if parts:
        return parts
    lines = read_text_lines(d / "SKILL.md")
    files = [d / "SKILL.md"]
    every = next((l for l in lines if l.startswith("Every role reads")), "")
    files += [d / m for m in re.findall(r"\]\((references/[^)]+\.md)\)", every)]
    row_pat = MAIN_ROW if role == "main" else next((rp for r, _, rp in ROLES if r == role), None)
    if row_pat:
        row = next((l for l in lines if re.match(row_pat, l)), "")
        files += [d / m for m in re.findall(r"\]\((references/[^)]+\.md)\)", row)]
    seen, out = set(), []
    for f in files:
        if f.exists() and f not in seen:
            seen.add(f)
            out.append(f)
    return out


# The artifacts of R&D that a script can check for presence (RND-DIRS, RND-BAR in the unity-dev skill): the direction
# sheet's rows on the R&D stage node, and the bar's rows on each variant's line by the judge.
SHEET_KEYS = ("link", "analogue", "usual", "kept", "taken")
BAR_KEYS = ("effect", "kept", "place", "way", "guards", "footprint", "risk", "shown")
MARKS = ("\u2705", "\u274c", "\u26a0")  # the cell starts with its verdict: holds, fails, not shown


def nodes_of(f):
    """{id: merged node} of one trace file; dict fields replace, as the viewer merges them."""
    nodes = {}
    for line in read_lines(f)[0]:
        try:
            o = json.loads(line)
        except ValueError:
            continue
        if isinstance(o, dict) and "id" in o:
            nodes.setdefault(str(o["id"]), {}).update(o)
    return nodes


def sheet_present(task_dir):
    """The direction sheet exists: the R&D stage node (sg PIPE-RND, or any node) carries its rows as attrs, or the sheet
    file is in the task's work folder."""
    work = task_dir.parents[2] / ".ai-profile" / "work" / task_dir.name
    if (work / "directions.md").exists():
        return True
    main = task_dir / "main.jsonl"
    if not main.exists():
        return False
    for n in nodes_of(main).values():
        a = n.get("attrs")
        if isinstance(a, dict) and all(k in a for k in SHEET_KEYS):
            return True
    return False


def bar_missing(task_dir, name):
    """What the judge's own trace lacks of the bar: '' when some line of its file carries attrs with every row."""
    f = own_file(task_dir, name)
    if not f:
        return "no trace file of yours under " + str(task_dir)
    best = ()
    for line in read_lines(f)[0]:
        try:
            o = json.loads(line)
        except ValueError:
            continue
        a = o.get("attrs") if isinstance(o, dict) else None
        if isinstance(a, dict):
            have = tuple(k for k in BAR_KEYS if k in a)
            if len(have) == len(BAR_KEYS):
                unmarked = [k for k in BAR_KEYS if not str(a.get(k, "")).lstrip().startswith(MARKS)]
                if not unmarked:
                    return ""
                best = have
                return "the rows " + ", ".join(unmarked) + " don't start with their verdict mark (holds / fails / not shown)"
            best = max(best, have, key=len)
    missing = [k for k in BAR_KEYS if k not in best]
    return "no line with attrs holding the rows " + ", ".join(missing)


def skill_files_note(d, role, again=False):
    """The files of this agent's role, by absolute path. Codex cuts a long tool output out of the middle, so each is
    read in full on its own. Again: after a compaction, when nothing of them is in the context any more."""
    files = role_files(d, role)
    if not files:
        return ""
    who = "you are the main thread" if role == "main" else f"you are a {role}" if role else "your brief names your role"
    return (f"Skill: this task runs the {d.name} skill ({who}). Before anything else, read these files "
            f"{'again ' if again else ''}in full, one file per call (a call that reads several at once gets cut), with no "
            f"output cap below the file's size: {', '.join(str(f) for f in files)}. "
            + ("" if again else "Skip the ones already in your context from the main thread's history; ")
            + ("" if role == "main" else ("Your" if again else "your") + " brief may add the task's mode reference. "))


# The rules of the Play Mode file that decide how a tester spends its time; they go into the tester's context as they
# are written in the skill, so they reach it even if it reads the file badly or not at all.
TESTER_CARD = ("PM-DRIVER", "PM-WAIT-ONCE", "PM-OUTPUT", "PM-LOGS", "PM-COMPILE")


def rule_block(lines, tag):
    """A rule as the skill writes it: its bullet and the indented lines under it."""
    i = next((k for k, l in enumerate(lines) if l.lstrip().startswith(f"- [{tag}]") or l.startswith(f"[{tag}]")), None)
    if i is None:
        return []
    j = i + 1
    while j < len(lines) and (lines[j].startswith("  ") or (not lines[j].strip() and j + 1 < len(lines) and lines[j + 1].startswith("  "))):
        j += 1
    return lines[i:j]


def role_card(d, role):
    if role != "tester" or d is None:
        return ""
    lines = read_text_lines(d / "references" / "play-mode.md")
    rules = ["\n".join(rule_block(lines, t)) for t in TESTER_CARD]
    rules = [r for r in rules if r]
    if not rules:
        return ""
    script = d / "scripts" / "wait_for.py"
    rest = "your rule set named above" if role_set(d, role) else "play-mode.md"
    return (f"Your core Play Mode rules, as the skill writes them (the rest is in {rest}):\n" + "\n".join(rules)
            + (f"\nThe wait script: {script}\n" if script.exists() else "\n"))


def unread_role_files(d, role, transcript):
    """Role files whose text never reached the agent: not read by it, and not in the history it was spawned with."""
    text = ""
    try:
        text = Path(transcript).read_text(encoding="utf-8", errors="ignore") if transcript else ""
    except OSError:
        pass
    if not text:
        return []
    missing = []
    for f in role_files(d, role):
        heading = next((l.strip() for l in read_text_lines(f) if l.startswith("# ")), "")
        if heading and heading not in text and json.dumps(heading)[1:-1] not in text:
            missing.append(f)
    return missing


def read_text_lines(f):
    try:
        return f.read_text(encoding="utf-8").splitlines()
    except OSError:
        return []


def block_stop(reason):
    """Sends a sub-agent back before it finishes. In Claude Code only its last message reaches the main thread, so there it
    is asked to end with its report again."""
    if CLAUDE:
        reason += " Then end with your final report again, in full: only your last message reaches the main thread."
    answer({"decision": "block", "reason": reason})


# ---------------------------------------------------------------- the events
def on_subagent_start(ev):
    proj, task_dir = active_trace(ev.get("cwd"))
    d = task_skill_dir(task_dir, ev.get("agent_type")) if task_dir else None
    if d is None:
        answer()
    name = agent_name(sub_agent_meta(ev)) or "<your task name>"
    work = f".ai-profile/work/{task_dir.name}/agents/{name}"
    typed = typed_role(ev.get("agent_type"), d)
    role = typed or role_of(name)
    rules = (f"Skill: this task runs the {d.name} skill and you are its {typed}: your rules are already in your context as your "
             f"{'system prompt' if CLAUDE else 'developer instructions'}, nothing to read for them; a link in them is relative to {d / 'roles'}. "
             if typed else skill_files_note(d, role) + role_card(d, role))
    answer({"hookSpecificOutput": {"hookEventName": "SubagentStart", "additionalContext": (
        rules +
        f"Your brief: save it word for word to {work}/brief.md as your first action, append every later message or task "
        f"from the main thread to the same file, and save your final report to "
        f"{work}/report.md before you return ("
        + ("the briefs and reports otherwise live only in the session logs" if CLAUDE else "messages between agents are encrypted in the logs")
        + "; these files are what the user reads).")}})


def on_subagent_stop(ev):
    if ev.get("stop_hook_active"):
        answer()
    proj, task_dir = active_trace(ev.get("cwd"))
    d = task_skill_dir(task_dir, ev.get("agent_type")) if task_dir else None
    if d is None:
        answer()
    meta = sub_agent_meta(ev)
    name = agent_name(meta)
    if not name:
        answer()
    transcript = meta.get("log") if CLAUDE else ev.get("agent_transcript_path") or find_rollout(ev.get("agent_id"))
    unread = [] if typed_role(meta.get("agent_role"), d) else unread_role_files(d, role_of(name), transcript)
    if unread:
        block_stop((
            "Before you finish: you never read these files of your role, so your work hasn't been checked against them: "
            + ", ".join(str(f) for f in unread) + ". Read each in full, one per call, check your work against them, "
            "fix what they show, then finish (and close your trace node if it is still open)."))
    if role_of(name) == "judge" and (d / "references" / "verdict.md").exists():
        gap = bar_missing(task_dir, name)
        if gap:
            block_stop((
                "RND-BAR: before you finish, the bar isn't in the trace (" + gap + "). For each variant you weighed, append to "
                "your trace file one line with its id and attrs holding the bar's rows (effect, kept, place, way, guards, "
                "footprint, risk, shown, and one per applicable criterion), each a short string that starts with a verdict mark and names what shows it, in the same "
                "line as its pro and con; the table stays in your report too (RND-BAR in references/verdict.md)."))
    answer()


def compacted_since(transcript):
    """Whether the client compacted this agent's context since its last tool call: its log gained a compaction line.
    Only what the log gained since the last look is read; the first look starts at the log's end (a forked agent's
    log begins with a copy of its parent's, compactions included)."""
    if not transcript:
        return False
    log = Path(transcript)
    try:
        size = log.stat().st_size
    except OSError:
        return False
    # (a folder of its own: the graph's hooks keep their own marks of the same logs)
    mark = data_dir() / "compact-skill" / (hashlib.sha1(os.path.normcase(str(log)).encode("utf-8")).hexdigest()[:16] + ".json")
    try:
        seen = int(json.loads(mark.read_text(encoding="utf-8"))["offset"])
    except (OSError, ValueError, KeyError, TypeError):
        seen = None
    found = False
    if seen is not None and size > seen:
        try:
            with open(log, "rb") as fh:
                fh.seek(seen)
                new = fh.read(size - seen)
                found = b'"type":"compacted"' in new or b'"subtype":"compact_boundary"' in new  # Codex, Claude Code
        except OSError:
            pass
    if seen != size:
        try:
            mark.parent.mkdir(parents=True, exist_ok=True)
            mark.write_text(json.dumps({"offset": size}), encoding="utf-8")
        except OSError:
            pass
    return found


def compaction_note(proj, task_dir, d, name):
    """What an agent gets again after its context was compacted: its role's files, and its brief or the task's
    documents."""
    role = role_of(name) if name else "main"
    work = f".ai-profile/work/{task_dir.name}"
    own = [f"{work}/agents/{name}/brief.md"] if name else [f"{work}/{f}" for f in ("task.md", "spec.md")]
    own = [f for f in own if (proj / f).exists()]
    return ("Your context was just compacted: the skill's rules you had read are now only a summary, and a summary loses "
            "their exact words (the trace fields and their values, the gates, the order of steps, etc.). "
            + skill_files_note(d, role, again=True) + role_card(d, role)
            + (f"Read again too: {', '.join(own)}. " if own else ""))


def viewer_task(task_dir):
    """The graph's view of the task (its agents with their status), when the graph's viewer runs: it reads the session
    logs, so it knows best who is at work. None without it."""
    import urllib.request
    from urllib.parse import quote

    def get(path):
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{PORT}{path}", timeout=3) as r:
                return json.loads(r.read().decode("utf-8"))
        except Exception:
            return None
    tasks = get("/api/tasks")
    for t in (tasks or {}).get("tasks", []):
        if t.get("kind") == "trace" and t["key"].endswith(":" + task_dir.name) and t.get("project") == task_dir.parents[2].name:
            return get("/api/task?key=" + quote(t["key"]))
    return None


def busy_agents(task_dir):
    """The sub-agents at work: the graph's view when its viewer runs; without it, the trace's: an agent whose own file
    still has a node open."""
    task = viewer_task(task_dir)
    if task is not None:
        return sorted({str(a.get("agent", "")).split("/")[-1] for a in task.get("agents", [])
                       if a.get("status") == "running" and str(a.get("agent", "")).rstrip("/") not in ("", "/root")})
    busy = set()
    for f in task_dir.glob("*.jsonl"):
        if f.name == "main.jsonl":
            continue
        st = {}
        for line in read_lines(f)[0]:
            try:
                o = json.loads(line)
            except ValueError:
                continue
            if isinstance(o, dict) and "id" in o and "st" in o:
                st[str(o["id"])] = o["st"]
        if "run" in st.values():
            busy.add(f.stem)
    return sorted(busy)


# What belongs to a role's agents, not to the main thread, while they work (MAIN-WAITS in agents.md): reads of code and
# assets, searches over the project, the Editor through the bridge. Writes (the spec, the trace, a brief) are its own.
INVEST = re.compile(r"Assets[/\\]|\.cs\b|\.prefab\b|\.asset\b|mcp__unity|read_mcp_resource", re.I)  # a search over the task's own log isn't this
PATHQ = re.compile(r"""['"]([A-Za-z]:[/\\][^'"]*)['"]""")  # a quoted absolute path
WRITES = re.compile(r"Add-Content|Set-Content|Out-File|apply_patch|New-Item|write_text", re.I)


def main_waits_note(task_dir, ev, mine):
    """The main thread just did a role's work, or waited in a short slice, while sub-agents are at work: told at once,
    as the rule says it (a note, not a block: the call has already run)."""
    if mine != "main.jsonl":
        return ""
    name = str(ev.get("tool_name") or "")
    arg = ev.get("tool_input")
    text = arg if isinstance(arg, str) else json.dumps(arg, ensure_ascii=False) if arg is not None else ""
    # a wait under five minutes is a slice: a run woke every minute, wrote a status line each time and compacted three times
    short_wait = name.endswith("wait_agent") and isinstance(arg, dict) and int(arg.get("timeout_ms") or 0) < 300000
    # the task's own materials outside the project (the user's logs, screenshots, a case folder, etc.) are the main thread's
    # to read for the spec: a quoted absolute path outside the project doesn't count as investigation
    proj = str(task_dir.parent.parent.parent).replace("\\", "/").lower()
    inside = PATHQ.sub(lambda m: m.group(0) if m.group(1).replace("\\", "/").lower().startswith(proj) else "", text)
    invest = (not name.endswith(("wait_agent", "spawn_agent", "send_message", "followup_task")) and name not in ("Agent", "Task", "SendMessage")
              and bool(INVEST.search(inside)) and not WRITES.search(text))
    if not (short_wait or invest):
        return ""
    busy = busy_agents(task_dir)
    if not busy:
        return ""
    who = ", ".join(busy)
    if invest:
        return (f"MAIN-WAITS: {who} are at work, and what you just did (code, assets or the Editor) is their role's work: their reports "
                "decide, not your own reading, and a finding of yours sent into their briefs mid-way has already cost a run a second round. "
                + ("End the turn and let their reports wake you" if CLAUDE else "Wait for them in one call")
                + "; meanwhile only the next briefs, the spec, the direction sheet, the trace and the draft of the report.")
    return (f"WAIT-RESULT: {who} are at work; wait for them in one call with the client's longest timeout, not in slices: "
            "nothing of yours is due until one of them returns, and every slice tempts a check of your own.")


SPAWN_NAME = re.compile(r"spawn_agent$|^(Agent|Task)$")
# handing work to an agent: a new one, or a follow-up task to one already there (Codex), or a message to a teammate
WORK_NAME = re.compile(r"spawn_agent$|followup_task$|^(Agent|Task|SendMessage)$")


TURN_EVENT = re.compile(r'"type":\s*"(task_started|task_complete)"')


def rollout_of(name, caller_transcript):
    """The Codex rollout of the sub-agent with this task name in the caller's team: a child of the caller, or a sibling
    (the same parent thread); the newest when several were spawned under that name."""
    meta = session_meta(caller_transcript) if caller_transcript else {}
    caller_id = str(meta.get("id") or "")
    parent = str(meta.get("parent_thread_id") or "")
    base = sessions_dir()
    hits = []
    for back in range(2):
        day = time.localtime(time.time() - back * 86400)
        d = base / time.strftime("%Y", day) / time.strftime("%m", day) / time.strftime("%d", day)
        if not d.is_dir():
            continue
        for f in d.glob("rollout-*.jsonl"):
            m = session_meta(f)
            if agent_name(m) != name:
                continue
            p = str(m.get("parent_thread_id") or "")
            if (p and p in (caller_id, parent)) or not (caller_id or parent):
                hits.append(f)
    return max(hits, key=lambda f: f.stat().st_mtime) if hits else None


def turn_running(name, caller_transcript):
    """Whether that agent has a turn running, from the tail of its own rollout: the last task_started / task_complete
    event. None when its rollout isn't found (then the trace decides)."""
    f = rollout_of(name, caller_transcript)
    if not f:
        return None
    try:
        with open(f, "rb") as fh:
            fh.seek(0, 2)
            size = fh.tell()
            fh.seek(max(0, size - 262144))
            tail = fh.read().decode("utf-8", errors="replace")
    except OSError:
        return None
    events = TURN_EVENT.findall(tail)
    if not events:
        return None
    return events[-1] == "task_started"


def followup_note(task_dir, ev, transcript):
    """A message to an agent that has no turn running (its last report is in): a message doesn't start a turn, so nothing
    runs until a follow-up task; said at once to whoever sent it (a run lost 24 minutes this way). The agent's own rollout
    says whether a turn runs; without it, the trace (an agent with no open node)."""
    name = str(ev.get("tool_name") or "")
    if not (name.endswith("send_message") or name == "SendMessage"):
        return ""
    arg = ev.get("tool_input") if isinstance(ev.get("tool_input"), dict) else {}
    target = str(arg.get("target") or arg.get("to") or arg.get("recipient") or "").rstrip("/").split("/")[-1]
    if not target or target in ("root", "main"):
        return ""
    running = None if CLAUDE else turn_running(target, transcript)
    if running is None:
        running = target in busy_agents(task_dir)
    if running:
        return ""
    return (f"FOLLOWUP: {target} has no turn running (its last turn ended; its report is in). A message doesn't start a turn, so "
            "nothing of it runs until it gets the work as a follow-up task (followup_task in Codex); send that now, and wait "
            "for its return ([WAIT-RESULT]).")


def round_note(task_dir, d, ev, mine):
    """The main thread hands out new work (a spawn or a follow-up task) outside the correction path (an implementer, the
    reviewer, the tester) after the round's acceptance failed and before the user said a word: a fix that needs another form,
    another reading or a new R&D ends the round with the report ([AUTONOMY]); told at once (a note, not a block). The trace decides: the
    last QA round that says fail (a `"sg":"PIPE-QA"` node, or a round written as a child of one: `qa1`, `qa2` under `qa`),
    and whether any word of the user came after it (a node by the user, an answer to a question card, a `you-*` node). Only a
    QA stage node that closes ok clears it: a child closing ok may be the tester's own node."""
    if mine != "main.jsonl" or not WORK_NAME.search(str(ev.get("tool_name") or "")):
        return ""
    arg = ev.get("tool_input") if isinstance(ev.get("tool_input"), dict) else {}
    kind = str(arg.get("agent_type") or arg.get("subagent_type") or "").split(":")[-1]
    label = " ".join(str(arg.get(k) or "") for k in ("name", "agent_name", "task_name", "label", "description", "target", "to"))
    # the correction path within the variant (an implementer or integrator, the reviewer, the tester's re-run) goes on unnoted
    fix_path = ("tester", "implementer", "reviewer", "recipe", "tool")
    if kind.split("-")[-1] in fix_path or (not kind.startswith(d.name + "-") and role_of(label) in fix_path):
        return ""
    fail = user = None; title = {}; qa_stage = set()
    for n, line in enumerate(read_lines(task_dir / "main.jsonl")[0]):
        try:
            o = json.loads(line)
        except ValueError:
            continue
        if not isinstance(o, dict) or "id" not in o:
            continue
        i = str(o["id"])
        if o.get("t"):
            title[i] = o["t"]
        if o.get("sg") == "PIPE-QA":
            qa_stage.add(i)
        if str(o.get("p") or "") in qa_stage and o.get("st") == "fail":
            fail = (n, i, title.get(i, i), o.get("s") or "")
        if o.get("sg") == "PIPE-QA" or i in qa_stage:
            if o.get("st") == "fail":
                fail = (n, i, title.get(i, i), o.get("s") or "")
            elif o.get("st") in ("ok", "skip", "drop"):
                fail = None  # a later round passed, or the stage was dropped: no failed round stands open
        if o.get("by") == "user" or "ans" in o or i.startswith("you-"):
            user = n
    if not fail or (user is not None and user > fail[0]):
        return ""
    return (f"ROUND: the acceptance \"{fail[2]}\" failed ({fail[3] or 'see its node'}) and the user hasn't said a word since. A correction "
            "within the chosen variant goes on; a fix that needs another form, another reading of the task, a new R&D or a search for a cause ends the round "
            "with the report ([AUTONOMY]): what failed, the evidence, the options for the next round. The next round is the user's pick.")


def sheet_note(task_dir, d, ev, mine):
    """The main thread just spawned an R&D branch while the R&D stage has no direction sheet: told at once (a note, not a
    block: the branch already runs)."""
    if mine != "main.jsonl" or not SPAWN_NAME.search(str(ev.get("tool_name") or "")):
        return ""
    if not (d / "references" / "profiles.md").exists() or "RND-DIRS" not in (d / "references" / "profiles.md").read_text(encoding="utf-8", errors="ignore"):
        return ""
    arg = ev.get("tool_input") if isinstance(ev.get("tool_input"), dict) else {}
    kind = str(arg.get("agent_type") or arg.get("subagent_type") or "").split(":")[-1]
    label = " ".join(str(arg.get(k) or "") for k in ("name", "agent_name", "task_name", "label", "description"))
    is_branch = kind.endswith("-branch") or (not kind.startswith(d.name + "-") and role_of(label) == "branch")
    if not is_branch or sheet_present(task_dir):
        return ""
    return ("RND-DIRS: an R&D branch is running and the R&D stage has no direction sheet: no attrs (link, analogue, usual, kept, "
            f"taken) on the stage node in {task_dir / 'main.jsonl'} and no .ai-profile/work/{task_dir.name}/directions.md. "
            "Write the sheet now (the cause's link, how the project already handles the same situation there, the field's usual "
            "ways by level, the kept items, the directions taken and not taken), put its rows on the stage node as attrs with "
            "RND-DIRS in r, and send each running branch its row; a direction the sheet shows missing gets its branch "
            "(RND-DIRS in references/profiles.md).")


def on_post_tool_use(ev):
    proj, task_dir = active_trace(ev.get("cwd"))
    d = task_skill_dir(task_dir) if task_dir else None
    if d is None:
        answer()
    mine = caller_file(task_dir, ev)
    caller = (claude_agent(ev) or {}) if CLAUDE else None
    transcript = (caller.get("log") or ev.get("transcript_path")) if CLAUDE else ev.get("transcript_path") or find_rollout(ev.get("session_id"))
    notes = []
    try:
        notes.append(main_waits_note(task_dir, ev, mine))
    except Exception as e:  # the guard must not stop the agent's work
        print(f"unity-dev hook: {e}", file=sys.stderr)
    try:
        notes.append(round_note(task_dir, d, ev, mine))
    except Exception as e:  # the reminder must not stop the agent's work
        print(f"unity-dev hook: {e}", file=sys.stderr)
    try:
        notes.append(sheet_note(task_dir, d, ev, mine))
    except Exception as e:  # the reminder must not stop the agent's work
        print(f"unity-dev hook: {e}", file=sys.stderr)
    try:
        notes.append(followup_note(task_dir, ev, transcript))
    except Exception as e:  # the reminder must not stop the agent's work
        print(f"unity-dev hook: {e}", file=sys.stderr)
    if compacted_since(transcript):
        try:
            notes.append(compaction_note(proj, task_dir, d, agent_name(caller if CLAUDE else session_meta(transcript))))
        except Exception as e:  # the reminder must not stop the agent's work
            print(f"unity-dev hook: {e}", file=sys.stderr)
    answer(context("\n\n".join(x for x in notes if x)))


SKILL_FILE = re.compile(r"(SKILL\.md|references[/\\][A-Za-z0-9_\-]+\.md|roles[/\\][a-z]+-\d+\.md)")
CUT = re.compile(r"truncated output \(original token count: (\d+)\)")
PARTIAL = re.compile(r"PARTIAL view\b.*?\((\d+) tokens, cap")  # Claude Code's Read above its limit: the first page only


def truncated_skill_read(ev):
    """Codex cuts a tool output above its token limit out of the middle, silently for the agent; Claude Code's Read returns
    only the first page of a file above its limit. A read of a skill file that came back cut is said at once: without this
    the agent believes it read the rules it never saw."""
    out = json.dumps(ev.get("tool_response"), ensure_ascii=False) if ev.get("tool_response") is not None else ""
    m, first_page = CUT.search(out), None
    if not m:
        m = first_page = PARTIAL.search(out)
    if not m:
        return ""
    arg = json.dumps(ev.get("tool_input"), ensure_ascii=False)
    files = sorted(set(SKILL_FILE.findall(arg)))
    if not files:
        return ""
    if first_page:
        return (f"Skill read cut: {', '.join(files)} is {m.group(1)} tokens and the read returned only its first page. Read the "
                "rest by line ranges (offset and limit) until the end of the file, one call per range. Don't go on with the "
                "rules you have: the part you didn't read is the part you don't know you're missing.")
    return (f"Skill read cut: the output of this call was {m.group(1)} tokens and Codex cut its middle out, so part of "
            f"{', '.join(files)} never reached you. Read the file again with no output cap of your own (no max_output_tokens "
            "below the file's size), one file per call; if a whole file is still above the limit, read it in two halves by line "
            "ranges. Don't go on with the rules you have: the cut part is the part you don't know you're missing.")


def main():
    raw = sys.stdin.buffer.read().decode("utf-8", errors="replace")
    # a copy of the main agent the graph's viewer started to answer the user's question (codex exec fork) has nothing
    # to keep: no reminder may turn it from its question
    if os.environ.get("AGENT_TRACE_QUESTION"):
        answer()
    try:
        ev = json.loads(raw)
    except ValueError:
        answer()
    name = ev.get("hook_event_name")
    try:
        if name == "SubagentStart":
            on_subagent_start(ev)
        elif name == "SubagentStop":
            on_subagent_stop(ev)
        elif name == "PostToolUse":
            cut = truncated_skill_read(ev)
            if cut:
                answer(context(cut))
            on_post_tool_use(ev)
    except SystemExit:
        raise
    except Exception as e:  # a broken check must never stop the agent's work
        print(f"unity-dev hook: {e}", file=sys.stderr)
    answer()


if __name__ == "__main__":
    main()
