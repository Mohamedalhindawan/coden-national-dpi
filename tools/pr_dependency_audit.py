"""Offline PR dependency graph audit; consumes GitHub REST pull request JSON."""
import argparse
import json


def audit(pulls, default_branch='main'):
    if not isinstance(default_branch, str) or not default_branch.strip():
        raise ValueError('invalid default branch')
    if not isinstance(pulls, list):
        raise ValueError('pulls must be a list')
    by_head = {}
    by_number = set()
    for pr in pulls:
        try:
            number = pr['number']
            head = pr['head']['ref']
            base = pr['base']['ref']
        except (TypeError, KeyError) as exc:
            raise ValueError('malformed PR record') from exc
        if isinstance(number, bool) or not isinstance(number, int) or number <= 0:
            raise ValueError('invalid PR number')
        if not isinstance(head, str) or not head.strip() or not isinstance(base, str) or not base.strip():
            raise ValueError('invalid PR branch ref')
        if number in by_number:
            raise ValueError(f'duplicate PR number: {number}')
        by_number.add(number)
        if head in by_head:
            raise ValueError(f'duplicate head branch: {head}')
        by_head[head] = number
    dependencies = {}
    for pr in pulls:
        base = pr['base']['ref']
        dependencies[pr['number']] = by_head.get(base)
    seen, active = set(), set()
    def visit(n):
        if n in active:
            raise ValueError('dependency cycle')
        if n in seen:
            return
        active.add(n)
        parent = dependencies[n]
        if parent is not None:
            visit(parent)
        active.remove(n)
        seen.add(n)
    for n in dependencies:
        visit(n)
    unresolved = sorted(
        [{'pr': pr['number'], 'base_ref': pr['base']['ref']} for pr in pulls
         if dependencies[pr['number']] is None and pr['base']['ref'] != default_branch],
        key=lambda item: item['pr'],
    )
    return {'unresolved_bases': unresolved, 'open_pr_count': len(pulls), 'stacked': [{'pr': n, 'depends_on_pr': parent} for n, parent in sorted(dependencies.items()) if parent is not None], 'independent': sorted(pr['number'] for pr in pulls if dependencies[pr['number']] is None and pr['base']['ref'] == default_branch)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('pulls_json', help='Saved GitHub REST /pulls?state=open JSON; no API access or credentials')
    args = parser.parse_args()
    with open(args.pulls_json, encoding='utf-8') as f:
        print(json.dumps(audit(json.load(f)), indent=2))


if __name__ == '__main__':
    main()
