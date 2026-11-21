"""Offline-only validation of a local Codex CLI router experiment.

This module never connects to a model, handles credentials, or starts a service.
"""
from urllib.parse import urlsplit


def check_router_config(config):
    errors = []
    if not isinstance(config, dict):
        return {'ready': False, 'errors': ['configuration must be an object']}
    if set(config) - {'base_url', 'api_style', 'model'}:
        errors.append('unsupported configuration field (do not provide credentials)')
    url = config.get('base_url')
    if not isinstance(url, str):
        errors.append('base_url must be a local HTTP URL')
    else:
        try:
            parsed = urlsplit(url)
            if (parsed.scheme != 'http' or parsed.hostname not in {'127.0.0.1', 'localhost', '::1'}
                    or parsed.username is not None or parsed.password is not None
                    or parsed.query or parsed.fragment or parsed.path.rstrip('/') != '/v1'
                    or parsed.port is None):
                errors.append('base_url must use local HTTP, explicit port and /v1 path without credentials')
        except ValueError:
            errors.append('base_url is malformed')
    if config.get('api_style') != 'responses':
        errors.append('Codex CLI experiment requires Responses API')
    if not isinstance(config.get('model'), str) or not config['model'].strip():
        errors.append('model must be a nonempty string')
    return {'ready': not errors, 'errors': errors}
