"""Deterministic validation helpers for enterprise dependency records."""
from collections import defaultdict
from typing import Iterable, Mapping, Set, Tuple, Optional, List


def validate_dependency(record: Mapping, known_endpoint_ids: Set[str]) -> List[str]:
    """Return stable validation error codes; this function does not persist data."""
    errors = []
    source = record.get("source_id")
    target = record.get("target_id")
    if source and target and source == target:
        errors.append("self_dependency")
    if source not in known_endpoint_ids or target not in known_endpoint_ids:
        errors.append("unknown_endpoint")
    return errors


def find_dependency_cycle(edges: Iterable[Tuple[str, str]]) -> Optional[Tuple[str, ...]]:
    """Return the first deterministic directed cycle, or None.

    Pass only dependency edges whose semantics require an acyclic ordering
    (normally 'blocks' and 'requires'); informational relationships may cycle.
    """
    adjacency = defaultdict(set)
    nodes = set()
    for source, target in edges:
        adjacency[source].add(target)
        nodes.update((source, target))

    state = {}
    stack = []
    positions = {}

    def visit(node):
        state[node] = 1
        positions[node] = len(stack)
        stack.append(node)
        for neighbor in sorted(adjacency[node]):
            if state.get(neighbor, 0) == 0:
                found = visit(neighbor)
                if found:
                    return found
            elif state.get(neighbor) == 1:
                return tuple(stack[positions[neighbor]:] + [neighbor])
        stack.pop()
        positions.pop(node, None)
        state[node] = 2
        return None

    for node in sorted(nodes):
        if state.get(node, 0) == 0:
            found = visit(node)
            if found:
                return found
    return None
