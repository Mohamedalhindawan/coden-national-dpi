"""Read-only policy check; does not authenticate humans or grant write access."""


def assess_pr_handoff(manifest):
    blocked = {"status": "blocked", "can_create_pr": False, "can_merge": False}
    if not isinstance(manifest, dict):
        return blocked
    expected = {
        "proposal_only": True,
        "source": "synthetic_demo",
        "files": ["demo-task.txt"],
        "github_write_permitted": False,
        "pull_request_created": False,
        "requires_human_review": True,
    }
    if manifest != expected:
        return blocked
    return {"status": "awaiting_human_review", "can_create_pr": False, "can_merge": False}
