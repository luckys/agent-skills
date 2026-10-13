import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'skills/boost/scripts'))
import resources as r


class AnalysisTest(unittest.TestCase):
    def test_deep_domain_code_ci_and_container_are_found_without_guessing_a_cloud(self):
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            domain = project / 'layers/trading/server/trading/domain/Order.ts'
            domain.parent.mkdir(parents=True)
            domain.write_text('export class Order extends AggregateRoot {}')
            workflow = project / '.github/workflows/ci.yml'
            workflow.parent.mkdir(parents=True)
            workflow.write_text('name: CI\njobs: {}\n')
            (project / 'Dockerfile').write_text('FROM node:24\n')
            (project / '.env').write_text('DATABASE_URL=do-not-read\n')
            (project / 'package.json').write_text(json.dumps({'dependencies': {'nuxt': '^4.6.1', 'drizzle-orm': '^0.45.2'}, 'devDependencies': {'vitest': '^4.1.10', 'typescript': '^6.0.3'}}))
            (project / 'pnpm-lock.yaml').write_text('importers:\n  .:\n    devDependencies:\n      vitest:\n        version: 4.1.10\n')
            facts = r.inspect_project(project)
            self.assertTrue({'ddd', 'oop', 'github-actions', 'docker', 'nuxt', 'vue', 'drizzle', 'vitest', 'typescript'} <= set(facts['capabilities']))
            self.assertEqual(facts['capabilities']['vitest']['evidence'][0]['resolved'], {'pnpm-lock.yaml': '4.1.10'})
            self.assertEqual(facts['context_inventory']['deployment'][0]['target_hint'], 'container')
            self.assertNotIn('vercel', facts['capabilities'])
            self.assertNotIn('do-not-read', json.dumps(facts))
            self.assertEqual(facts['lifecycle']['observability']['status'], 'unknown')

    def test_directory_name_alone_does_not_prove_ddd(self):
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            (project / 'domain').mkdir()
            (project / 'domain/data.ts').write_text('export const value = 1')
            self.assertNotIn('ddd', r.inspect_project(project)['capabilities'])

    def test_monorepo_versions_are_associated_with_the_correct_importer(self):
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            app = project / 'apps/web'
            app.mkdir(parents=True)
            (app / 'package.json').write_text(json.dumps({'devDependencies': {'vitest': '^4.1.10'}}))
            (project / 'pnpm-lock.yaml').write_text('importers:\n  apps/web:\n    devDependencies:\n      vitest:\n        version: 4.1.10\n  apps/legacy:\n    devDependencies:\n      vitest:\n        version: 3.2.0\n')
            evidence = r.inspect_project(project)['capabilities']['vitest']['evidence'][0]
            self.assertEqual(evidence['path'], 'apps/web/package.json')
            self.assertEqual(evidence['resolved'], {'pnpm-lock.yaml': '4.1.10'})

    def test_search_preserves_rounded_installs_and_index_skill_alias(self):
        output = '\x1b[36mowner/repo@short-name\x1b[0m \x1b[32m12.4K installs\x1b[0m\n└ https://skills.sh/owner/repo/canonical-name\n'
        with patch.object(r.subprocess, 'run', return_value=subprocess.CompletedProcess([], 0, output, '')):
            result = r.search_results('topic', 'owner')['results'][0]
        self.assertEqual(result['installs_display'], '12.4K')
        self.assertIsNone(result['downloads'])
        self.assertEqual(result['url'], 'https://skills.sh/owner/repo/canonical-name')
        self.assertTrue(result['observed_at'])


if __name__ == '__main__':
    unittest.main()
