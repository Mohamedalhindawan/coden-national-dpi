"""Candidate import contract. Never import excluded modules to check absence.

Run only in an approved isolated, synthetic runtime. No agent session is created.
"""
import importlib
from importlib import metadata, util
import json
import re
import sys

BANNED = {"browser-use":"browser_use", "browser-use-sdk":"browser_use_sdk",
          "func-timeout":"func_timeout", "lmnr":"lmnr",
          "lmnr-claude-code-proxy":"lmnr_claude_code_proxy"}
CODING = ("openhands.tools.terminal", "openhands.tools.file_editor",
          "openhands.tools.task_tracker")


def check_absence(distributions, lookup):
    names={re.sub(r"[-_.]+","-",name).lower() for name in distributions}
    errors=[]
    for dist,module in BANNED.items():
        if dist in names:
            errors.append("distribution:"+dist)
        try:
            if lookup(module) is not None:
                errors.append("module:"+module)
        except Exception:
            errors.append("discovery_failed:"+module)
    return sorted(errors)


def current_absence():
    return check_absence(
        [dist.metadata["Name"] for dist in metadata.distributions()],
        util.find_spec)


def main():
    errors=current_absence()
    imported=[]
    if not errors:
        for name in CODING:
            try:
                mod=importlib.import_module(name)
                imported.append({"module":name,"origin":str(mod.__file__)})
            except Exception as exc:
                errors.append("coding_import:"+name+":"+type(exc).__name__)
        errors.extend(current_absence())
        for name in sys.modules:
            if name.split(".")[0] in BANNED.values():
                errors.append("loaded:"+name)
    result={"status":"OVERLAY_IMPORT_CONTRACT_RED" if errors else "OVERLAY_IMPORT_CONTRACT_GREEN",
            "errors":sorted(set(errors)), "imported":imported,
            "runtime_admitted":False,"sdk_conversation_ran":False,"release_authorized":False}
    print(json.dumps(result,indent=2))
    return 1 if errors else 0


if __name__=="__main__":
    sys.exit(main())
