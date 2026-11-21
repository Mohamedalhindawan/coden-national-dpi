"""Opt-in official OpenHands SDK Conversation bridge for a synthetic local-model pilot.

This module does NOT create Docker containers or install an agent SDK. A trusted
operator must provide an already-running DockerWorkspace with one empty,
isolated export mount and an internally isolated Ollama network. Import of the
official upstream SDK is lazy; CI injects a stand-in to verify the contract.

The OpenHands SDK runs the agent; CODEN only supplies policy, a restricted
prompt and independent multi-file artifact review. No automatic retry,
approval, merge, production release or paid provider fallback.
"""
import os
import re

from . import openhands_multifile_review, project

PINNED_IMAGE = re.compile(
    r"ghcr[.]io/openhands/agent-server@sha256:[0-9a-f]{64}\Z"
)
NETWORK = re.compile(r"[A-Za-z][A-Za-z0-9_.-]{0,63}\Z")
LOCAL_MODEL = re.compile(r"ollama/[A-Za-z0-9][A-Za-z0-9._:/-]{0,127}\Z")
FORBIDDEN_NETWORKS = frozenset({"host", "bridge", "none", "default"})
UNSAFE_ENV_KEYS = frozenset({
    "OPENAI_API_KEY", "ANTHROPIC_API_KEY", "LLM_API_KEY",
    "OLLAMA_API_KEY", "CODEX_AUTH_TOKEN", "GOOGLE_API_KEY",
})


def _result(status, attempted=False):
    return {
        "status": status,
        "agent_session_attempted": attempted,
        "execution_authorized": False,
        "release_authorized": False,
        "automatic_retry_allowed": False,
    }


def _official_sdk():
    try:
        from openhands.sdk import LLM, Agent, Conversation, Tool
        from openhands.tools.file_editor import FileEditorTool
        from openhands.tools.terminal import TerminalTool
        from openhands.workspace import DockerWorkspace
    except ImportError:
        return None

    from types import SimpleNamespace
    return SimpleNamespace(LLM=LLM, Agent=Agent, Tool=Tool,
                           Conversation=Conversation,
                           FileEditorTool=FileEditorTool,
                           TerminalTool=TerminalTool,
                           DockerWorkspace=DockerWorkspace)


def _workspace(workspace, sdk, root):
    if not isinstance(workspace, sdk.DockerWorkspace):
        raise ValueError("DockerWorkspace is mandatory")
    if not isinstance(getattr(workspace, "server_image", None), str) or not PINNED_IMAGE.fullmatch(workspace.server_image):
        raise ValueError("immutable OpenHands container image required")
    if workspace.volumes != [f"{root}:/workspace/export:rw"]:
        raise ValueError("single dedicated writable export mount required")
    if workspace.forward_env != [] or workspace.extra_ports is not False or workspace.enable_gpu is not False:
        raise ValueError("unsafe workspace privileges or inherited credentials")
    network = workspace.network
    if (not isinstance(network, str) or not NETWORK.fullmatch(network)
            or network.lower() in FORBIDDEN_NETWORKS):
        raise ValueError("explicit isolated Docker network required")
    # This structural check cannot prove Docker network isolation or image
    # provenance. Operators must independently attest firewall and image SBOM.


def _prompt(task):
    # Review-only acceptance cases are intentionally not provided to the SDK.
    return (
        "Synthetic offline CODEN programming pilot. Your only permitted task "
        "is to author EXACTLY these files in /workspace/export: "
        "app/logic.py, README.md, tests/test_logic.py. "
        "The only executable code must be app/logic.py, consisting of exactly "
        "one function def transform(value), with no imports, helper functions, "
        "network or filesystem use. Do not touch any other workspace files, "
        "run untrusted dependencies, fetch packages, call cloud services, "
        "make GitHub changes, or approve deployment. "
        "Return only the files, no release claims. Requirements: "
        + task["description"]
        + "\nVisible cases (not the independent hidden review cases): "
        + project.encoded(task["cases"])
    )


def run_once(*, task, candidate_root, output_root, workspace, model,
             base_url, allow_agent=False, sdk=None):
    """Execute one SDK Conversation ONLY with explicit operator opt-in.

    SDK must already be installed/pinned, and the operator must have created,
    network-isolated, and supervised DockerWorkspace before calling this.
    """
    if type(allow_agent) is not bool:
        raise ValueError("explicit boolean operator approval required")
    if not allow_agent:
        return _result("disabled")

    if not project.valid(task) or task.get("recipe") != "python-transform":
        raise ValueError("synthetic reviewed transform task required")
    if (not isinstance(model, str) or not LOCAL_MODEL.fullmatch(model)
            or "cloud" in model.lower()):
        raise ValueError("local Ollama-only model identifier required")
    if base_url != "http://ollama:11434":
        raise ValueError("only operator-owned Docker-network Ollama endpoint allowed")

    export = openhands_multifile_review._trusted_dir(candidate_root)
    outputs = openhands_multifile_review._trusted_dir(output_root)
    if any(export.iterdir()):
        raise ValueError("isolated export must start empty")
    if any(key in os.environ for key in UNSAFE_ENV_KEYS):
        return _result("unsafe_environment")

    installed = _official_sdk() if sdk is None else sdk
    if installed is None:
        return _result("sdk_unavailable")
    _workspace(workspace, installed, export)

    if not project.supported_host():
        return _result("sandbox_unavailable")

    conversation = None
    try:
        # Upstream SDK agent and tools are reused; there is NO custom agent
        # execution engine. Provider session and tools must be confined to
        # the operator's isolated container/network.
        llm = installed.LLM(model=model, base_url=base_url, api_key="local")
        agent = installed.Agent(
            llm=llm,
            tools=[installed.Tool(name=installed.TerminalTool.name),
                   installed.Tool(name=installed.FileEditorTool.name)],
        )
        conversation = installed.Conversation(agent=agent, workspace=workspace)
        conversation.send_message(_prompt(task))
        conversation.run()
    except Exception:
        # Child may have already created files. Do not replay automatically
        # or allow a failed agent's message to constitute review evidence.
        return _result("agent_failed_review_required", attempted=True)
    finally:
        if conversation is not None:
            try:
                conversation.close()
            except Exception:
                pass

    try:
        accepted = openhands_multifile_review.review(task, export, outputs)
    except (OSError, ValueError, TypeError, RuntimeError):
        return _result("artifact_review_required", attempted=True)
    return {**accepted, "agent_session_attempted": True,
            "execution_authorized": False, "release_authorized": False,
            "automatic_retry_allowed": False}
