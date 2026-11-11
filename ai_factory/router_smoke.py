"""Offline smoke check for CODEN's optional local Codex CLI model router.

Usage: python -m ai_factory.router_smoke
No network requests, secrets, or service startup.
"""
import json
import os
import sys
from .router_preflight import check_router_config


def smoke_check(env):
    config = {
        'base_url': env.get('CODEN_ROUTER_BASE_URL', 'http://127.0.0.1:3001/v1'),
        'api_style': env.get('CODEN_ROUTER_API_STYLE', 'responses'),
        'model': env.get('CODEN_ROUTER_MODEL', ''),
    }
    return check_router_config(config)


def main():
    result = smoke_check(os.environ)
    print(json.dumps({'configuration_ready': result['ready'], 'errors': result['errors']}, ensure_ascii=False))
    return 0 if result['ready'] else 1


if __name__ == '__main__':
    sys.exit(main())
