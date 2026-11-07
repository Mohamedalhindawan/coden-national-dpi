"""Deterministic dependency planning for CODEN task graphs.

This module plans waves and derives readiness/blocking state. It never schedules,
executes, retries, or invokes providers.
"""
from collections import defaultdict, deque


class DAGError(ValueError):
    pass


VALID_STATES = {"pending", "ready", "running", "succeeded", "failed", "blocked", "cancelled"}


def _normalize(tasks):
    if not isinstance(tasks, list) or not tasks:
        raise DAGError("Tasks must be a non-empty list")
    by_id = {}
    for task in tasks:
        if not isinstance(task, dict):
            raise DAGError("Each task must be an object")
        task_id = task.get("task_id")
        if not isinstance(task_id, str) or not task_id.strip():
            raise DAGError("Every task requires a non-empty task_id")
        if task_id in by_id:
            raise DAGError("Duplicate task_id: " + task_id)
        dependencies = task.get("depends_on", [])
        if not isinstance(dependencies, list) or any(
            not isinstance(item, str) or not item.strip() for item in dependencies
        ):
            raise DAGError("depends_on must be a list of non-empty task IDs")
        if len(dependencies) != len(set(dependencies)):
            raise DAGError("Duplicate dependency for task: " + task_id)
        if task_id in dependencies:
            raise DAGError("Task cannot depend on itself: " + task_id)
        by_id[task_id] = dependencies
    for task_id, dependencies in by_id.items():
        missing = sorted(set(dependencies) - set(by_id))
        if missing:
            raise DAGError("Unknown dependencies for " + task_id + ": " + ", ".join(missing))
    return by_id


def build_execution_plan(tasks):
    graph = _normalize(tasks)
    indegree = {task_id: len(dependencies) for task_id, dependencies in graph.items()}
    dependents = defaultdict(list)
    for task_id, dependencies in graph.items():
        for dependency in dependencies:
            dependents[dependency].append(task_id)
    frontier = sorted(task_id for task_id, degree in indegree.items() if degree == 0)
    waves = []
    visited = 0
    while frontier:
        wave = frontier
        waves.append(wave)
        visited += len(wave)
        next_frontier = []
        for completed in wave:
            for child in dependents[completed]:
                indegree[child] -= 1
                if indegree[child] == 0:
                    next_frontier.append(child)
        frontier = sorted(next_frontier)
    if visited != len(graph):
        cyclic = sorted(task_id for task_id, degree in indegree.items() if degree > 0)
        raise DAGError("Dependency cycle detected involving: " + ", ".join(cyclic))
    return {
        "plan_version": "1.0.0",
        "task_count": len(graph),
        "wave_count": len(waves),
        "waves": waves,
        "parallelism_max": max(map(len, waves)),
    }


def ready_tasks(tasks, states):
    graph = _normalize(tasks)
    if not isinstance(states, dict):
        raise DAGError("states must be a task_id-to-state mapping")
    unknown = sorted(set(states) - set(graph))
    if unknown:
        raise DAGError("States supplied for unknown tasks: " + ", ".join(unknown))
    for task_id, state in states.items():
        if state not in VALID_STATES:
            raise DAGError("Invalid state for " + task_id + ": " + str(state))
    current = {task_id: states.get(task_id, "pending") for task_id in graph}
    return sorted(
        task_id for task_id, dependencies in graph.items()
        if current[task_id] in {"pending", "ready"}
        and all(current[dependency] == "succeeded" for dependency in dependencies)
    )


def propagate_blocked(tasks, states):
    graph = _normalize(tasks)
    if not isinstance(states, dict):
        raise DAGError("states must be a task_id-to-state mapping")
    unknown = sorted(set(states) - set(graph))
    if unknown:
        raise DAGError("States supplied for unknown tasks: " + ", ".join(unknown))
    for task_id, state in states.items():
        if state not in VALID_STATES:
            raise DAGError("Invalid state for " + task_id + ": " + str(state))
    reverse = defaultdict(list)
    for task_id, dependencies in graph.items():
        for dependency in dependencies:
            reverse[dependency].append(task_id)
    blocked = set()
    queue = deque(sorted(task_id for task_id, state in states.items()
                         if state in {"failed", "blocked", "cancelled"}))
    visited = set(queue)
    while queue:
        failed = queue.popleft()
        for child in reverse[failed]:
            if child not in visited:
                visited.add(child)
                blocked.add(child)
                queue.append(child)
    return sorted(blocked)


def retry_allowed(task_policy, attempts):
    if not isinstance(task_policy, dict):
        raise DAGError("Task retry policy must be an object")
    maximum = task_policy.get("max_retries")
    if isinstance(maximum, bool) or not isinstance(maximum, int) or not 0 <= maximum <= 3:
        raise DAGError("max_retries must be an integer between 0 and 3")
    if isinstance(attempts, bool) or not isinstance(attempts, int) or attempts < 0:
        raise DAGError("attempts must be a non-negative integer")
    return attempts < maximum
