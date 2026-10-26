"""Regression checks without model invocations or live PocketBase writes."""
import importlib.util
import ast
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import os
import time
from types import SimpleNamespace
import io
import unittest
from datetime import datetime, timezone
from unittest.mock import patch
from unittest.mock import Mock

FLEET = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(FLEET))
from scheduler_policy import availability, quota_retry_seconds
import heartbeat_check

spec = importlib.util.spec_from_file_location('pb_flush', FLEET/'codi/pb_flush.py')
pb = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pb)


class AvailabilityTests(unittest.TestCase):
    def test_qwen_and_legacy_gemma_share_pause(self):
        meta = {'team': [{'heartbeatKey': 'gemma', 'available': False}]}
        for name in ['qwen', 'gemma']:
            self.assertFalse(availability(name, meta, {})[0])

    def test_misty_subscription_pause(self):
        self.assertFalse(availability('misty', {'team': [{'heartbeatKey': 'misty', 'available': False}]}, {})[0])

    def test_future_quota_blocks_both_entrypoints(self):
        now = datetime(2026, 10, 26, tzinfo=timezone.utc)
        failures = {'gem': {'blocked_until': '2026-10-31T04:00:00Z', 'reason': 'quota'}}
        self.assertFalse(availability('gem', {'team': []}, failures, now)[0])
        self.assertFalse(availability('gemini', {'team': []}, failures, now)[0])
        self.assertTrue(availability('codi', {'team': []}, failures, now)[0])

    def test_expired_quota_allows_retry(self):
        self.assertTrue(availability('gem', {'team': []}, {'gem': {'blocked_until': '2020-01-01T00:00:00Z'}})[0])

    def test_provider_reset_longer_than_twelve_hours(self):
        self.assertEqual(quota_retry_seconds('Individual quota reached. Resets in 118h59m29s.'),
                         118*3600 + 59*60 + 29 + 120)

    def test_provider_reset_shorter_than_twelve_hours(self):
        self.assertEqual(quota_retry_seconds('Resets in 59m58s.'), 3598+120)
        self.assertEqual(quota_retry_seconds('No reset hint', 42), 42)

    def test_dispatcher_gem_task_bypasses_autonomous_heartbeat_gate(self):
        tree = ast.parse((FLEET/'dispatcher.py').read_text())
        function = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'run_agent')
        popen = Mock(return_value=SimpleNamespace(pid=1234))
        active = {}
        scope = dict(AGENT_COMMANDS={'gem': ['agy', 'Run heartbeat protocol']},
                     _active_agents=active, is_agent_available=lambda *a: (True, ''),
                     log=lambda *a: None, update_task_status=Mock(),
                     tempfile=tempfile, os=os, time=time,
                     subprocess=SimpleNamespace(Popen=popen, STDOUT=-2))
        exec(compile(ast.Module(body=[function], type_ignores=[]), '<dispatcher>', 'exec'), scope)
        scope['run_agent']('gem', {'id': 'task', 'title': 'Actual work', 'status': 'todo'})
        prompt = popen.call_args[0][0][-1]
        self.assertIn('Do not run heartbeat_check.py', prompt)
        self.assertIn('YOUR TASK: Actual work', prompt)
        Path(active['gem'][2]).unlink()

    def test_peer_review_query_excludes_own_work(self):
        with patch.object(heartbeat_check.urllib.request, 'urlopen', return_value=io.BytesIO(b'{"items": []}')) as call:
            self.assertEqual(heartbeat_check._pb_fetch_actionable(['codi', 'codex']), [])
            url = heartbeat_check.urllib.parse.unquote(call.call_args[0][0])
            self.assertIn("status='peer_review'&&(assigned_agent!='codi'&&assigned_agent!='codex')", url)

    def test_empty_authoritative_queue_ignores_stale_mission_control(self):
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp)
            (repo/'MISSION_CONTROL.md').write_text('### OPEN\nCodi still mentioned here\n')
            with patch.object(sys, 'argv', ['heartbeat_check.py', '--agent', 'codi', '--repo', str(repo)]), \
                 patch.object(heartbeat_check, '_load_meta', return_value={'team': []}), \
                 patch.object(heartbeat_check, '_active_project_mcs', return_value=[]), \
                 patch.object(heartbeat_check, '_pb_fetch_actionable', return_value=[]), \
                 patch.object(heartbeat_check, 'availability', return_value=(True, '')):
                with self.assertRaises(SystemExit) as stopped:
                    heartbeat_check.main()
                self.assertEqual(stopped.exception.code, 1)


class ProgressTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.repo = Path(cls.temp.name)/'repo'
        cls.repo.mkdir()
        def git(*args):
            return subprocess.check_output(['git', '-C', str(cls.repo), *args], stderr=subprocess.DEVNULL).decode().strip()
        git('init', '-b', 'master')
        git('config', 'user.name', 'Test')
        git('config', 'user.email', 'test@example.invalid')
        (cls.repo/'work.txt').write_text('real implementation')
        git('add', 'work.txt')
        git('-c', 'core.hooksPath=/dev/null', 'commit', '-m', 'fix(TSC-4): implementation')
        cls.commit = git('rev-parse', 'HEAD')
        cls.repos = [cls.repo]

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def setUp(self):
        self.task = dict(id='exampletask', title='TSC-4: verify data', status='peer_review',
                         assigned_agent='gem', updated='2026-10-24 10:00:00Z')
        self.op = dict(method='PATCH', collection='tasks', id='exampletask', data={'status': 'approved'})
        self.comment = dict(task_id='exampletask', agent='codi', type='approval',
                            created='2026-10-26 08:00:00Z', content=f'Reviewed {self.commit}. Verified.')

    def valid(self, comments=None):
        return pb.validate_progress(self.op, self.task, self.repos,
                                    [self.comment] if comments is None else comments)[0]

    def test_real_tsc_review_has_no_pc_prefix_or_one_hour_requirement(self):
        self.assertTrue(self.valid())

    def test_self_approval_rejected(self):
        self.task['assigned_agent'] = 'codi'
        self.assertFalse(self.valid())

    def test_missing_approval_rejected(self):
        self.assertFalse(self.valid([]))

    def test_fabricated_commit_rejected(self):
        self.comment['content'] = 'Reviewed deadbeef.'
        self.assertFalse(self.valid())

    def test_stale_approval_rejected_after_task_changed(self):
        self.task['updated'] = '2026-10-26 09:00:00Z'
        self.assertFalse(self.valid())

    def test_wrong_task_or_author_rejected(self):
        self.comment['task_id'] = 'another'
        self.assertFalse(self.valid())
        self.comment['task_id'] = 'exampletask'
        self.comment['agent'] = 'gem'
        self.assertFalse(self.valid())

    def test_task_progress_requires_real_linked_commit(self):
        self.op['data']['status'] = 'peer_review'
        self.task['status'] = 'in_progress'
        self.assertTrue(self.valid([]))
        self.task['title'] = 'TSC-40: unrelated'
        self.assertFalse(self.valid([]))

    def test_dry_run_does_not_mutate_queue_or_api(self):
        self.exercise_flush(dry_run=True)

    def test_success_removes_pending_patch(self):
        self.exercise_flush()

    def test_network_failure_never_discards_queued_write(self):
        self.exercise_flush(fail=True)

    def exercise_flush(self, dry_run=False, fail=False):
        with tempfile.TemporaryDirectory() as temp:
            pending = Path(temp)/'pending.json'
            pending.write_text(json.dumps([self.op]))
            before = pending.read_bytes()
            writes = []
            def api(collection, record_id='', data=None, method='GET', params=None):
                if method != 'GET':
                    if fail:
                        raise OSError('offline')
                    writes.append((collection, record_id, data))
                    return {'id': record_id}
                return self.task if collection == 'tasks' else {'items': [self.comment]}
            result = pb.flush(pending, api=api, repos=self.repos, dry_run=dry_run)
            self.assertEqual(result, 1 if fail else 0)
            if dry_run:
                self.assertEqual(pending.read_bytes(), before)
                self.assertFalse(writes)
            elif fail:
                self.assertEqual(json.loads(pending.read_text())[0]['data'], self.op['data'])
            else:
                self.assertFalse(pending.exists())
                self.assertEqual(len(writes), 1)


if __name__ == '__main__':
    unittest.main()
