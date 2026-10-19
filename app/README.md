# Tamam Prototype

This is a static, browser-only demonstration of a social-assistance request flow.

## Preview
Open `index.html` in a browser, or use a browser-based development environment to preview the file.

## Current limits
- No server, database, login, or external API.
- Requests are held in memory only and disappear when the page is refreshed.
- The interface announces successful demo submission and review through an accessible status message. User-provided demo text is rendered as text, not interpreted as HTML.
- The list includes a demo-only button to mark a request as reviewed. This is a local UI simulation, not an official SFD review or benefit decision; the status disappears on refresh.
- All entries must be synthetic. Do not enter real names, phone numbers, identity numbers, addresses, or other citizen information.
- The prototype does not assess eligibility, approve benefits, or make payment decisions.
- Do not interpret “تمت مراجعة تجريبية” as an official decision.
- It is not ready for real users or production.

## Checks
From the repository root, run:

```sh
python -m unittest discover -s tests -v
```

The GitHub Actions workflow runs the same contract checks on pushes and pull requests.
