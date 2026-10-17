#!/usr/bin/env python3
"""Operator installer. Render/check by default; --apply performs declared setup."""
import argparse
import base64
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent


def load_platform():
    spec = importlib.util.spec_from_file_location('platform_access', ROOT / 'deploy/platform.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def configuration(path, cli, config_directory):
    c = json.loads(path.read_text())
    required = set(json.loads((ROOT / 'environment.example.json').read_text()))
    if not required <= set(c):
        raise ValueError('Missing configuration: ' + ', '.join(sorted(required - set(c))))
    for key in ('agent_id', 'resource_prefix', 'model_secret', 'git_secret'):
        if not re.fullmatch(r'[a-z][a-z0-9]{0,47}', c[key]):
            raise ValueError('Invalid resource name: ' + key)
    for key in ('tenant', 'operator_id', 'compute', 'depot', 'source_secret'):
        if not re.fullmatch(r'[A-Za-z0-9_.-]+', c[key]):
            raise ValueError('Invalid identifier: ' + key)
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9.-]+', c['host']):
        raise ValueError('host must be a bare hostname')
    url = urlparse(c['git_repository'])
    if url.scheme != 'https' or not url.hostname or url.username or url.password:
        raise ValueError('Use an HTTPS Git URL without embedded credentials')
    if not c['git_branch'] or c['git_branch'].startswith('-') or any(ord(x) < 32 for x in c['git_branch']):
        raise ValueError('Invalid Git branch')
    if not shutil.which(cli):
        raise ValueError('DataOS CLI executable not found')
    c['cli'] = cli
    c['cli_config_directory'] = str(Path(config_directory).expanduser().resolve())
    text = (Path(c['cli_config_directory']) / 'dataos.context.yaml').read_text()
    match = re.search(r'^\s*current_context_name:\s*(\S+)\s*$', text, re.M)
    if not match:
        raise ValueError('CLI context is not initialized')
    c['context'] = match[1].strip('\"\'')
    c.setdefault('git_username', 'x-bitbucket-api-token-auth' if url.hostname == 'bitbucket.org' else 'x-access-token')
    c.setdefault('sandbox_mode', 'workspace-write')
    if c['sandbox_mode'] not in ('workspace-write', 'read-only', 'danger-full-access'):
        raise ValueError('Invalid sandbox_mode')
    if c['sandbox_mode'] == 'danger-full-access' and not c.get('container_execution_authorized'):
        raise ValueError('Direct container execution needs explicit operator authorization')
    return c


def render(c, output):
    lock = json.loads((ROOT / 'deploy/runtime.lock.json').read_text())
    lock.update(c.get('runtime_overrides', {}))
    if set(lock) != {'main_image', 'cli_image', 'vulcan_image', 'codex_package'}:
        raise ValueError('Unknown runtime override')
    if not re.fullmatch(r'@openai/codex@[A-Za-z0-9.+_-]+', lock['codex_package']):
        raise ValueError('Invalid Codex package selection')
    values = dict(c, **lock)
    instructions = (ROOT / 'runtime/instructions.md').read_text()
    instructions += '\nRead /etc/dataos/work/agent/skills/productize/SKILL.md and /etc/dataos/work/agent/tools.md as needed. Vulcan docs are at /etc/dataos/work/agent/docs. Environment defaults are in /etc/dataos/work/agent/environment.json.\n'
    config = '\n'.join(k + ' = ' + json.dumps(v) for k, v in {
        'model': c['model'], 'model_reasoning_effort': c['reasoning_effort'],
        'forced_login_method': 'api', 'cli_auth_credentials_store': 'file',
        'sandbox_mode': c['sandbox_mode'], 'developer_instructions': instructions,
    }.items()) + '\n[mcp_servers.dataos]\ncommand = "/etc/dataos/work/bin/dataos-ctl"\nargs = ["develop", "assist", "mcp", "run"]\nenabled_tools = ["dataos_resource_get", "dataos_resource_apply", "dataos_resource_log", "dataos_resource_runtime_get", "dataos_schema_get", "dataos_schema_validate", "dataos_develop_stack_versions"]\n'
    files = {'/etc/dataos/work/agent-config.toml': config,
             '/etc/dataos/work/git-url': c['git_repository'], '/etc/dataos/work/git-branch': c['git_branch']}
    for f in sorted((ROOT / 'runtime').rglob('*')):
        if f.is_file():
            files['/etc/dataos/work/agent/' + f.relative_to(ROOT / 'runtime').as_posix()] = f.read_text()
    files['/etc/dataos/work/agent/environment.json'] = json.dumps({k: c[k] for k in (
        'host', 'tenant', 'agent_id', 'compute', 'depot', 'resource_prefix',
        'git_repository', 'git_branch', 'git_secret')}, indent=2)
    # Only runtime content is projected. deploy/, installer and operator context stay outside.
    commands = []
    for path, text in files.items():
        commands.append('mkdir -p ' + str(Path(path).parent))
        commands.append("printf '%s' '" + base64.b64encode(text.encode()).decode() + "' | base64 -d > " + path)
    values['RUNTIME_FILES'] = '\n'.join(commands)

    def replace(text):
        def token(m):
            key = m[1]
            if key.startswith('FILE:'):
                return base64.b64encode((ROOT / 'runtime' / key[5:]).read_bytes()).decode()
            if key not in values:
                raise ValueError('Unresolved template variable: ' + key)
            return str(values[key])
        return re.sub(r'@@([^@]+)@@', token, text)

    def walk(obj):
        if isinstance(obj, str): return replace(obj)
        if isinstance(obj, list): return [walk(x) for x in obj]
        if isinstance(obj, dict): return {k: walk(v) for k, v in obj.items()}
        return obj

    service = walk(json.loads((ROOT / 'deploy/service.template.json').read_text()))
    policies = walk(json.loads((ROOT / 'deploy/access.template.json').read_text()))
    output.mkdir(parents=True, exist_ok=False)
    for name, obj in [('service.json', service), ('access.json', policies), ('config.json', c)]:
        (output / name).write_text(json.dumps(obj, indent=2) + '\n')
    return service, policies


def cli_run(c, args):
    result = subprocess.run([c['cli'], *args], capture_output=True, text=True, timeout=120,
                            env=dict(os.environ, DATAOS_CONFIG_DIRECTORY=c['cli_config_directory'], GIT_TERMINAL_PROMPT='0'))
    if result.returncode or 'level=error' in (result.stdout + result.stderr).lower():
        raise RuntimeError('CLI operation failed: ' + ' '.join(args[:3]) + '; inspect with your operator CLI')
    return result.stdout


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('config', type=Path)
    parser.add_argument('--cli', default='dataos-ctl')
    parser.add_argument('--cli-config', default=os.environ.get('DATAOS_CONFIG_DIRECTORY', str(Path.home() / '.dataos')))
    parser.add_argument('--output', type=Path)
    parser.add_argument('--render-only', action='store_true')
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    if args.render_only and args.apply:
        raise ValueError('--render-only and --apply are mutually exclusive')
    c = configuration(args.config, args.cli, args.cli_config)
    platform = load_platform()
    platform.verify_target(c)
    output = args.output or Path(tempfile.mkdtemp(prefix='dataos-agent-')) / 'rendered'
    render(c, output)
    if args.render_only:
        print(json.dumps({'rendered': str(output), 'platform_writes': False})); return
    status, user = platform.request(c, '/heimdall/api/v1/users/' + c['agent_id'])
    if status not in (200, 404):
        raise RuntimeError('Cannot inspect application identity: HTTP ' + str(status))
    if status == 200 and (not isinstance(user, dict) or user.get('type') != 'application'):
        raise ValueError('Existing identity is not an application; refusing to reuse it')
    print(json.dumps({'identity': 'exists' if status == 200 else 'create', 'rendered': str(output)}))
    platform.policies(c, output, False)
    if not args.apply:
        return
    # This operator command intentionally creates only missing resources and additive grants.
    if status == 404:
        cli_run(c, ['user', 'create', '--user_id', c['agent_id'], '--name', c['agent_id'], '--type', 'application'])
    for kind, key in [('openai', 'model_secret'), ('git', 'git_secret')]:
        try:
            found = cli_run(c, ['resource', 'get', '-t', 'secret', '-n', c[key], '-d'])
        except RuntimeError:
            raise RuntimeError('Cannot inspect credential Secret; initialize it explicitly before retrying: ' + c[key])
        if c[key] not in found:
            platform.secret(c, kind, True)
    # Require configured source/compute to exist; installation does not invent data connections.
    for typ, name in [('depot', c['depot']), ('compute', c['compute'])]:
        found = cli_run(c, ['resource', 'get', '-t', typ, '-n', name, '-d'])
        if name not in found: raise ValueError('Configured resource not found: ' + typ + ':' + name)
    platform.policies(c, output, True)
    cli_run(c, ['resource', 'apply', '-f', str(output / 'service.json'), '--lint', '--disable-interpolation'])
    cli_run(c, ['resource', 'apply', '-f', str(output / 'service.json'), '--disable-interpolation'])
    print(json.dumps({'service': 'service:v2alpha:' + c['agent_id'], 'state': 'submitted',
                      'verify': 'Inspect Service runtime/logs; hosted Git clone and model/tool checks must pass before declaring ready.'}))


if __name__ == '__main__':
    try: main()
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as exc:
        print(str(exc) if isinstance(exc, (ValueError, RuntimeError)) else 'Installer failed; credential-bearing diagnostics withheld', file=sys.stderr)
        sys.exit(1)
