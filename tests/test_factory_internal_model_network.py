"""TDD: actual Docker internal network between synthetic agent and model endpoint.

A successful metadata fixture never authorizes OpenHands; only the real Docker
workflow checks end-to-end local HTTP and *denied* external IP/DNS egress.
"""
import copy
import json
from pathlib import Path
import unittest

from ai_factory import factory_internal_model_network_probe as probe
from ai_factory.factory_docker_isolation_probe import TEST_IMAGE

ROOT = Path(__file__).resolve().parents[1]
FLOW = ROOT / ".github/workflows/factory-p0-internal-model-network.yml"
DOC = ROOT / "docs/FACTORY_P0_PRIVATE_MODEL_NETWORK.md"
NAME = "coden-factory-ollama-55555-1"


def fixtures():
    ids = ("a" * 64, "b" * 64)
    network = {
        "Name": NAME, "Internal": True, "Driver": "bridge", "Scope": "local",
        "Containers": {
            ids[0]: {"Name": "coden-model-synthetic-55555-1"},
            ids[1]: {"Name": "coden-client-synthetic-55555-1"},
        },
    }
    def container(identifier):
        return {
            "Id": identifier,
            "Image": "sha256:" + "d" * 64,
            "State": {"Running": True},
            "Config": {"Image": TEST_IMAGE, "User": "65534:65534",
                       "Env": ["PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"]},
            "HostConfig": {
                "NanoCpus": 1_000_000_000, "Memory": 268435456,
                "MemorySwap": 268435456, "PidsLimit": 64,
                "CapDrop": ["ALL"], "CapAdd": [], "Privileged": False,
                "ReadonlyRootfs": True, "NetworkMode": NAME,
                "PidMode": "", "IpcMode": "private",
                "SecurityOpt": ["no-new-privileges"],
                "Binds": None, "Devices": [], "PortBindings": {},
                "Tmpfs": {"/tmp": "rw,noexec,nosuid,nodev,size=16m,mode=1777"},
                "AutoRemove": True, "RestartPolicy": {"Name": "no"},
            },
            "Mounts": [],
            "NetworkSettings": {
                "Networks": {NAME: {"NetworkID": "f" * 64}},
                "Ports": {},
            },
        }
    return network, container(ids[0]), container(ids[1])


class InternalModelNetworkTests(unittest.TestCase):
    def test_exact_two_constrained_containers_on_internal_private_network(self):
        network, client, server = fixtures()
        result = probe.inspect_pair(network, client, server)
        self.assertEqual(result["policy_state"], "SYNTHETIC_INTERNAL_NETWORK_METADATA_PASS")
        self.assertEqual(result["scope"], "TWO_SYNTHETIC_BUSYBOX_CONTAINERS_ONLY")
        self.assertTrue(result["docker_network_internal"])
        self.assertTrue(result["same_isolated_network"])
        self.assertTrue(result["no_host_port_publications"])
        self.assertTrue(result["both_containers_resource_capped"])
        self.assertEqual(result["container_count"], 2)
        self.assertEqual(result["image"], TEST_IMAGE)
        self.assertFalse(result["real_model_invoked"])
        self.assertFalse(result["rootless_docker_host_verified"])
        self.assertFalse(result["actual_egress_proved_by_metadata_alone"])
        self.assertFalse(result["openhands_live_execution_authorized"])
        self.assertFalse(result["factory_production_authorized"])
        self.assertFalse(result["release_authorized"])
        self.assertEqual(result["paid_calls"], 0)

    def test_network_mutations_fail_closed(self):
        mutations = [
            ("Internal", False), ("Driver", "overlay"), ("Scope", "swarm"),
            ("Name", "bridge"), ("Containers", {}),
        ]
        for k, v in mutations:
            with self.subTest(field=k):
                network, client, server = fixtures()
                network[k] = v
                with self.assertRaises(ValueError):
                    probe.inspect_pair(network, client, server)
        network, client, server = fixtures()
        network["Containers"]["c" * 64] = {"Name": "unapproved-service"}
        with self.assertRaises(ValueError):
            probe.inspect_pair(network, client, server)

    def test_container_mutations_fail_closed(self):
        mutations = [
            (("Config", "Image"), "busybox:latest"),
            (("Config", "User"), "0:0"),
            (("Config", "Env"), ["PATH=/bin", "OPENAI_API_KEY=not-a-secret"]),
            (("HostConfig", "NetworkMode"), "bridge"),
            (("HostConfig", "NanoCpus"), 0),
            (("HostConfig", "Memory"), 0),
            (("HostConfig", "MemorySwap"), -1),
            (("HostConfig", "PidsLimit"), 0),
            (("HostConfig", "CapDrop"), []),
            (("HostConfig", "CapAdd"), ["NET_ADMIN"]),
            (("HostConfig", "Privileged"), True),
            (("HostConfig", "ReadonlyRootfs"), False),
            (("HostConfig", "SecurityOpt"), []),
            (("HostConfig", "Binds"), ["/var/run/docker.sock:/var/run/docker.sock"]),
            (("HostConfig", "PortBindings"), {"11434/tcp": [{"HostPort": "11434"}]}),
            (("HostConfig", "AutoRemove"), False),
            (("HostConfig", "RestartPolicy"), {"Name": "always"}),
            (("HostConfig", "Tmpfs"), {}),
            (("NetworkSettings", "Ports"), {"11434/tcp": [{"HostPort": "11434"}]}),
            (("NetworkSettings", "Networks"), {"bridge": {}}),
            (("Mounts",), [{"Type": "bind", "Source": "/etc", "Destination": "/etc"}]),
            (("State", "Running"), False),
        ]
        for role in (1, 2):
            for path, value in mutations:
                with self.subTest(role=role, path=path):
                    parts = list(fixtures())
                    target = parts[role]
                    for k in path[:-1]:
                        target = target[k]
                    target[path[-1]] = value
                    with self.assertRaises(ValueError):
                        probe.inspect_pair(*parts)

    def test_network_with_same_id_or_cross_network_rejected(self):
        net, client, server = fixtures()
        server["Id"] = client["Id"]
        with self.assertRaises(ValueError):
            probe.inspect_pair(net, client, server)
        net, client, server = fixtures()
        server["NetworkSettings"]["Networks"][NAME]["NetworkID"] = "e" * 64
        with self.assertRaises(ValueError):
            probe.inspect_pair(net, client, server)

    def test_ci_requires_actual_private_http_positive_and_public_egress_negative(self):
        flow = FLOW.read_text(encoding="utf-8")
        for term in (
            TEST_IMAGE,
            "docker network create --internal --driver bridge",
            "docker network inspect",
            "docker exec",
            "http://ollama:11434/health",
            "CODEN_SYNTHETIC_MODEL_ENDPOINT_ONLY",
            "http://1.1.1.1/",
            "http://example.com/",
            "expected external IP egress DENIED",
            "expected external DNS egress DENIED",
            "--cpus=1", "--memory=256m", "--pids-limit=64",
            "--cap-drop=ALL", "--read-only", "--security-opt=no-new-privileges",
            "--user=65534:65534", "--tmpfs=/tmp:",
            "factory_internal_model_network_probe",
            "trap cleanup EXIT", "docker network rm", "docker rm -f",
            "pull_request", "contents: read", "persist-credentials: false",
            "rootless_docker_host_verified", "openhands_live_execution_authorized",
        ):
            self.assertIn(term, flow)
        self.assertNotIn("--network=host", flow)
        self.assertNotIn("pull_request_target:", flow)
        self.assertNotIn("continue-on-error: true", flow)

    def test_docs_have_explicit_scope_and_limitations(self):
        text = DOC.read_text(encoding="utf-8")
        for marker in ("v1.0", "#162", "#173", "rootless", "OpenHands",
                       "SBOM", "Ollama", "Human review", "mock", "not"):
            self.assertIn(marker, text)
        self.assertIn(TEST_IMAGE, text)


if __name__ == "__main__":
    unittest.main()
