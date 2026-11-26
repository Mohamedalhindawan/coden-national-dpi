"""Opt-in official OpenHands SDK Conversation bridge for a synthetic local-model pilot.

This module does NOT install Docker, an agent SDK or a model. Issue #162
blocks the real default SDK path; injected SDKs are trusted test fixtures only.
Its managed
entrypoint may start ONE upstream DockerWorkspace container only after explicit
operator opt-in and fail-closed local daemon/network/image preflight. An expert
may instead supply a pre-created DockerWorkspace to run_once. Both require
an isolated export mount and an audited local Ollama network. SDK imports
are lazy and CI injects stand-ins to verify the contract.

The OpenHands SDK runs the agent; CODEN only supplies policy, a restricted
prompt and independent multi-file artifact review. No automatic retry,
approval, merge, production release or paid provider fallback.
"""
import hashlib
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


def review_qwen_route(*, model, base_url):
    """Review-only SDK configuration for the previously probed Qwen3 alias.

    This does not resolve DNS, contact the endpoint, bind a credential, import
    SDK or permit a Conversation. The final isolated route and an operator-
    owned authentication boundary still require independent runtime admission.
    Never pass this incomplete configuration directly to a live SDK.
    """
    if (type(model) is not str or model != "openai/local-qwen"
            or type(base_url) is not str or base_url != "http://qwen3:11434/v1"):
        raise ValueError("only the reviewed local Qwen route is eligible")
    return {
        "status": "review_only_route",
        "llm_options": {
            "model": model,
            "base_url": base_url,
            "api_mode": "chat",
            # Pinned SDK retry_mixin uses stop_after_attempt(num_retries).
            "num_retries": 1,
            "timeout": 35,
            "drop_params": False,
            "fallback_strategy": None,
        },
        "model_sha256": "9465e63a22add5354d9bb4b99e90117043c7124007664907259bd16d043bb031",
        "credentials_bound": False,
        "network_verified": False,
        "sdk_imported": False,
        "agent_session_attempted": False,
        "execution_authorized": False,
        "release_authorized": False,
        "automatic_retry_allowed": False,
    }


def _fixture_llm_options(model, base_url):
    """Shared exact route validation for injected SDK fixtures only.

    Real SDK admission remains blocked before this helper is called. The
    placeholder is not an authentication mechanism or production secret.
    """
    if model == "openai/local-qwen":
        return {**review_qwen_route(model=model,base_url=base_url)["llm_options"],
                "api_key":"fixture-only"}
    if (type(model) is not str or not LOCAL_MODEL.fullmatch(model)
            or "cloud" in model.lower() or base_url != "http://ollama:11434"):
        raise ValueError("only reviewed local fixture routes allowed")
    return {"model":model,"base_url":base_url,"api_key":"local"}


MODEB_TASK_SHA256 = "81706571edbff4228be140b398a0fddc5b4df84de50407b06f46c2397f009d0f"


def prepare_modeb_request(task):
    """Exact first-task intent, not a capability or authority to execute.

    No host path, secret, hidden case, SDK object, or arbitrary tool command
    is passed across this boundary. The external isolated adapter is not
    implemented/admitted yet. This policy does not itself confine tools.
    """
    encoded = project.encoded(task)
    if hashlib.sha256(encoded.encode("utf-8")).hexdigest() != MODEB_TASK_SHA256:
        raise ValueError("only the pinned first Mode B task is eligible")
    if not project.valid(task):
        raise ValueError("invalid first Mode B task")
    route = review_qwen_route(model="openai/local-qwen", base_url="http://qwen3:11434/v1")
    return {
        "task_id": task["id"],
        "task_sha256": MODEB_TASK_SHA256,
        "prompt": _prompt(task),
        "workspace": "/workspace/export",
        "allowed_files": sorted(openhands_multifile_review.EXPECTED_FILES),
        "allowed_tools": ["file_editor", "terminal"],
        "limits": {"cpu": 2, "ram_bytes": 4294967296, "pids": 128,
                   "scratch_bytes": 1006632960, "seconds": 600},
        "model": route["llm_options"],
        "auth_broker_required": True,
        "host_workspace_allowed": False,
        "external_network_allowed": False,
        "docker_socket_allowed": False,
        "execution_authorized": False,
        "release_authorized": False,
    }


def run_modeb_once(*, task, allow_agent=False, fixture_only=False,
                   fixture_adapter=None, cancelled=None, source_identity=None,
                   require_runtime_metadata=False):
    """Exercise the isolated-adapter contract using trusted injected fixtures.

    Never instantiates a real SDK, LocalWorkspace, process, or network client.
    Fixture receipts are not runtime evidence. Cancellation checks only
    surround the fixture call; real asynchronous cancellation and cgroup
    cleanup must be provided and admitted by a separate external supervisor.
    """
    def receipt(status, attempted=False):
        return dict(_result(status), fixture_adapter_attempted=attempted,
                    runtime_isolation_verified=False, real_sdk_imported=False,
                    qwen_connected=False)
    if (type(allow_agent) is not bool or type(fixture_only) is not bool
            or type(require_runtime_metadata) is not bool):
        raise ValueError("explicit boolean scope required")
    if not allow_agent:
        return receipt("disabled")
    if not fixture_only or fixture_adapter is None:
        return receipt("blocked_runtime_admission")
    request = prepare_modeb_request(task)
    request_digest = None
    if source_identity is not None:
        from . import checkpoint
        if (type(source_identity) is not dict
                or set(source_identity) != {"branch", "commit", "task_file_sha256"}
                or not source_identity["branch"] or not source_identity["commit"]
                or type(source_identity["task_file_sha256"]) is not str
                or not re.fullmatch(r"[0-9a-f]{64}", source_identity["task_file_sha256"])):
            raise ValueError("invalid fixture source binding")
        checkpoint._branch(source_identity["branch"])
        checkpoint._commit(source_identity["commit"])
        request["source_identity"] = dict(source_identity)
    metadata_request = None
    if require_runtime_metadata:
        if source_identity is None:
            raise ValueError("strict fixture metadata requires source binding")
        from . import runtime_contract
        metadata_request = {
            "schema": runtime_contract.REQ_SCHEMA,
            "task_id": request["task_id"],
            "task_sha256": request["task_sha256"],
            "classification": "synthetic",
            "required_capabilities": ["coding", "tool_calls"],
            "allowed_providers": ["local_qwen"],
            "allow_external_api": False,
            "max_tokens_total": 2048,
            "max_duration_seconds": request["limits"]["seconds"],
            "max_cost_usd": "0",
        }
        # Keep a separate expected copy outside the adapter's mutable request.
        request["runtime_metadata_request"] = dict(metadata_request,
            required_capabilities=list(metadata_request["required_capabilities"]),
            allowed_providers=list(metadata_request["allowed_providers"]))
    if source_identity is not None:
        request_digest = hashlib.sha256(project.encoded(request).encode("utf-8")).hexdigest()
    try:
        if cancelled is not None and cancelled():
            return receipt("fixture_cancelled_review_required")
    except Exception:
        return receipt("fixture_cancellation_unverified")
    if any(key in os.environ for key in UNSAFE_ENV_KEYS):
        return receipt("unsafe_environment")
    response = None
    failure = False
    cleanup = None
    try:
        response = fixture_adapter.execute(request)
    except Exception:
        failure = True
    finally:
        try:
            cleanup = fixture_adapter.close()
        except Exception:
            pass
    if type(cleanup) is not dict or set(cleanup) != {"fixture_cleanup"} or cleanup["fixture_cleanup"] is not True:
        return receipt("fixture_cleanup_unverified", True)
    try:
        if cancelled is not None and cancelled():
            return receipt("fixture_cancelled_review_required", True)
    except Exception:
        return receipt("fixture_cancellation_unverified", True)
    if failure:
        return receipt("fixture_failed_review_required", True)
    expected = {"status": "fixture_completed", "task_sha256": MODEB_TASK_SHA256}
    if request_digest is not None:
        expected["request_sha256"] = request_digest
    if require_runtime_metadata:
        if type(response) is not dict or set(response) != set(expected) | {"runtime_report_json"}:
            return receipt("fixture_receipt_rejected", True)
        if {k: response[k] for k in expected} != expected:
            return receipt("fixture_receipt_rejected", True)
        try:
            assessment = runtime_contract.assess_bound_local_json(
                metadata_request, response["runtime_report_json"], expected_model_id="local-qwen")
            # A fixture must explicitly attest only a blocked policy outcome.
            # No claim of model usage, artifact generation or successful run.
            if (assessment["status"] != "blocked" or assessment["error_code"] != "policy_denied"
                    or assessment["artifact_hash_recorded"] or assessment["input_tokens"] != 0
                    or assessment["output_tokens"] != 0 or assessment["duration_ms"] != 0):
                raise ValueError("fixture cannot claim runtime activity")
        except (ValueError, TypeError, KeyError, RecursionError):
            return receipt("fixture_receipt_rejected", True)
    elif type(response) is not dict or response != expected:
        return receipt("fixture_receipt_rejected", True)
    result = receipt("fixture_completed_review_required", True)
    if request_digest is not None:
        result["request_sha256"] = request_digest
    if require_runtime_metadata:
        result.update(runtime_metadata_validated=True, runtime_metadata_status="blocked")
    return result


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


def _run_once(*, task, candidate_root, output_root, workspace, model,
             base_url, allow_agent=False, sdk=None, defer_review=False):
    """Execute one SDK Conversation ONLY with explicit operator opt-in.

    SDK must already be installed/pinned, and the operator must have created,
    network-isolated, and supervised DockerWorkspace before calling this.
    """
    if type(allow_agent) is not bool:
        raise ValueError("explicit boolean operator approval required")
    if not allow_agent:
        return _result("disabled")
    if sdk is None:
        # #162: an opt-in flag is not an independent runtime admission receipt.
        return _result("blocked_runtime_admission")

    if not project.valid(task) or task.get("recipe") != "python-transform":
        raise ValueError("synthetic reviewed transform task required")
    llm_options = _fixture_llm_options(model, base_url)

    export, outputs = openhands_multifile_review._review_paths(candidate_root, output_root)
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
    agent_failed = cleanup_failed = False
    try:
        # Upstream SDK agent and tools are reused; there is NO custom agent
        # execution engine. Provider session and tools must be confined to
        # the operator's isolated container/network.
        llm = installed.LLM(**llm_options)
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
        agent_failed = True
    finally:
        if conversation is not None:
            try:
                conversation.close()
            except Exception:
                cleanup_failed = True
    if cleanup_failed:
        # Do not accept an export while SDK teardown remains uncertain.
        return _result("cleanup_unverified_review_required", attempted=True)
    if agent_failed:
        return _result("agent_failed_review_required", attempted=True)

    if defer_review:
        return _result("conversation_closed_pending_workspace_exit", attempted=True)
    return _review_closed(task, export, outputs)


def _review_closed(task, export, outputs):
    try:
        accepted = openhands_multifile_review.review(task, export, outputs)
    except (OSError, ValueError, TypeError, RuntimeError, SyntaxError,
            RecursionError, ArithmeticError, subprocess.TimeoutExpired):
        return _result("artifact_review_required", attempted=True)
    return {**accepted, "agent_session_attempted": True,
            "execution_authorized": False, "release_authorized": False,
            "automatic_retry_allowed": False}


def run_once(*, task, candidate_root, output_root, workspace, model,
             base_url, allow_agent=False, sdk=None):
    return _run_once(task=task, candidate_root=candidate_root,
                     output_root=output_root, workspace=workspace, model=model,
                     base_url=base_url, allow_agent=allow_agent, sdk=sdk)


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
    if sdk is None and not preflight_only:
        # No real SDK import or Docker startup until #162 is independently admitted.
        return _result("blocked_runtime_admission")
    if not project.valid(task) or task.get("recipe") != "python-transform":
        raise ValueError("synthetic-only reviewed transform required")
    # Metadata preflight accepts the same exact routes; no credentials are used.
    _fixture_llm_options(model, base_url)
    if not isinstance(server_image, str) or not PINNED_IMAGE.fullmatch(server_image):
        raise ValueError("pinned OpenHands image digest required")
    if (not isinstance(network, str) or not NETWORK.fullmatch(network)
            or network.lower() in FORBIDDEN_NETWORKS):
        raise ValueError("dedicated named Docker network required")

    export, outputs = openhands_multifile_review._review_paths(candidate_root, output_root)
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
            outcome = _run_once(
                task=task,
                candidate_root=export,
                output_root=output_root,
                workspace=workspace,
                model=model,
                base_url=base_url,
                allow_agent=True,
                sdk=installed,
                defer_review=True,
            )
        if outcome["status"] == "conversation_closed_pending_workspace_exit":
            return _review_closed(task, export, outputs)
        return outcome
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
