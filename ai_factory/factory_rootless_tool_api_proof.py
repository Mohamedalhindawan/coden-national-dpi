"""Read-only admission of one *operator-authored* real OpenHands tool API trial.

This module verifies only sanitized flags supplied after actual Rootless CI
commands pass. A green receipt never means that an LLM invoked a tool, that
the official SDK Conversation ran or that deployment is authorized.
"""
import argparse
import json
from pathlib import Path
import os
import stat

OPENHANDS_SHA="5ad5fa2bb86256b510df3bfbbd9653fbc60a243ea744a579d3ca4c6fd9e91cf3"
QWEN_SHA="1d9614638d18024d0fbb36575a15f1302a3adf044df10345688ec4f6e1c4ff32"
SOURCE="077f3fad6d31cd852be5c87176e0a93c3b446126"
TRUE=(
    "rootless_cgroup_and_network_pass",
    "signed_source_build_verified",
    "strict_temporary_workspace_caps_verified",
    "real_model_link_verified",
    "no_key_post_denied",
    "wrong_key_post_denied",
    "correct_key_post_succeeded",
    "real_tool_exit_zero",
    "exact_synthetic_stdout_verified",
    "auth_key_never_forwarded_to_qwen",
    "actual_api_bash_command_ran",
)
FALSE=(
    "model_generated_this_command",
    "openhands_sdk_conversation_ran",
    "independent_three_file_acceptance_passed",
    "production_authorized",
    "release_authorized",
    "automatic_merge",
)
KEYS=frozenset(TRUE+FALSE+(
    "plan_version","source_commit","openhands_binary_sha256",
    "qwen_gguf_sha256","paid_calls"
))


def verify(receipt):
    if type(receipt) is not dict or set(receipt)!=KEYS:
        raise ValueError("incomplete/bogus OpenHands tool evidence")
    if (
        receipt["plan_version"]!="v1.0"
        or receipt["source_commit"]!=SOURCE
        or receipt["openhands_binary_sha256"]!=OPENHANDS_SHA
        or receipt["qwen_gguf_sha256"]!=QWEN_SHA
        or any(receipt[k] is not True for k in TRUE)
        or any(receipt[k] is not False for k in FALSE)
        or type(receipt["paid_calls"]) is not int
        or receipt["paid_calls"]!=0
    ):
        raise ValueError("unverified tool sandbox proof or forbidden authorization")
    return {**receipt,"stage":"REAL_AUTHENTICATED_OPERATOR_TOOL_API_ONLY"}


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--input",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    a=p.parse_args(argv)
    try:
        src=a.input
        if src.is_symlink() or not hasattr(os,"O_NOFOLLOW"):
            raise ValueError("unsafe input")
        fd=os.open(src,os.O_RDONLY|os.O_NOFOLLOW)
        try:
            st=os.fstat(fd)
            if not stat.S_ISREG(st.st_mode) or not 0<st.st_size<=8192:
                raise ValueError("unsafe evidence size")
            with os.fdopen(os.dup(fd),"rb") as f:
                raw=f.read(8193)
            if len(raw)!=st.st_size:
                raise ValueError("racing evidence")
        finally:
            os.close(fd)
        report=verify(json.loads(raw.decode("utf-8")))
        out=a.output
        if not out.is_absolute() or out.is_symlink() or out.exists() or not out.parent.is_dir():
            raise ValueError("unsafe output path")
        with out.open("x",encoding="utf-8") as f:
            json.dump(report,f,indent=2,sort_keys=True)
            f.write("\n")
    except (OSError,ValueError,TypeError,UnicodeError,json.JSONDecodeError):
        p.exit(2,"Rootless real OpenHands tool API BLOCKED\n")
    print(json.dumps({"stage":report["stage"],"release_authorized":False},sort_keys=True))
    return 0


if __name__=="__main__":
    raise SystemExit(main())
