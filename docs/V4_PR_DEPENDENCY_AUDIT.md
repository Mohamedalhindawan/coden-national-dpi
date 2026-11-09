# V4 pull request dependency audit

Run on a locally saved JSON response from GitHub REST `GET /repos/Mohamedalhindawan/coden-national-dpi/pulls?state=open&per_page=100`:

```sh
python tools/pr_dependency_audit.py open-pulls.json
python -m unittest discover -s tests -p 'test_pr_dependency_audit.py' -v
```

No network access, tokens, GitHub write permissions or citizen data are required. The audit identifies PRs stacked by base branch, detects cycles and duplicate head branches. It does **not** prove merge readiness, code quality or passing CI. PRs targeting a base outside the input page appear independent; fetch all pages before using the output to make review decisions.

Current observed examples on 2026-11-09: #37 is based on main, #38 depends on #37 through #47; #58 is based on main, #59 depends on #58 through #65. Keep these chains intact during review. Coordinate with issue #55 and PR #57. Human approval remains mandatory before merging.
