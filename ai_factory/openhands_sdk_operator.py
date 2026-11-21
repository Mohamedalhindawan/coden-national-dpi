"""Opt-in official OpenHands SDK Conversation bridge for a synthetic local-model pilot.

This module does NOT install Docker, an agent SDK or a model. Its managed
entrypoint may start ONE upstream DockerWorkspace container only after explicit
operator opt-in and fail-closed local daemon/network/image preflight. An expert
may instead supply a pre-created DockerWorkspace to run_once. Both require
an isolated export mount and an audited local Ollama network. SDK imports
are lazy and CI injects stand-ins to verify the contract.

The OpenHands SDK runs the agent; CODEN only supplies policy, a restricted
prompt and independent multi-file artifact review. No automatic retry,
approval, merge, production release or paid provider fallback.
"""
import json
import os
import re
import subprocess

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


def _context_is_local(context):
    """Restrict Docker CLI to known local Unix socket endpoints only.

    A Unix endpoint is necessary, not sufficient, for a secure Docker daemon:
    the operator must still verify socket ownership, image provenance,
    firewall policy and absence of an untrusted local proxy.
    """
    if not isinstance(context, dict):
        return False
    endpoints = context.get("Endpoints")
    if not isinstance(endpoints, dict):
        return False
    docker = endpoints.get("docker")
    if not isinstance(docker, dict):
        return False
    allowed = {
        "unix:///var/run/docker.sock",
        "unix:///run/docker.sock",
        f"unix:///run/user/{os.getuid()}/docker.sock",
    }
    return docker.get("Host") in allowed and docker.get("SkipTLSVerify") is not True


def _inspect_local_docker(kind, name):
    """Read metadata only; never start a Docker container or pull an image."""
    if kind not in ("network", "image", "context"):
        raise ValueError("unsupported Docker inspect target")
    if kind == "context":
        if name != "current":
            raise ValueError("only active Docker context may be inspected")
        command = ["docker", "context", "inspect"]
    else:
        command = ["docker", kind, "inspect", name]
    result = subprocess.run(
        command, capture_output=True, text=True, timeout=5, check=False
    )
    if result.returncode or len(result.stdout) > 65536:
        raise ValueError("Docker inspect unavailable")
    parsed = json.loads(result.stdout)
    if not isinstance(parsed, list) or len(parsed) != 1 or not isinstance(parsed[0], dict):
        raise ValueError("untrusted Docker inspect reply")
    return parsed[0]


def launch_isolated(*, task, candidate_root, output_root, model, base_url,
                    server_image, network, allow_agent=False,
                    sdk=None, inspect_docker=None, preflight_only=False):
    """Safe entry path: preflight before DockerWorkspace constructor side effects.

    A regular DockerWorkspace constructs/starts its container during init.
    This is the only managed path CODEN should use for a future real SDK
    pilot; it validates immutable image, isolated network and installed
    local sandbox BEFORE constructing the SDK workspace.

    Docker network 'Internal' is only one layer of defense. Require an
    independently audited local Docker daemon, firewall, pinned model and
    external watchdog before using this on an operator-controlled machine.
    """
    if type(allow_agent) is not bool or type(preflight_only) is not bool:
        raise ValueError("explicit boolean operator mode required")
    if not (allow_agent or preflight_only):
        return _result("disabled")
    if not project.valid(task) or task.get("recipe") != "python-transform":
        raise ValueError("synthetic-only reviewed transform required")
    if (not isinstance(model, str) or not LOCAL_MODEL.fullmatch(model)
            or "cloud" in model.lower()):
        raise ValueError("local Ollama model required")
    if base_url != "http://ollama:11434":
        raise ValueError("unexpected local model endpoint")
    if not isinstance(server_image, str) or not PINNED_IMAGE.fullmatch(server_image):
        raise ValueError("pinned OpenHands image digest required")
    if (not isinstance(network, str) or not NETWORK.fullmatch(network)
            or network.lower() in FORBIDDEN_NETWORKS):
        raise ValueError("dedicated named Docker network required")

    export = openhands_multifile_review._trusted_dir(candidate_root)
    openhands_multifile_review._trusted_dir(output_root)
    if any(export.iterdir()):
        raise ValueError("export must start empty")

    # Docker CLI honors these variables and may contact a different daemon.
    # The operator must also check the local active Docker context explicitly.
    if any(key in os.environ for key in UNSAFE_ENV_KEYS | {
        "DOCKER_HOST", "DOCKER_CONTEXT", "DOCKER_TLS_VERIFY",
        "DOCKER_CERT_PATH",
    }):
        return _result("unsafe_environment")
    if not project.supported_host():
        return _result("sandbox_unavailable")

    inspect = _inspect_local_docker if inspect_docker is None else inspect_docker
    try:
        context = inspect("context", "current")
        if not _context_is_local(context):
            return _result("unsafe_runtime")
        net = inspect("network", network)
        if not isinstance(net, dict) or net.get("Internal") is not True or net.get("Driver") != "bridge":
            return _result("unsafe_runtime")
        image = inspect("image", server_image)
        if (not isinstance(image, dict)
                or not isinstance(image.get("RepoDigests"), list)
                or server_image not in image["RepoDigests"]
                or not isinstance(image.get("Id"), str)
                or not re.fullmatch(r"sha256:[0-9a-f]{64}", image["Id"])):
            return _result("unsafe_runtime")
    except (OSError, ValueError, TypeError, subprocess.SubprocessError):
        return _result("unsafe_runtime")

    # Preflight can confirm metadata, never Docker isolation, model readiness,
    # signed image provenance, model weight license or available resources.
    if preflight_only:
        return _result("preflight_passed")

    installed = _official_sdk() if sdk is None else sdk
    if installed is None:
        return _result("sdk_unavailable")

    try:
        # Do NOT use :latest images, default forwarding, privileged mode,
        # implicit host repository mounts, cloud credentials or public nets.
        # SDK owns the real Docker lifecycle; CODEN does not reimplement it.
        with installed.DockerWorkspace(
            server_image=server_image,
            volumes=[f"{export}:/workspace/export:rw"],
            forward_env=[],
            network=network,
            extra_ports=False,
            enable_gpu=False,
            detach_logs=False,
        ) as workspace:
            return run_once(
                task=task,
                candidate_root=export,
                output_root=output_root,
                workspace=workspace,
                model=model,
                base_url=base_url,
                allow_agent=True,
                sdk=installed,
            )
    except Exception:
        # SDK construction can have started a container before raising.
        # Report uncertainty and require operator cleanup, never retry.
        return _result("workspace_start_failed_review_required", attempted=True)



def main(argv=None):
    """CLI operator entrypoint: no agent, network or file reads by default."""
    import argparse
    import sys

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task", required=True)
    parser.add_argument("--candidate-dir", required=True)
    parser.add_argument("--output-root", required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--base-url", default="http://ollama:11434")
    parser.add_argument("--server-image", required=True)
    parser.add_argument("--network", required=True)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--allow-agent", action="store_true",
                      help="Explicit operator permission for one SDK conversation")
    mode.add_argument("--preflight-only", action="store_true",
                      help="Read-only local Docker/sandbox checks, never start a container")
    args = parser.parse_args(argv)

    # Do not inspect directories, Docker, SDK installation, model or task when
    # no real operation is requested.
    if not (args.allow_agent or args.preflight_only):
        print(json.dumps(_result("disabled"), sort_keys=True))
        return 0

    try:
        task = json.loads(project.read_text(args.task, 32768))
        outcome = launch_isolated(
            task=task,
            candidate_root=args.candidate_dir,
            output_root=args.output_root,
            model=args.model,
            base_url=args.base_url,
            server_image=args.server_image,
            network=args.network,
            allow_agent=args.allow_agent,
            preflight_only=args.preflight_only,
        )
    except (OSError, ValueError, TypeError, RuntimeError, json.JSONDecodeError):
        outcome = _result("invalid_config")

    if "directory" in outcome:
        outcome["directory"] = str(outcome["directory"])
    print(json.dumps(outcome, sort_keys=True))
    return 0 if outcome["status"] in ("awaiting_human_review", "preflight_passed") else 1


if __name__ == "__main__":
    raise SystemExit(main())
