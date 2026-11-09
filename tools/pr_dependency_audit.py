"""Offline PR dependency graph audit; consumes GitHub REST pull request JSON."""
import argparse
import json


def audit(pulls):
    if not isinstance(pulls, list):
        raise ValueError('pulls must be a list')
    by_head = {}
    for pr in pulls:
        number = pr['number']
        head = pr['head']['ref']
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
    return {'open_pr_count': len(pulls), 'stacked': [{'pr': n, 'depends_on_pr': parent} for n, parent in sorted(dependencies.items()) if parent is not None], 'independent': sorted(n for n, parent in dependencies.items() if parent is None)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('pulls_json', help='Saved GitHub REST /pulls?state=open JSON; no API access or credentials')
    args = parser.parse_args()
    with open(args.pulls_json, encoding='utf-8') as f:
        print(json.dumps(audit(json.load(f)), indent=2))


if __name__ == '__main__':
    main()
