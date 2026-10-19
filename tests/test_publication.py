"""Local packaging and isolation checks. Fixtures are retained under .ai-profile/work/."""
import argparse
import http.client
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import threading
import time
import unittest
import uuid
from unittest.mock import patch
from urllib.parse import urlencode

REPO = Path(__file__).resolve().parents[1]
ARTIFACTS = Path(os.environ.get("PUBLICATION_TEST_ARTIFACTS", REPO / ".ai-profile/work/publication-tests")) / uuid.uuid4().hex
ARTIFACTS.mkdir(parents=True)


def run_build(host):
    root = ARTIFACTS / host
    run = subprocess.run([sys.executable, str(REPO / "tools/build_plugin.py"), "--host", host,
                          "--dist-root", str(root), "--version", "1.0.0"], cwd=REPO,
                         capture_output=True, text=True, encoding="utf-8")
    (ARTIFACTS / f"{host}-build.log").write_text(run.stdout + run.stderr, encoding="utf-8")
    if run.returncode:
        raise AssertionError(run.stdout + run.stderr)
    return root


def check_mcp(test, package, host):
    entry = json.loads((package / ".mcp.json").read_text(encoding="utf-8"))["mcpServers"]["flow-ai-graph"]
    test.assertNotIn("/", entry["command"])
    test.assertNotIn("\\", entry["command"])
    argv = [entry["command"]] + [a.replace("${CLAUDE_PLUGIN_ROOT}", str(package)) for a in entry["args"]]
    project = ARTIFACTS / (host + "-project")
    project.mkdir(exist_ok=True)
    argv += ["--root", str(project / "trace")]
    methods = [("initialize", {"protocolVersion": "2025-06-18"}), ("tools/list", {}),
               ("tools/call", {"name": "graph_start", "arguments": {"title": "Synthetic package test", "project": str(project)}})]
    raw = "".join(json.dumps({"jsonrpc": "2.0", "id": i, "method": m, "params": p}) + "\n" for i, (m, p) in enumerate(methods, 1))
    result = subprocess.run(argv, cwd=package, input=raw, capture_output=True, text=True, encoding="utf-8", timeout=30,
                            env={**os.environ, "AI_GRAPH_VIEWER": "0", "PYTHONUTF8": "1"})
    test.assertEqual(result.returncode, 0, result.stderr)
    messages = [json.loads(line) for line in result.stdout.splitlines()]
    test.assertEqual([m["id"] for m in messages], [1, 2, 3])
    test.assertEqual(messages[0]["result"]["serverInfo"]["name"], "flow-ai-graph")
    test.assertIn("graph_check", {t["name"] for t in messages[1]["result"]["tools"]})
    test.assertFalse(messages[2]["result"].get("isError"), messages[2])
    (ARTIFACTS / f"{host}-mcp.json").write_text(json.dumps(messages, indent=2), encoding="utf-8")

PRODUCT = json.loads((REPO / "product.json").read_text(encoding="utf-8"))
NAME = PRODUCT["name"]
sys.path.insert(0, str(REPO / "tools"))
import validate_skill


class SkillBuildTests(unittest.TestCase):
    def test_both_hosts_and_dependency(self):
        for host in ("codex", "claude"):
            with self.subTest(host=host):
                package = run_build(host) / NAME
                self.assertEqual({p.name for p in (package / "skills").iterdir()}, {NAME})
                self.assertEqual(validate_skill.validate(package / "skills" / NAME), [])
                self.assertTrue((package / "LICENSE").is_file())
                source = json.loads((package / "SOURCES.json").read_text(encoding="utf-8"))
                if PRODUCT.get("graph"):
                    self.assertTrue((package / "scripts/skills_part.py").is_file())
                    self.assertTrue((package / "scripts/trace_scope.py").is_file())
                    pin = subprocess.check_output(["git", "-C", str(REPO), "ls-files", "--stage", "--", "vendor/flow-ai-graph"]).decode().split()[1]
                    self.assertEqual(source["dependencies"]["flow-ai-graph"]["git"], pin)
                    self.assertTrue(list((package / "agents").glob("*.toml" if host == "codex" else "*.md")))
                    check_mcp(self, package, host)
                    if host == "claude":
                        built = (package / "skills/unity-dev/SKILL.md").read_text(encoding="utf-8")
                        self.assertNotIn("ai-skills:", built)
                    # Both parts receive a harmless event; no model, session or viewer is started.
                    event = json.dumps({"hook_event_name": "SubagentStart", "cwd": str(ARTIFACTS), "session_id": "synthetic"})
                    probe = subprocess.run([sys.executable, str(package / "scripts/skill_hooks.py")], input=event,
                        capture_output=True, text=True, env={**os.environ, "PLUGIN_ROOT": str(package), "PLUGIN_DATA": str(ARTIFACTS / "hook-data"), "AI_GRAPH_VIEWER": "0"})
                    self.assertEqual(probe.returncode, 0, probe.stderr)
                    self.assertNotIn("bundle hook", probe.stderr)
                else:
                    self.assertFalse((package / "mcp_graph.py").exists())
                    self.assertFalse((package / ".mcp.json").exists())
                    self.assertNotIn("dependencies", source)
                    self.assertFalse((package / "agents").exists())

    def test_invalid_metadata_fails(self):
        path = ARTIFACTS / "invalid"
        path.mkdir()
        (path / "SKILL.md").write_text("---\nname: wrong\ndescription: ''\n---\n", encoding="utf-8")
        self.assertTrue(validate_skill.validate(path))

    def test_missing_validator_dependency_fails(self):
        run = subprocess.run([sys.executable, "-S", "-c", "import sys; sys.path.insert(0, 'tools'); import validate_skill"],
                             cwd=REPO, capture_output=True, text=True)
        self.assertNotEqual(run.returncode, 0)
        self.assertIn("requirements-dev.txt", run.stderr)

    def dependency_fixture(self, name, initialize=False):
        fixture = ARTIFACTS / name
        subprocess.run(["git", "clone", "--quiet", "--no-local", str(REPO), str(fixture)], check=True)
        if initialize:
            subprocess.run(["git", "-c", "protocol.file.allow=always",
                            "-c", f"submodule.vendor/flow-ai-graph.url={REPO / 'vendor/flow-ai-graph'}",
                            "-C", str(fixture), "submodule", "update", "--init"], check=True, capture_output=True)
        return fixture

    def dependency_build_fails(self, fixture, expected):
        result = subprocess.run([sys.executable, str(fixture / "tools/build_plugin.py")], cwd=fixture,
                                capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn(expected, result.stderr)

    def test_missing_graph_dependency_is_rejected(self):
        self.dependency_build_fails(self.dependency_fixture("missing-graph"), "submodule is missing")

    def test_dirty_graph_dependency_is_rejected(self):
        fixture = self.dependency_fixture("dirty-graph", initialize=True)
        with open(fixture / "vendor/flow-ai-graph/README.md", "a", encoding="utf-8") as stream:
            stream.write("\nSynthetic dirty-dependency test.\n")
        self.dependency_build_fails(fixture, "submodule is dirty")

    def test_wrong_graph_commit_is_rejected(self):
        fixture = self.dependency_fixture("wrong-graph", initialize=True)
        graph = fixture / "vendor/flow-ai-graph"
        for key, value in (("user.name", "Synthetic Check"), ("user.email", "check@example.invalid")):
            subprocess.run(["git", "-C", str(graph), "config", key, value], check=True)
        subprocess.run(["git", "-C", str(graph), "commit", "--quiet", "--allow-empty", "-m", "Synthetic wrong dependency revision"], check=True)
        self.dependency_build_fails(fixture, "differs from the pinned gitlink")
