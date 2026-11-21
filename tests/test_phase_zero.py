import json
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock

from ai_factory.phase_zero import CodingAgent, QAAgent, run, EXAMPLE
from ai_factory.codex_artifact import CodexArtifact


class FactoryTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(self.enterContext(tempfile.TemporaryDirectory()))
        self.task = json.loads(EXAMPLE.read_text())

    def execute(self, **kwargs):
        return run(self.task, self.root, **kwargs)

    def test_pipeline_keeps_artifact_and_role_evidence(self):
        directory, status = self.execute()
        self.assertEqual(status, 'awaiting_human_review')
        events = [json.loads(line) for line in (directory/'events.jsonl').read_text().splitlines()]
        self.assertEqual([e['role'] for e in events], ['orchestrator', 'coding', 'qa', 'orchestrator'])
        self.assertEqual(events[2]['passed'], 3)
        self.assertIn('COUNT', (directory/'candidate-1.sql').read_text())
        self.assertNotEqual(directory, self.execute()[0])

    def test_qa_rejects_wrong_results_and_forbidden_statements(self):
        for sql in ['SELECT status FROM builds', 'DELETE FROM builds',
                    "ATTACH DATABASE '/tmp/out' AS data", 'SELECT randomblob(1000000)']:
            with self.subTest(sql=sql), self.assertRaises((ValueError, sqlite3.Error)):
                QAAgent().check(sql)

    def test_retries_retain_failed_candidate(self):
        coder = Mock(spec=CodingAgent)
        coder.mode = 'simulation'
        coder.write.side_effect = ['SELECT status FROM builds', CodingAgent().write()]
        directory, status = self.execute(coder=coder, attempts=2)
        self.assertEqual(status, 'awaiting_human_review')
        self.assertTrue((directory/'candidate-2.sql').exists())
        self.assertIn('wrong result', (directory/'events.jsonl').read_text())

    def test_attempt_limit(self):
        coder = Mock(spec=CodingAgent)
        coder.mode = 'simulation'
        coder.write.return_value = 'SELECT status FROM builds'
        self.assertEqual(self.execute(coder=coder, attempts=2)[1], 'failed')
        self.assertEqual(coder.write.call_count, 2)
        with self.assertRaises(ValueError):
            self.execute(attempts=3)

    def test_intake_fails_closed(self):
        for changes in [{'estimated_cost_usd': 1}, {'requested_actions':['deploy']},
                        {'data_classification':'personal'}, {'recipe':'unknown'},
                        {'requested_actions':['draft_pull_request']}]:
            with self.subTest(changes=changes):
                task = dict(self.task, **changes)
                coder = Mock(spec=CodingAgent)
                coder.mode = 'simulation'
                directory, status = run(task, self.root, coder=coder)
                self.assertEqual(status, 'blocked')
                coder.write.assert_not_called()
                self.assertFalse(list(directory.glob('*.sql')))

    def test_artifact_requires_matching_turn_and_path_and_size(self):
        from types import SimpleNamespace
        api = Mock()
        store = api.beta.agents.sessions.artifacts
        artifact = SimpleNamespace(id='a', turn_id='t', path='/workspace/outputs/report.sql')
        store.list.return_value = [artifact]
        from contextlib import nullcontext
        response = Mock()
        response.iter_bytes.return_value = [b'SELECT ', b'1']
        store.with_streaming_response.content.return_value = nullcontext(response)
        coder = CodexArtifact(api, 's', 't')
        self.assertEqual(coder.write(), 'SELECT 1')
        store.with_streaming_response.content.assert_called_once_with('a', session_id='s')
        response.iter_bytes.return_value = [b'x' * 4097]
        with self.assertRaises(ValueError):
            coder.write()
        artifact.turn_id = 'different'
        with self.assertRaises(ValueError):
            coder.write()

    def test_cli_defaults_and_invalid_input(self):
        from contextlib import redirect_stdout, redirect_stderr
        from io import StringIO
        from ai_factory.phase_zero import main
        output = StringIO()
        with redirect_stdout(output):
            self.assertEqual(main(['--output', str(self.root)]), 0)
        self.assertEqual(json.loads(output.getvalue())['status'], 'awaiting_human_review')
        with redirect_stderr(StringIO()), self.assertRaises(SystemExit) as error:
            main(['--task', str(self.root/'absent')])
        self.assertEqual(error.exception.code, 2)

    def test_sdk_artifact_flow_without_network(self):
        try:
            from openai import OpenAI
            import httpx2 as httpx
        except ImportError:
            self.skipTest('optional OpenAI SDK unavailable')
        routes = []

        def respond(request):
            routes.append((request.method, request.url.path))
            self.assertEqual(request.headers['OpenAI-Beta'], 'agents=v1')
            if request.url.path.endswith('/content'):
                return httpx.Response(200, content=CodingAgent().write().encode())
            return httpx.Response(200, json={'data': [{
                'id': 'demo', 'turn_id': 't', 'session_id': 's', 'created_at': 0,
                'environment_id': 'e', 'object': 'agent.session.artifact',
                'size_bytes': 68, 'path': '/workspace/outputs/report.sql'
            }], 'has_more': False})

        http = httpx.Client(transport=httpx.MockTransport(respond))
        with OpenAI(api_key='synthetic', base_url='https://example.invalid/v1',
                    http_client=http, max_retries=0) as client:
            self.assertEqual(self.execute(coder=CodexArtifact(client, 's', 't'))[1],
                             'awaiting_human_review')
        self.assertEqual(routes, [
            ('GET', '/v1/agents/sessions/s/artifacts'),
            ('GET', '/v1/agents/sessions/s/artifacts/demo/content')
        ])
