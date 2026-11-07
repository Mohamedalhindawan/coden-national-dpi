"""Deterministic adapter that produces receipts without running external tools."""
class DryRunAdapter:
    def execute(self, context):
        return {
            "status": "simulated",
            "executed": False,
            "output": {
                "message": "No command, model, network request, or external tool was executed.",
                "payload_sha256": context["payload_sha256"],
            },
        }
