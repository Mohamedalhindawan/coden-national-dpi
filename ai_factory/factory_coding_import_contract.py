"""Legacy import entrypoint blocked pending independent R2 admission.

Pure absence checks remain available for synthetic tests; this CLI cannot
perform module discovery or imports, create an agent or authorize a release.
"""
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
    # The legacy command has no independent admission mechanism. Do not
    # discover or import installed candidate modules from this entrypoint.
    # Keep the pure absence checker available for synthetic review only.
    result = {"status": "BLOCKED",
              "errors": ["independent_r2_admission_required"],
              "imported": [], "runtime_admitted": False,
              "sdk_conversation_ran": False, "release_authorized": False}
    print(json.dumps(result, indent=2))
    return 1


if __name__=="__main__":
    sys.exit(main())
