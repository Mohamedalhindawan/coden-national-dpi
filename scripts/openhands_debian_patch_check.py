"""Evaluate signed APT candidates against #176's immutable minimal-image report."""
import hashlib
import json
from pathlib import Path
import subprocess
import zipfile

BASELINE = Path("docs/evidence/openhands-077f3fad/minimal-image-review.zip")
ARCHIVE_SHA256 = "6b773af239eb96921e17e329ce99a3c33e1dcd35a8afe9eef2570156b7d8c843"


def run(*args):
    return subprocess.check_output(args, text=True)


def main():
    if hashlib.sha256(BASELINE.read_bytes()).hexdigest() != ARCHIVE_SHA256:
        raise ValueError("baseline digest mismatch")
    with zipfile.ZipFile(BASELINE) as archive:
        report = json.loads(archive.read("vulnerabilities.json"))
    records = [
        item for result in report["Results"] if result.get("Class") == "os-pkgs"
        for item in result.get("Vulnerabilities", []) if item["Severity"] == "HIGH"
    ]
    if len(records) != 124:
        raise ValueError("unexpected baseline population")
    candidates = {}
    for name in sorted({item["PkgName"] for item in records}):
        policy = run("apt-cache", "policy", name)
        version = next(line.split()[1] for line in policy.splitlines()
                       if line.strip().startswith("Candidate:"))
        candidates[name] = version
    packages = {}
    findings = []
    for item in records:
        name = item["PkgName"]
        candidate = candidates[name]
        fixed = item.get("FixedVersion")
        status = "no_fix_in_baseline"
        if fixed:
            status = "candidate_below_fix"
            if candidate != "(none)" and subprocess.run(
                ["dpkg", "--compare-versions", candidate, "ge", fixed], check=False
            ).returncode == 0:
                status = "candidate_meets_fix"
                packages[name] = candidate
        findings.append(dict(package=name, advisory=item["VulnerabilityID"],
                             installed=item["InstalledVersion"], candidate=candidate,
                             fixed=fixed, status=status))
    requests = [f"{name}={version}" for name, version in sorted(packages.items())]
    if requests:
        simulation = run("apt-get", "--simulate", "--no-remove", "install", *requests)
        Path("solver.txt").write_text(simulation)
        subprocess.run(["apt-get", "--download-only", "--no-remove", "-y",
                        "install", *requests], check=True)
    archives = {}
    for package in sorted(Path("apt-review/cache/archives").glob("*.deb")):
        name = run("dpkg-deb", "-f", str(package), "Package").strip()
        version = run("dpkg-deb", "-f", str(package), "Version").strip()
        archives[name] = dict(version=version, sha256=hashlib.sha256(package.read_bytes()).hexdigest())
    for name, version in packages.items():
        if archives.get(name, {}).get("version") != version:
            raise ValueError(f"missing verified download for {name}")
    Path("patch-review.json").write_text(json.dumps(dict(
        baseline_sha256=ARCHIVE_SHA256, findings=findings, downloads=archives,
        image_patched=False, live_execution_authorized=False), indent=2) + "\n")
    print("Observed signed candidate coverage:", len(packages), "packages;",
          sum(f["status"] == "candidate_meets_fix" for f in findings), "baseline records")


if __name__ == "__main__":
    main()
