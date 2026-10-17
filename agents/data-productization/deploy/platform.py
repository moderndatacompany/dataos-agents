#!/usr/bin/env python3
"""Operator-side policy replay, private Secret entry and single-product registration."""
import argparse
from datetime import datetime, timezone
import getpass
import json
import os
from pathlib import Path
import re
import subprocess
import sys


def verify_target(c):
    directory = Path(c['cli_config_directory'])
    checks = [(directory / 'dataos.context.yaml', 'current_context_name', c['context']),
              (directory / c['context'] / '.dataos.tenancy.config.yaml', 'dataos_fqdn', c['host']),
              (directory / c['context'] / '.dataos.tenancy.config.yaml', 'dataos_tenant', c['tenant'])]
    for path, field, expected in checks:
        values = re.findall(r'^\s*' + field + r':\s*(\S+)\s*$', path.read_text(), re.M)
        if [x.strip('\"\'') for x in values] != [expected]:
            raise ValueError('CLI target mismatch: ' + field)


def request(c, path, method='GET', body=None):
    credential = Path(c['cli_config_directory']) / ('.' + c['host'] + '.dataos.cred.config.yaml')
    token = re.search(r'^\s*access_token:\s*(\S+)\s*$', credential.read_text(), re.M)
    if token is None:
        raise ValueError('No operator token in isolated CLI credential file')
    token = token[1].strip('\"\'')
    lines = ['url = ' + json.dumps('https://' + c['host'] + path),
             'header = ' + json.dumps('Authorization: Bearer ' + token),
             'header = "Content-Type: application/json"', 'request = ' + json.dumps(method)]
    if body is not None:
        lines.append('data = ' + json.dumps(json.dumps(body)))
    result = subprocess.run(['curl', '--silent', '--show-error', '--max-time', '60',
                             '--config', '-', '--write-out', '\n%{http_code}'],
                            input='\n'.join(lines) + '\n', text=True, capture_output=True, timeout=65)
    if result.returncode:
        raise RuntimeError('HTTP transport failed; sensitive diagnostics withheld')
    raw, status = result.stdout.rsplit('\n', 1)
    return int(status), json.loads(raw)


def policies(c, directory, apply):
    desired = json.loads((directory / 'access.json').read_text())
    status, actual = request(c, '/heimdall/api/v1/policies')
    if status != 200 or not isinstance(actual, list):
        raise RuntimeError('Cannot read existing policies: HTTP ' + str(status))
    actual = {p['name']: p for p in actual}
    missing = []
    for policy in desired:
        old = actual.get(policy['name'])
        if old is None:
            missing.append(policy)
        elif any(old.get(k) != v for k, v in policy.items()):
            raise ValueError('Existing policy differs; no write attempted: ' + policy['name'])
    print(json.dumps({'create': [p['name'] for p in missing],
                      'unchanged': len(desired) - len(missing), 'apply': apply}))
    if apply:
        for policy in missing:
            status, _ = request(c, '/heimdall/api/v1/policies', 'POST', policy)
            if status != 201:
                raise RuntimeError('Policy creation stopped at ' + policy['name'] + ': HTTP ' + str(status))


def secret(c, kind, apply):
    if not apply:
        raise ValueError('Private Secret submission requires --apply')
    value = getpass.getpass(kind + ' credential (hidden): ').strip()
    if len(value) < 20 or any(x.isspace() for x in value):
        raise ValueError('Invalid credential input; no write attempted')
    if kind == 'openai':
        name, data = c['model_secret'], {'OPENAI_API_KEY': value}
    else:
        name, data = c['git_secret'], {'GITSYNC_USERNAME': c['git_username'], 'GITSYNC_PASSWORD': value}
    manifest = {'name': name, 'version': 'v2alpha', 'type': 'secret', 'layer': 'user',
                'description': 'Credential for agent ' + c['agent_id'],
                'secret': {'type': 'key-value', 'data': data}}
    for extra in (['--lint'], []):
        result = subprocess.run([c['cli'], 'resource', 'apply', '--in', '--disable-interpolation', *extra],
                                input=json.dumps(manifest), text=True, capture_output=True, timeout=90,
                                env=dict(os.environ, DATAOS_CONFIG_DIRECTORY=c['cli_config_directory']))
        if result.returncode or 'level=error' in (result.stdout + result.stderr).lower():
            raise RuntimeError('Secret submission failed; sensitive diagnostics withheld')
    print('Stored ' + c['tenant'] + ':' + name)
