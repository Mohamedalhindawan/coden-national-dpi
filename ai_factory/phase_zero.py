"""Phase 0 factory. Run python -m ai_factory.phase_zero --help."""

import argparse
from contextlib import closing
from datetime import datetime, timezone
import json
import re
import sqlite3
import tempfile
from pathlib import Path

from .codex_artifact import CodexArtifact, MAX_BYTES
from .review_queue import prepare_review_queue

EXAMPLE = Path(__file__).with_name('examples') / 'build-summary.json'


class CodingAgent:
    mode = 'simulation'

    def write(self):
        return 'SELECT status, COUNT(*) FROM builds GROUP BY status ORDER BY status;\n'


class QAAgent:
    # Restrict grammar before SQLite sees model output. Only this report recipe is supported.
    vocabulary = set('select status count from builds as total group by order asc desc distinct'.split())
    cases = (
        ([], []),
        (['queued'], [('queued', 1)]),
        (['queued', 'failed', 'queued', 'done'], [('done', 1), ('failed', 1), ('queued', 2)]),
    )

    def check(self, query):
        if not query or len(query.encode()) > MAX_BYTES:
            raise ValueError('invalid candidate size')
        tokens = re.findall(r'[a-zA-Z]+|[^\s]', query)
        if any(t.lower() not in self.vocabulary and t not in '(),*;' for t in tokens):
            raise ValueError('unsupported SQL token')
        for statuses, expected in self.cases:
            with closing(sqlite3.connect(':memory:')) as db:
                db.execute('CREATE TABLE builds(status TEXT)')
                db.executemany('INSERT INTO builds VALUES (?)', [(s,) for s in statuses])
                db.execute('PRAGMA query_only=ON')
                db.set_progress_handler(lambda: 1, 10000)
                if db.execute(query).fetchmany(len(expected) + 1) != expected:
                    raise ValueError('wrong result')
        return len(self.cases)


def run(task, root, *, attempts=1, coder=None, qa=None):
    """Coordinate one synthetic recipe and return its private evidence directory and status."""
    if type(attempts) is not int or attempts not in (1, 2):
        raise ValueError('attempts must be 1 or 2')
    coder = CodingAgent() if coder is None else coder
    qa = QAAgent() if qa is None else qa
    directory = Path(tempfile.mkdtemp(prefix='coden-run-', dir=root))

    def record(role, status, **fields):
        event = dict(time=datetime.now(timezone.utc).isoformat(), mode=coder.mode,
                     role=role, status=status, **fields)
        with (directory / 'events.jsonl').open('a', encoding='utf-8') as log:
            log.write(json.dumps(event) + '\n')

    review = prepare_review_queue([task], budget_usd=0)
    if not review['valid']:
        record('orchestrator', 'blocked', errors=review['errors'])
        return directory, 'blocked'
    if task.get('recipe') != 'build-summary' or task['requested_actions'] != ['run_tests']:
        record('orchestrator', 'blocked', reason='unsupported recipe or actions')
        return directory, 'blocked'

    record('orchestrator', 'planned', task_id=task['id'], recipe='build-summary', steps=['coding', 'qa', 'human_review'],
           budget_usd=0, attempts=attempts, execution_authorized=False)
    for attempt in range(1, attempts + 1):
        role = 'coding'
        try:
            query = coder.write()
            if len(query.encode()) > MAX_BYTES:
                raise ValueError('oversized artifact')
            filename = f'candidate-{attempt}.sql'
            (directory / filename).write_text(query, encoding='utf-8')
            record(role, 'candidate', attempt=attempt, artifact=filename)
            role = 'qa'
            passed = qa.check(query)
            record(role, 'passed', attempt=attempt, passed=passed)
        except Exception as exc:
            # SDK errors may include request details. Only emit fixed diagnostics.
            reason = 'wrong result' if type(exc) is ValueError and exc.args == ('wrong result',) else type(exc).__name__
            record(role, 'failed', attempt=attempt, reason=reason)
            continue
        record('orchestrator', 'awaiting_human_review')
        return directory, 'awaiting_human_review'
    record('orchestrator', 'failed')
    return directory, 'failed'


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--task', type=Path, default=EXAMPLE)
    parser.add_argument('--output', type=Path, help='Existing parent directory (default: system temp)')
    parser.add_argument('--attempts', type=int, choices=(1, 2), default=1)
    parser.add_argument('--codex-artifact', nargs=2, metavar=('SESSION', 'TURN'),
                        help='Read an existing Codex artifact via the Agents API')
    args = parser.parse_args(argv)
    try:
        task = json.loads(args.task.read_text(encoding='utf-8'))
        if args.codex_artifact:
            from openai import OpenAI
            with OpenAI(max_retries=0, timeout=15.0) as client:
                result = run(task, args.output, attempts=args.attempts,
                             coder=CodexArtifact(client, *args.codex_artifact))
        else:
            result = run(task, args.output, attempts=args.attempts)
    except Exception as exc:
        parser.exit(2, f'Factory input or setup error ({type(exc).__name__})\n')
    directory, status = result
    print(json.dumps({'status': status, 'directory': str(directory)}))
    return int(status != 'awaiting_human_review')


if __name__ == '__main__':
    raise SystemExit(main())
