"""TDD: authentic local Qwen inference over an isolated OCI internal network.

Metadata and synthetic receipt tests are necessary but not sufficient:
real Docker + llama.cpp server + GGUF SHA + HTTP completion must run in CI.
"""
import copy
from pathlib import Path
import unittest

from ai_factory import factory_real_qwen_server_admission as adm

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github/workflows/factory-p0-real-qwen-private-server.yml"
DOCKERFILE = ROOT / ".github/docker/Factory-Qwen-CPU.Dockerfile"
DOC = ROOT / "docs/FACTORY_REAL_QWEN_PRIVATE_SERVER_EVIDENCE.md"


def _fixture():
    name = "coden-factory-real-qwen-22222-1"
    net_id = "9" * 64
    client_id = "a" * 64
    server_id = "b" * 64
    network = {
        "Name": name, "Id": net_id, "Internal": True,
        "Driver": "bridge", "Scope": "local",
        "Containers": {
            client_id: {"Name": "coden-qwen-client-22222-1"},
            server_id: {"Name": "coden-qwen-server-22222-1"},
        },
    }
    def base(cid, image, cpus, memory):
        return {
            "Id": cid, "Image": "sha256:" + "1"*64,
            "State": {"Running": True},
            "Config": {
                "Image": image,
                "User": "65534:65534",
                "Env": ["PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"],
                "Labels": {},
            },
            "HostConfig": {
                "NanoCpus": cpus*1_000_000_000, "Memory": memory,
                "MemorySwap": memory, "PidsLimit": 64,
                "CapDrop": ["ALL"], "CapAdd": [],
                "Privileged": False, "ReadonlyRootfs": True,
                "NetworkMode": name, "PidMode": "", "IpcMode": "private",
                "SecurityOpt": ["no-new-privileges"],
                "Binds": None, "Devices": [],
                "PortBindings": {}, "AutoRemove": True,
                "RestartPolicy": {"Name": "no"},
                "Tmpfs": {"/tmp": "rw,noexec,nosuid,nodev,size=16m,mode=1777"},
            },
            "Mounts": [],
            "NetworkSettings": {
                "Networks": {name: {"NetworkID": net_id}},
                "Ports": {},
            },
        }
    client = base(client_id, adm.CLIENT_IMAGE, 1, 268435456)
    server = base(server_id, "coden-qwen-private:22222-1", 2, 1610612736)
    server["Config"]["Env"].append("LD_LIBRARY_PATH=/opt/llama:/opt/runtime-libs")
    server["Config"]["Labels"] = {
        "org.coden.llama_archive_sha256": adm.LLAMA_SHA,
        "org.coden.qwen_weights_sha256": adm.MODEL_SHA,
        "org.coden.ubuntu_base": adm.UBUNTU_BASE,
        "org.coden.pilot_scope": "read-only-synthetic-internal-llama-server",
        "org.coden.libgomp_archive_sha256": adm.LIBGOMP_SHA,
        "org.coden.libcurl_archive_sha256": adm.LIBCURL_SHA,
        "org.coden.libstdcxx_archive_sha256": adm.LIBSTDCXX_SHA,
    }
    server["HostConfig"]["Tmpfs"] = {
        "/tmp": "rw,noexec,nosuid,nodev,size=32m,mode=1777"
    }
    return network, client, server


class RealQwenPrivateServerAdmissionTests(unittest.TestCase):
    def test_metadata_approval_is_limited_pilot_not_openhands(self):
        result = adm.audit_pair(*_fixture())
        self.assertEqual(result["state"], "REAL_QWEN_PRIVATE_NETWORK_INSPECT_PASS")
        self.assertEqual(result["scope"], "SYNTHETIC_LLAMA_CPP_QWEN_SERVER_ONLY")
        self.assertEqual(result["model_sha256"], adm.MODEL_SHA)
        self.assertEqual(result["runtime_archive_sha256"], adm.LLAMA_SHA)
        self.assertTrue(result["two_resource_capped_containers"])
        self.assertTrue(result["network_internal"])
        self.assertTrue(result["no_published_ports"])
        self.assertFalse(result["model_inference_proven_by_inspect"])
        self.assertFalse(result["rootless_daemon_verified"])
        self.assertFalse(result["openhands_live_execution_authorized"])
        self.assertFalse(result["release_authorized"])
        self.assertEqual(result["paid_calls"], 0)

    def test_detects_no_privilege_increase_or_model_swap(self):
        cases = [
            (1, ("Config", "Image"), "busybox:latest"),
            (1, ("HostConfig", "NetworkMode"), "bridge"),
            (1, ("HostConfig", "Memory"), 0),
            (2, ("Config", "User"), "0:0"),
            (2, ("Config", "Env"), ["PATH=/bin", "OPENAI_API_KEY=stolen"]),
            (2, ("Config", "Labels", "org.coden.qwen_weights_sha256"), "bad"),
            (2, ("Config", "Labels", "org.coden.ubuntu_base"), "ubuntu:latest"),
            (2, ("HostConfig", "NanoCpus"), 0),
            (2, ("HostConfig", "Memory"), 0),
            (2, ("HostConfig", "MemorySwap"), -1),
            (2, ("HostConfig", "PidsLimit"), -1),
            (2, ("HostConfig", "CapDrop"), []),
            (2, ("HostConfig", "CapAdd"), ["NET_ADMIN"]),
            (2, ("HostConfig", "Privileged"), True),
            (2, ("HostConfig", "ReadonlyRootfs"), False),
            (2, ("HostConfig", "NetworkMode"), "host"),
            (2, ("HostConfig", "SecurityOpt"), []),
            (2, ("HostConfig", "Binds"), ["/var/run/docker.sock:/var/run/docker.sock"]),
            (2, ("HostConfig", "PortBindings"), {"11434/tcp": [{"HostPort": "11434"}]}),
            (2, ("HostConfig", "RestartPolicy"), {"Name": "always"}),
            (2, ("NetworkSettings", "Networks"), {"bridge": {}}),
            (2, ("NetworkSettings", "Ports"), {"11434/tcp": [{"HostPort": "11434"}]}),
        ]
        for i, path, value in cases:
            with self.subTest(i=i, path=path):
                args = copy.deepcopy(_fixture())
                data = args[i]
                for k in path[:-1]:
                    data = data[k]
                data[path[-1]] = value
                with self.assertRaises(ValueError):
                    adm.audit_pair(*args)

    def test_wrong_network_or_extra_container_rejected(self):
        net, client, server = _fixture()
        net["Internal"] = False
        with self.assertRaises(ValueError):
            adm.audit_pair(net, client, server)
        net, client, server = _fixture()
        net["Containers"]["c"*64] = {"Name": "unapproved-agent"}
        with self.assertRaises(ValueError):
            adm.audit_pair(net, client, server)
        net, client, server = _fixture()
        server["NetworkSettings"]["Networks"][net["Name"]]["NetworkID"] = "a"*64
        with self.assertRaises(ValueError):
            adm.audit_pair(net, client, server)

    def test_completion_result_verification_does_not_claim_more_than_one_model_call(self):
        receipt = adm.audit_completion({
            "content": "Hi CODEN Factory",
            "tokens_predicted": 7,
            "timings": {"predicted_n": 7},
            "stop": True,
        })
        self.assertEqual(receipt["state"], "LLAMA_SERVER_COMPLETION_SHAPE_PASS")
        self.assertEqual(receipt["tokens_predicted"], 7)
        self.assertEqual(len(receipt["response_sha256"]), 64)
        self.assertFalse(receipt["openhands_live_execution_authorized"])
        self.assertFalse(receipt["release_authorized"])
        for invalid in (
            {}, {"content": "", "tokens_predicted": 7},
            {"content": "mock", "tokens_predicted": 0},
            {"content": "ok", "tokens_predicted": True},
            {"content": "ok", "tokens_predicted": 999},
            {"content": "ok", "tokens_predicted": 7, "timings": {"predicted_n": 8}},
        ):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                adm.audit_completion(invalid)

    def test_dockerfile_build_is_pinned_and_nonroot(self):
        d = DOCKERFILE.read_text(encoding="utf-8")
        for s in (
            adm.UBUNTU_BASE, adm.MODEL_SHA, adm.LLAMA_SHA,
            adm.LIBGOMP_SHA, adm.LIBCURL_SHA, adm.LIBSTDCXX_SHA,
            "USER 65534:65534", "LD_LIBRARY_PATH=/opt/llama",
            "COPY --chown=65534:65534", "ENTRYPOINT",
            "llama-server",
        ):
            self.assertIn(s, d)
        self.assertNotIn("apt-get", d)
        self.assertNotIn("curl ", d)
        self.assertNotIn("latest", d)

    def test_real_model_and_external_egress_are_exercised_in_ci(self):
        flow = WORKFLOW.read_text(encoding="utf-8")
        for word in (
            adm.MODEL_SHA, adm.LLAMA_SHA, adm.UBUNTU_BASE,
            adm.LIBGOMP_SHA, adm.LIBCURL_SHA, adm.LIBSTDCXX_SHA,
            adm.CLIENT_IMAGE, "sha256sum --check",
            "llama-b12600-bin-ubuntu-x64.tar.gz",
            "qwen2.5-coder-0.5b-instruct-q4_k_m.gguf",
            "docker network create --internal",
            "docker build", "docker inspect", "docker exec",
            "dpkg-deb -x", "--entrypoint=/usr/bin/ldd", "docker logs",
            "http://ollama:11434/health", "http://ollama:11434/completion",
            "tokens_predicted", "actual_real_qwen_completion_verified",
            "http://1.1.1.1/", "http://example.com/",
            "--cap-drop=ALL", "--read-only", "--pids-limit=64",
            "--memory=1536m", "--network-alias ollama",
            "factory_real_qwen_server_admission",
            "contents: read", "persist-credentials: false",
            "trap cleanup EXIT", "rootless_daemon_verified",
            "openhands_live_execution_authorized",
        ):
            self.assertIn(word, flow)
        for forbidden in ("pull_request_target:", "--privileged", "--network=host", "continue-on-error: true"):
            self.assertNotIn(forbidden, flow)

    def test_doc_blocks_sdk_and_production_inference(self):
        d = DOC.read_text(encoding="utf-8")
        for term in ("v1.0", "#162", "#174", "OpenHands", "rootless", "SBOM",
                     "Qwen", "llama.cpp", "Human review", "NOT"):
            self.assertIn(term, d)


if __name__ == "__main__":
    unittest.main()
