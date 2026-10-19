# Tamam Prototype

This is a static, browser-only demonstration of a social-assistance request flow.

## Preview
Open `index.html` in a browser, or use a browser-based development environment to preview the file.

## Current limits
- No server, database, login, or external API.
- Requests are held in memory only and disappear when the page is refreshed.
- All entries must be synthetic. Do not enter real names, phone numbers, identity numbers, addresses, or other citizen information.
- The prototype does not assess eligibility, approve benefits, or make payment decisions.
- It is not ready for real users or production.

## Checks
From the repository root, run:

```sh
python -m unittest discover -s tests -v
```

The GitHub Actions workflow runs the same contract checks on pushes and pull requests.
