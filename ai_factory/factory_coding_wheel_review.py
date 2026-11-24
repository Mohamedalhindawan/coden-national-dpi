"""Static candidate wheel evidence, not installation or license admission."""
import base64
import hashlib
import json
import re
import sys
import tomllib
from email.parser import BytesParser
from pathlib import Path
from urllib.parse import urlsplit
from urllib.request import build_opener
from ai_factory.factory_wheel_notice_audit import CAP, NoRedirect, inspect_wheel

LOCK = "ed07829fc67bf0da94b493e9488e8798a9e067c200e8ccbdc1e2a1b8c35ebd1a"


def choose_wheel(wheels, rank):
    candidates = []
    for w in wheels:
        u = urlsplit(w["url"])
        if (u.scheme != "https" or u.netloc != "files.pythonhosted.org"
                or u.query or u.fragment or not u.path.endswith(".whl")
                or not re.fullmatch("sha256:[a-f0-9]{64}", w["hash"])
                or not 0 < w["size"]):
            raise ValueError("unapproved wheel locator or size")
        name = u.path.rsplit("/",1)[-1]
        priority = rank(name)
        if priority is not None:
            candidates.append((priority, name, w))
    if not candidates:
        raise ValueError("no compatible locked wheel")
    selected = min(candidates,key=lambda x:(x[0],x[1]))[2]
    if selected["size"] > CAP:
        raise ValueError("selected wheel exceeds size limit")
    return selected


def primary_metadata(entries):
    # The wheel's own metadata is at archive root. Vendored packages may
    # carry independent metadata and notices; preserve those as evidence.
    roots = [entry for path,entry in entries.items()
             if path.count("/") == 1 and path.endswith(".dist-info/METADATA")]
    if len(roots) != 1:
        raise ValueError("ambiguous root distribution metadata")
    return roots[0]


def metadata_fields(m):
    # Header objects from malformed/non-ASCII legacy metadata are not JSON-native.
    # The exact original metadata bytes and hash remain in evidence.
    return {"license":str(m["License"]) if m["License"] is not None else None,
            "license_expression":str(m["License-Expression"]) if m["License-Expression"] is not None else None,
            "license_classifiers":[str(s) for s in m.get_all("Classifier",[]) if str(s).startswith("License ::")],
            "license_files":[str(s) for s in m.get_all("License-File",[])]}


def summarize(records, expected):
    collected = [r for r in records if r["status"] == "collected"]
    missing = sorted(r["name"] for r in records if r["status"] != "collected")
    ok = len(records) == expected and len(collected) == expected and len({r["name"] for r in records}) == expected
    return {"status":"static_collection_complete" if ok else "collection_incomplete",
            "expected":expected,"collected":len(collected),"failed":missing,
            "without_notice":sorted(r["name"] for r in collected if not r["notice_count"]),
            "without_license_declaration":sorted(r["name"] for r in collected if not any(r.get(k) for k in ("license","license_expression","license_classifiers"))),
            "license_approved":False,"runtime_compatibility_verified":False,"installed":False,"release_authorized":False}


def main():
    # Use existing pip's packaging implementation for the host's exact tags.
    # No pip installation or execution of inspected wheel code.
    from pip._vendor.packaging.tags import sys_tags
    from pip._vendor.packaging.utils import parse_wheel_filename, canonicalize_name
    from pip._vendor.packaging.version import Version
    if sys.version_info[:2] != (3,13) or sys.platform != "linux":
        raise ValueError("wrong review interpreter")
    tags={tag:i for i,tag in enumerate(sys_tags())}
    raw=Path(sys.argv[1]).read_bytes()
    if hashlib.sha256(raw).hexdigest()!=LOCK:
        raise ValueError("candidate lock digest mismatch")
    packages=tomllib.loads(raw.decode())["package"]
    registry=[p for p in packages if p["source"]=={"registry":"https://pypi.org/simple"}]
    editable=[p for p in packages if "editable" in p["source"]]
    if len(packages)!=202 or len(registry)!=198 or len(editable)!=4:
        raise ValueError("unexpected graph")
    out=Path(sys.argv[2])
    out.mkdir(parents=True,exist_ok=True)
    records=[]
    for p in registry:
        name,version=p["name"],p["version"]
        rec={"name":name,"version":version,"status":"blocked"}
        try:
            def rank(filename):
                n,v,_,supported=parse_wheel_filename(filename)
                if n!=canonicalize_name(name) or v!=Version(version):
                    raise ValueError("wheel identity mismatch")
                return min((tags[t] for t in supported if t in tags),default=None)
            w=choose_wheel(p["wheels"],rank)
            with build_opener(NoRedirect()).open(w["url"],timeout=20) as response:
                raw=response.read(CAP+1)
            if len(raw)!=w["size"]:
                raise ValueError("wheel length mismatch")
            entries=inspect_wheel(raw,w["hash"][7:])
            m=BytesParser().parsebytes(base64.b64decode(primary_metadata(entries)["base64"]))
            if canonicalize_name(m["Name"])!=canonicalize_name(name) or Version(m["Version"])!=Version(version):
                raise ValueError("embedded metadata identity mismatch")
            notices={path:e for path,e in entries.items() if not path.endswith(".dist-info/METADATA")}
            candidate=dict(rec,status="collected",sha256=w["hash"][7:],url=w["url"],notice_count=len(notices),**metadata_fields(m))
            (out/(name+".json")).write_text(json.dumps({"record":candidate,"evidence":entries}))
            rec=candidate
        except Exception as exc:
            rec["status"]="blocked"
            rec["error_type"]=type(exc).__name__
            rec["error"]=str(exc)[:160]
        records.append(rec)
        print(name,version,rec["status"],flush=True)
    result=summarize(records,198)
    result.update(records=records,editable_source_records=[{"name":p["name"],"version":p["version"],"source":p["source"]} for p in editable],selection="one compatible wheel per registry record; not proof of actual installer selection")
    (out/"review.json").write_text(json.dumps(result,indent=2))
    print(result["status"],result["collected"],"/",result["expected"])
    if result["status"]!="static_collection_complete":
        raise SystemExit(1)


if __name__=="__main__":
    main()
