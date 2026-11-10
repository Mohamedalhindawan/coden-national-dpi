"""Fail-closed graph and integrity validation for issue #55 PR inventory."""
from collections.abc import Mapping


def validate_inventory(data):
    """Return errors; never infer CI success or human approval."""
    errors = []
    if not isinstance(data, Mapping):
        return ["inventory must be an object"]
    if data.get("merge_policy") != "human_review_only":
        errors.append("merge policy must require human review")
    items = data.get("items")
    if not isinstance(items, list) or not items:
        return errors + ["items must be a nonempty list"]
    nodes = {}
    for index, item in enumerate(items):
        if not isinstance(item, Mapping):
            errors.append(f"item {index} must be an object")
            continue
        number = item.get("pr")
        if type(number) is not int or number <= 0:
            errors.append(f"item {index} has invalid PR number")
            continue
        if number in nodes:
            errors.append(f"duplicate PR {number}")
        nodes[number] = item
        if item.get("review") != "required" or item.get("decision") != "pending":
            errors.append(f"PR {number} has implicit approval")
        if item.get("ci") not in ("not_verified_in_this_snapshot", "pending", "failed"):
            errors.append(f"PR {number} has unverified CI assertion")
        if item.get("url") != f"https://github.com/Mohamedalhindawan/coden-national-dpi/pull/{number}":
            errors.append(f"PR {number} has invalid URL")
        if not isinstance(item.get("depends_on"), list):
            errors.append(f"PR {number} has invalid dependencies")
    edges = {}
    for number, item in nodes.items():
        deps = item.get("depends_on")
        if not isinstance(deps, list):
            continue
        edges[number] = []
        seen_deps = set()
        for dep in deps:
            if type(dep) is not int or dep not in nodes:
                errors.append(f"PR {number} has unknown dependency")
            elif dep in seen_deps:
                errors.append(f"PR {number} has duplicate dependency {dep}")
            elif dep == number:
                errors.append(f"PR {number} depends on itself")
            else:
                seen_deps.add(dep)
                edges[number].append(dep)
    overlaps = data.get("overlap_reviews", [])
    if not isinstance(overlaps, list):
        errors.append("overlap_reviews must be a list")
    else:
        for index, overlap in enumerate(overlaps):
            if not isinstance(overlap, Mapping):
                errors.append(f"overlap {index} must be an object")
                continue
            prs = overlap.get("prs")
            if not isinstance(prs, list) or len(prs) < 2:
                errors.append(f"overlap {index} must contain at least two PRs")
            else:
                seen = set()
                for pr in prs:
                    if type(pr) is not int or pr <= 0:
                        errors.append(f"overlap {index} has invalid PR identifier")
                    elif pr in seen:
                        errors.append(f"overlap {index} has duplicate PR {pr}")
                    elif pr not in nodes:
                        errors.append(f"overlap {index} references unknown PR {pr}")
                    else:
                        seen.add(pr)
            topic = overlap.get("topic")
            if not isinstance(topic, str) or not topic.strip():
                errors.append(f"overlap {index} missing topic")
    # Iterative DFS avoids RecursionError on large, untrusted inventories.
    visited, active = set(), set()
    for root in edges:
        if root in visited:
            continue
        stack = [(root, False)]
        while stack:
            node, exiting = stack.pop()
            if exiting:
                active.discard(node)
                visited.add(node)
                continue
            if node in active:
                errors.append(f"dependency cycle at PR {node}")
                continue
            if node in visited:
                continue
            active.add(node)
            stack.append((node, True))
            for dep in reversed(edges.get(node, [])):
                stack.append((dep, False))
    return errors
