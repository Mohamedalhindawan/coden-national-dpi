"""TDD contract for REAL pinned Docker resource-boundary smoke evidence.

Mock inspect objects prove only rejection logic; actual enforcement is proven
separately by the dedicated CI job inspecting/running a real Docker container.
OpenHands SDK and production permission MUST remain BLOCKED.
"""
import copy
import json
from pathlib import Path
import unittest

from ai_factory import factory_docker_isolation_probe as probe

ROOT = Path(__file__).resolve().parents[1]
FLOW = ROOT / ".github/workflows/factory-p0-real-docker-boundary.yml"
DOC = ROOT / "docs/FACTORY_P0_REAL_DOCKER_ISOLATION_BOUNDARY.md"


def _fixture():
    return {
        "Id": "c" * 64,
        "Image": "sha256:" + "a" * 64,
        "State": {"Running": True},
        "Config": {
            "Image": probe.TEST_IMAGE,
            "User": "65534:65534",
            "Env": ["PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"],
        },
        "HostConfig": {
            "NanoCpus": 1_000_000_000,
            "Memory": 268435456,
            "MemorySwap": 268435456,
            "PidsLimit": 64,
            "CapDrop": ["ALL"],
            "CapAdd": [],
            "Privileged": False,
            "ReadonlyRootfs": True,
            "NetworkMode": "none",
            "PidMode": "private",
            "IpcMode": "private",
            "SecurityOpt": ["no-new-privileges"],
            "Binds": None,
            "Devices": [],
            "Tmpfs": {"/tmp": "rw,noexec,nosuid,nodev,size=16m,mode=1777"},
            "AutoRemove": True,
            "RestartPolicy": {"Name": "no"},
        },
        "Mounts": [],
    }


class RealDockerSafetyBoundaryTests(unittest.TestCase):
    def test_verified_fixed_inspect_returns_only_limited_pilot_receipt(self):
        x = probe.inspect_config(_fixture())
        self.assertEqual(x["policy_state"], "CONSTRAINED_FIXTURE_METADATA_PASS")
        self.assertTrue(x["cpu_limit_configured"])
        self.assertTrue(x["memory_limit_configured"])
        self.assertTrue(x["pids_limit_configured"])
        self.assertTrue(x["all_capabilities_dropped"])
        self.assertTrue(x["nonroot_container_user"])
        self.assertTrue(x["read_only_rootfs"])
        self.assertTrue(x["network_disabled"])
        self.assertTrue(x["no_privileged_mounts"])
        self.assertEqual(x["image"], probe.TEST_IMAGE)
        self.assertEqual(x["scope"], "SYNTHETIC_BUSYBOX_FIXTURE_ONLY")
        self.assertEqual(x["openhands_runtime_state"], "BLOCKED_FOR_REAL_SESSION")
        self.assertIs(x["openhands_live_execution_authorized"], False)
        self.assertIs(x["factory_production_authorized"], False)
        self.assertIs(x["release_authorized"], False)
        self.assertEqual(x["paid_calls"], 0)

    def test_tampering_never_creates_execution_permission(self):
        changes = [
            (("State", "Running"), False),
            (("Config", "Image"), "busybox:latest"),
            (("Config", "User"), "root"),
            (("Config", "Env"), ["PATH=/bin", "OPENAI_API_KEY=secret"]),
            (("HostConfig", "NanoCpus"), 0),
            (("HostConfig", "Memory"), 0),
            (("HostConfig", "MemorySwap"), -1),
            (("HostConfig", "PidsLimit"), -1),
            (("HostConfig", "CapDrop"), None),
            (("HostConfig", "CapAdd"), ["SYS_ADMIN"]),
            (("HostConfig", "Privileged"), True),
            (("HostConfig", "ReadonlyRootfs"), False),
            (("HostConfig", "NetworkMode"), "bridge"),
            (("HostConfig", "PidMode"), "host"),
            (("HostConfig", "IpcMode"), "host"),
            (("HostConfig", "SecurityOpt"), []),
            (("HostConfig", "Binds"), ["/var/run/docker.sock:/var/run/docker.sock"]),
            (("HostConfig", "Devices"), ["/dev/kvm"]),
            (("HostConfig", "Tmpfs"), {}),
            (("HostConfig", "AutoRemove"), False),
            (("HostConfig", "RestartPolicy"), {"Name": "always"}),
            (("Mounts",), [{"Type": "bind", "Source": "/etc", "Destination": "/etc"}]),
        ]
        for path, value in changes:
            with self.subTest(path=path):
                inspect = copy.deepcopy(_fixture())
                target = inspect
                for segment in path[:-1]:
                    target = target[segment]
                target[path[-1]] = value
                with self.assertRaises(ValueError):
                    probe.inspect_config(inspect)

    def test_rejects_malformed_or_unknown_docker_inspect(self):
        for x in (None, [], {}, {"HostConfig":{}}, "docker ok"):
            with self.subTest(type=type(x).__name__), self.assertRaises(ValueError):
                probe.inspect_config(x)

    def test_runner_steps_use_exact_pinned_image_and_prove_negative_cases(self):
        content = FLOW.read_text(encoding="utf-8")
        for marker in (
            probe.TEST_IMAGE,
            "--cpus=1",
            "--memory=256m",
            "--memory-swap=256m",
            "--pids-limit=64",
            "--cap-drop=ALL",
            "--security-opt=no-new-privileges",
            "--read-only",
            "--network=none",
            "--user=65534:65534",
            "--tmpfs=/tmp:rw,noexec,nosuid,nodev,size=16m,mode=1777",
            "docker inspect",
            "docker exec",
            "pids.max",
            "memory.max",
            "cpu.max",
            "CapEff",
            "NoNewPrivs",
            "expected rootfs write rejection",
            "python -m ai_factory.factory_docker_isolation_probe",
            "contents: read",
            "persist-credentials: false",
            "release_authorized",
        ):
            self.assertIn(marker, content)
        self.assertNotIn("pull_request_target:", content)
        self.assertNotIn("--privileged", content)
        self.assertNotIn("--network=host", content)
        self.assertNotIn("continue-on-error: true", content)

    def test_workflow_limits_first_party_draft_scope_and_cleanup(self):
        x = FLOW.read_text(encoding="utf-8")
        self.assertIn("feat/factory-p0-real-docker-resource-boundary-20261124", x)
        self.assertIn("github.event.pull_request.head.repo.full_name == github.repository", x)
        self.assertIn("timeout-minutes: 8", x)
        self.assertIn("trap cleanup EXIT", x)
        self.assertIn("docker rm -f", x)
        self.assertIn("docker pull", x)
        self.assertIn("rootless_daemon_verified", x)

    def test_document_only_claims_a_bounded_fixture_not_openhands(self):
        doc = DOC.read_text(encoding="utf-8")
        for term in ("#162", "v1.0", "Docker", "real", "rootless", "SBOM", "not", "Human review"):
            self.assertIn(term, doc)
        self.assertIn(probe.TEST_IMAGE, doc)


if __name__ == "__main__":
    unittest.main()
