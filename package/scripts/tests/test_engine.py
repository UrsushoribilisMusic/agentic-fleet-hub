"""Engine unit tests. Run: python3 -m unittest discover -s scripts/tests"""
import importlib
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))


def fresh(module, **env):
    """Reload flotilla_config (and the module) under a patched environment."""
    old = {k: os.environ.get(k) for k in env}
    os.environ.update({k: v for k, v in env.items()})
    try:
        import flotilla_config
        importlib.reload(flotilla_config)
        mod = importlib.import_module(module)
        return importlib.reload(mod)
    finally:
        for k, v in old.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v


class ConfigTests(unittest.TestCase):
    def test_defaults_follow_the_workspace(self):
        with tempfile.TemporaryDirectory() as ws:
            cfg = fresh("flotilla_config", FLOTILLA_WORKSPACE=ws)
            self.assertEqual(str(cfg.WORKSPACE_DIR), str(Path(ws).resolve()))
            self.assertEqual(cfg.MISSION_CONTROL_PATH.name, "MISSION_CONTROL.md")
            self.assertIn("clau", cfg.load_agent_commands())

    def test_agent_commands_override_and_disable(self):
        with tempfile.TemporaryDirectory() as ws:
            conf = Path(ws, "AGENTS", "CONFIG")
            conf.mkdir(parents=True)
            (conf / "agent_commands.json").write_text(json.dumps({
                "_comment": "ignored",
                "clau": ["mycli", "-C", "{workspace}", "{prompt}"],
                "gem": None,
            }))
            cfg = fresh("flotilla_config", FLOTILLA_WORKSPACE=ws)
            cmds = cfg.load_agent_commands()
            self.assertNotIn("gem", cmds)
            self.assertNotIn("_comment", cmds)
            self.assertEqual(cmds["clau"][0], "mycli")
            self.assertEqual(cmds["clau"][2], str(Path(ws).resolve()))
            self.assertEqual(cmds["clau"][3], cfg.HEARTBEAT_PROMPT)

    def test_github_disabled_by_default(self):
        cfg = fresh("flotilla_config", FLOTILLA_GITHUB_REPO="")
        self.assertEqual(cfg.GITHUB_REPO, "")
        self.assertEqual(cfg.github_repo_url("/issues/1"), "")


class GithubPrivacyTests(unittest.TestCase):
    def setUp(self):
        self.gs = fresh("github_sync", FLOTILLA_GITHUB_REPO="example-org/private-workspace")
        self.created = []
        self.gs.create_github_issue = lambda title, body: (self.created.append((title, body)), 1)[1]
        self.gs.set_issue_labels = lambda *a, **k: None
        self.gs.find_existing_issue_by_title = lambda t: None
        self.gs.pb_patch = lambda *a, **k: {}
        self.gs.log = lambda *a, **k: None

    def run_sync(self, task):
        base = {"id": "t1", "title": "T", "description": "secret plan", "status": "todo", "gh_issue_id": 0}
        base.update(task)
        self.gs.sync_outbound([base], {})
        return self.created

    def test_normal_task_is_mirrored(self):
        self.assertEqual(len(self.run_sync({})), 1)

    def test_private_council_and_telegram_tasks_are_skipped(self):
        for extra in ({"private": True}, {"source": "council"}, {"source": "telegram"}, {"is_github_sync": False}):
            self.created.clear()
            self.assertEqual(self.run_sync(extra), [], extra)

    def test_goal_tasks_get_placeholder_body(self):
        created = self.run_sync({"goal_id": "g1"})
        self.assertEqual(len(created), 1)
        self.assertNotIn("secret plan", created[0][1])

    def test_confidential_marker_hides_body(self):
        created = self.run_sync({"description": "CONFIDENTIAL partner list"})
        self.assertNotIn("partner list", created[0][1])


if __name__ == "__main__":
    unittest.main()
