"""Offline operator/runtime boundary and installer checks; no network or model calls."""
import base64
import contextlib
import importlib.util
import io
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('agent_installer', ROOT / 'install.py')
installer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(installer)


class PackageChecks(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.area = Path(self.tmp.name)
        self.config = json.loads((ROOT / 'environment.example.json').read_text())
        self.config.update(agent_id='freshagent', tenant='fresh', host='fresh.example.test',
                           operator_id='freshoperator', compute='freshcompute', depot='freshdepot',
                           source_secret='freshsource', model_secret='freshmodel', git_secret='freshgit',
                           resource_prefix='freshdp')
        self.path = self.area / 'environment.json'
        self.path.write_text(json.dumps(self.config))
        self.cli_dir = self.area / 'cli'
        (self.cli_dir / 'freshcontext').mkdir(parents=True)
        (self.cli_dir / 'dataos.context.yaml').write_text('current_context_name: freshcontext\n')
        (self.cli_dir / 'freshcontext/.dataos.tenancy.config.yaml').write_text(
            'dataos_fqdn: fresh.example.test\ndataos_tenant: fresh\n')

    def load(self):
        return installer.configuration(self.path, '/usr/bin/true', str(self.cli_dir))

    def test_runtime_contains_no_operator_artifacts(self):
        service, policies = installer.render(self.load(), self.area / 'rendered')
        self.assertEqual(service['spec']['runAsUser'], 'freshagent')
        self.assertEqual(service['name'], 'freshagent')
        serialized = json.dumps([service, policies])
        for stale in ('@@', 'showcaseagent20261017', 'sawaniks', 'soumadipde'):
            self.assertNotIn(stale, serialized)
        boot = service['spec']['stackSpec']['arguments'][0]
        payloads = [base64.b64decode(x).decode() for x in
                    re.findall(r"printf '%s' '([A-Za-z0-9+/=]+)' \| base64 -d", boot)]
        self.assertTrue(any('name: productize' in x for x in payloads))
        self.assertTrue(any('developer_instructions =' in x for x in payloads))
        for text in payloads:
            self.assertNotIn('name: build-dataos-agent', text)
            self.assertNotIn('def policies(', text)
            self.assertNotIn('cli_config_directory', text)
        script = self.area / 'bootstrap.sh'
        script.write_text(boot)
        subprocess.run(['bash', '-n', str(script)], check=True)

    def test_existing_render_directory_is_preserved(self):
        out = self.area / 'rendered'
        out.mkdir()
        sentinel = out / 'keep'
        sentinel.write_text('preserve')
        with self.assertRaises(FileExistsError): installer.render(self.load(), out)
        self.assertEqual(sentinel.read_text(), 'preserve')

    def test_target_mismatch_and_embedded_credentials_fail(self):
        platform = installer.load_platform()
        c = self.load()
        platform.verify_target(c)
        with self.assertRaises(ValueError): platform.verify_target(dict(c, host='wrong.example.test'))
        self.config['git_repository'] = 'https://user:secret@example.test/repo'
        self.path.write_text(json.dumps(self.config))
        with self.assertRaises(ValueError): self.load()

    def test_direct_execution_requires_authorization(self):
        self.config['sandbox_mode'] = 'danger-full-access'
        self.path.write_text(json.dumps(self.config))
        with self.assertRaises(ValueError): self.load()
        self.config['container_execution_authorized'] = True
        self.path.write_text(json.dumps(self.config))
        self.assertEqual(self.load()['sandbox_mode'], 'danger-full-access')

    def test_dry_run_performs_no_writes(self):
        platform = installer.load_platform()
        calls = []
        def request(c, path, method='GET', body=None):
            calls.append(method)
            return (200, {'type': 'application'}) if '/users/' in path else (200, [])
        platform.request = request
        argv = ['install.py', str(self.path), '--cli', '/usr/bin/true', '--cli-config', str(self.cli_dir)]
        with patch.object(installer, 'load_platform', return_value=platform), \
             patch.object(installer, 'cli_run', side_effect=AssertionError('dry run executed CLI mutation')), \
             patch.object(sys, 'argv', argv), contextlib.redirect_stdout(io.StringIO()):
            installer.main()
        self.assertTrue(calls)
        self.assertEqual(set(calls), {'GET'})

    def test_policy_conflict_prevents_all_mutation(self):
        platform = installer.load_platform()
        out = self.area / 'rendered'
        c = self.load()
        _, policies = installer.render(c, out)
        conflict = dict(policies[-1], allow=False)
        calls = []
        def request(c, path, method='GET', body=None):
            calls.append(method)
            return 200, [conflict]
        platform.request = request
        with self.assertRaises(ValueError): platform.policies(c, out, True)
        self.assertEqual(calls, ['GET'])


if __name__ == '__main__': unittest.main()
