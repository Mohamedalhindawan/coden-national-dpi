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


SELF_TASK_ID = "CODEN-SELF-001"
SELF_TEST_PATH = "tests/test_factory_queue_alerts.py"
MAX_SELF_SOURCE_BYTES = 65536
MAX_SELF_ADDITION_BYTES = 16384


def assess_self_development(*, task_id, base_commit, expected_base_commit,
                            original, expected_original_sha256, files):
    """Review-only structural intake for one narrowly scoped test proposal.

    The operator supplies trusted original bytes, expected digest and base
    commit; this function does not authenticate Git, the agent, or the caller.
    New method bodies remain untrusted, even if syntax and scope match.
    No filesystem, network, test execution, PR creation or approval occurs.
    """
    import ast
    import hashlib
    import re

    blocked = {"status": "blocked", "agent_origin_verified": False,
               "tests_executed": False, "execution_authorized": False,
               "can_create_pr": False, "can_merge": False,
               "release_authorized": False, "automatic_retry_allowed": False}
    if (task_id != SELF_TASK_ID
            or type(base_commit) is not str
            or not re.fullmatch(r"[0-9a-f]{40}", base_commit)
            or type(expected_base_commit) is not str
            or base_commit != expected_base_commit
            or type(expected_original_sha256) is not str
            or not re.fullmatch(r"[0-9a-f]{64}", expected_original_sha256)
            or type(original) is not bytes
            or not 0 < len(original) <= MAX_SELF_SOURCE_BYTES
            or not original.endswith(b"\n")
            or hashlib.sha256(original).hexdigest() != expected_original_sha256
            or type(files) is not dict or set(files) != {SELF_TEST_PATH}):
        return blocked
    candidate = files[SELF_TEST_PATH]
    if (type(candidate) is not bytes or len(candidate) > MAX_SELF_SOURCE_BYTES
            or not 0 < len(candidate) - len(original) <= MAX_SELF_ADDITION_BYTES
            or not candidate.startswith(original)):
        return blocked
    try:
        before = ast.parse(original.decode("utf-8"))
        after = ast.parse(candidate.decode("utf-8"))
        if (not before.body or len(before.body) != len(after.body)
                or not isinstance(before.body[-1], ast.ClassDef)
                or not isinstance(after.body[-1], ast.ClassDef)):
            return blocked
        old, new = before.body[-1], after.body[-1]
        if old.name != "QueueAlertTests" or new.name != old.name:
            return blocked
        if any(ast.dump(a) != ast.dump(b)
               for a, b in zip(before.body[:-1], after.body[:-1])):
            return blocked
        if len(new.body) <= len(old.body):
            return blocked
        prefix, additions = new.body[:len(old.body)], new.body[len(old.body):]
        if not 1 <= len(additions) <= 4:
            return blocked
        # Compile only: AST parsing alone accepts invalid control flow.
        compile(after, "<self-development-review>", "exec", dont_inherit=True)
        # Comparing the entire old class, including existing method bodies,
        # also rejects suffixes that change the last existing statement.
        new.body = prefix
        if ast.dump(old) != ast.dump(new):
            return blocked
        # Include non-function class bindings: no new test may shadow them.
        names = {node.name for node in old.body
                 if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))}
        names.update(node.id for stmt in old.body for node in ast.walk(stmt)
                     if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store))
        for method in additions:
            if (type(method) is not ast.FunctionDef
                    or not re.fullmatch(r"test_[a-z][a-z0-9_]{0,79}", method.name)
                    or method.name in names or method.decorator_list
                    or method.returns is not None
                    # Generator tests can return without running assertions.
                    or any(isinstance(node, (ast.Yield, ast.YieldFrom))
                           for node in ast.walk(method))
                    or getattr(method, "type_params", [])
                    or ast.dump(method.args) != ast.dump(ast.parse("def f(self): pass").body[0].args)):
                return blocked
            names.add(method.name)
    except (SyntaxError, UnicodeError, ValueError, RecursionError, MemoryError):
        return blocked
    return dict(blocked, status="awaiting_human_review",
                task_id=SELF_TASK_ID, base_commit=base_commit,
                original_sha256=expected_original_sha256,
                candidate_sha256=hashlib.sha256(candidate).hexdigest(),
                path=SELF_TEST_PATH, added_test_methods=len(additions),
                structural_scope_matched=True)
