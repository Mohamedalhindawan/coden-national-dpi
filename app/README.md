# Tamam Prototype

This is a static, browser-only demonstration of a social-assistance request flow.

## Preview
Open `index.html` in a browser, or use a browser-based development environment to preview the file.

## Current limits
- No server, database, login, or external API.
- Requests are held in memory only and disappear when the page is refreshed.
- The interface announces successful demo submission and review through an accessible status message, and offers a button to clear all demo requests from the current browser session. User-provided demo text is rendered as text, not interpreted as HTML.
- The demo form shows one inline Arabic error per invalid field: an empty or spaces-only synthetic name, a missing district, a household size that is not a whole number between 1 and 30, or a missing need type. Native browser validation UI is turned off with `novalidate` so these messages stay in Arabic and consistent; each message is announced through `role="alert"`, linked to its field with `aria-describedby`, marks the field with `aria-invalid`, and moves focus to the first field that needs correcting. Errors clear once the field is edited. These messages are demo guidance only, not eligibility or verification results.
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
