"""Create one synthetic artifact in an isolated workspace; never touch the repository."""
import re
from pathlib import Path


def preview_synthetic_patch(workspace, task_id):
    if not isinstance(task_id, str) or re.fullmatch(r"[A-Za-z0-9_-]{1,64}", task_id) is None:
        return {"status": "blocked", "reason": "invalid_task_id"}
    root = Path(workspace)
    folder = root / "output"
    if folder.is_symlink() or folder.exists() and not folder.is_dir():
        return {"status": "blocked", "reason": "unsafe_output"}
    try:
        folder.mkdir(parents=True, exist_ok=True)
        target = folder / "demo-task.txt"
        with target.open("x", encoding="utf-8") as handle:
            handle.write(f"CODEN demo task: {task_id}\n")
    except (FileExistsError, OSError):
        return {"status": "blocked", "reason": "output_exists_or_unavailable"}
    return {"status": "preview_created", "path": "output/demo-task.txt"}
