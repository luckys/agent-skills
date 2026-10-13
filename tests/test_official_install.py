import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'skills/boost/scripts'))
import official
r = official.r


class OfficialInstallTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.project = self.root / 'project'
        self.project.mkdir()
        self.library = self.root / 'review'
        self.registry = {'sources': [{'id': 'personal', 'path': str(self.library), 'repository': 'luckys/agent-skills'}]}
        self.cache = patch.object(r, 'DATA', self.root / 'downloaded-packages')
        self.cache.start()
        self.addCleanup(self.cache.stop)
        self.skill('testing')
        self.cli = patch.object(official.subprocess, 'run', side_effect=self.fake_cli)
        self.run = self.cli.start()
        self.addCleanup(self.cli.stop)
        self.which = patch.object(official.shutil, 'which', return_value='/usr/bin/pnpx')
        self.which.start()
        self.addCleanup(self.which.stop)

    def skill(self, name):
        folder = self.library / name
        folder.mkdir(parents=True)
        (folder / 'SKILL.md').write_text(f'---\nname: {name}\ndescription: Test guidance\n---\nBody\n')
        return folder

    def selection(self, *names):
        items, _ = r.catalog(self.registry)
        return {'clients': ['codex', 'opencode', 'antigravity'], 'resources': [
            {'id': item['id'], 'reviewed_sha256': item['sha256'], 'reason': 'Observed project evidence'}
            for item in items if item['name'] in names]}

    def fake_cli(self, args, cwd, **kwargs):
        self.assertEqual(args[:3], ['pnpx', 'skills', 'add'])
        self.assertIn(args[3], ['luckys/agent-skills', 'anthropics/skills'])
        self.assertNotIn('--global', args)
        name = args[args.index('--skill') + 1]
        stage = Path(cwd)
        destination = stage / '.agents/skills' / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        source = next(s for s in self.registry['sources'] if s['repository'] == args[3])
        shutil.copytree(Path(source['path']) / name, destination)
        _, lock = official.cli_lock(stage)
        lock['skills'][name] = {'source': args[3], 'sourceType': 'github', 'computedHash': 'cli-receipt'}
        r.write_json(stage / 'skills-lock.json', lock)
        return subprocess.CompletedProcess(args, 0, json.dumps([{'name': name, 'status': 'installed'}]), '')

    def test_preview_then_official_install_is_portable_and_idempotent(self):
        selected = self.selection('testing')
        preview = official.install(self.project, selected, self.registry)
        self.assertEqual(list(self.project.iterdir()), [])
        self.assertEqual(preview['plan'][0]['command'][:4], ['pnpx', 'skills', 'add', 'luckys/agent-skills'])
        self.run.assert_not_called()
        official.install(self.project, selected, self.registry, True)
        destination = self.project / '.agents/skills/testing'
        self.assertTrue(destination.is_dir())
        self.assertTrue(destination.is_symlink())
        self.assertTrue(destination.resolve().is_relative_to(r.DATA))
        shutil.rmtree(self.library)
        self.assertTrue(r.doctor(self.project)['ok'])
        self.assertEqual(r.read_json(self.project / 'skills-lock.json')['skills']['testing']['source'], 'luckys/agent-skills')

    def test_second_run_reuses_official_copy_without_download(self):
        selected = self.selection('testing')
        official.install(self.project, selected, self.registry, True)
        self.run.reset_mock()
        result = official.install(self.project, selected, self.registry, True)
        self.assertEqual(result['plan'][0]['action'], 'keep')
        self.run.assert_not_called()

    def test_unpublished_local_skill_is_not_an_install_source(self):
        self.registry['sources'][0].pop('repository')
        with self.assertRaisesRegex(ValueError, 'upstream repository'):
            official.install(self.project, self.selection('testing'), self.registry, True)
        self.run.assert_not_called()
        self.assertEqual(list(self.project.iterdir()), [])

    def test_local_link_command_refuses_portable_skills(self):
        with self.assertRaisesRegex(ValueError, 'pnpx skills add'):
            r.native_only(self.selection('testing'), self.registry)

    def test_user_file_collision_aborts_before_download(self):
        path = self.project / '.agents/skills/testing'
        path.mkdir(parents=True)
        (path / 'work.txt').write_text('User work')
        with self.assertRaisesRegex(ValueError, 'collision'):
            official.install(self.project, self.selection('testing'), self.registry, True)
        self.run.assert_not_called()
        self.assertEqual((path / 'work.txt').read_text(), 'User work')

    def test_upstream_drift_during_download_does_not_publish(self):
        original = self.fake_cli
        def changed(args, cwd, **kwargs):
            result = original(args, cwd, **kwargs)
            name = args[args.index('--skill') + 1]
            (Path(cwd) / '.agents/skills' / name / 'SKILL.md').write_text('Unreviewed upstream change')
            return result
        self.run.side_effect = changed
        with self.assertRaisesRegex(ValueError, 'since review'):
            official.install(self.project, self.selection('testing'), self.registry, True)
        self.assertEqual(list(self.project.iterdir()), [])

    def test_failed_second_download_does_not_install_first(self):
        self.skill('writing')
        original = self.fake_cli
        def fail(args, cwd, **kwargs):
            if 'writing' in args: return subprocess.CompletedProcess(args, 1, '', 'Failure')
            return original(args, cwd, **kwargs)
        self.run.side_effect = fail
        with self.assertRaisesRegex(ValueError, 'installation failed'):
            official.install(self.project, self.selection('testing', 'writing'), self.registry, True)
        self.assertEqual(list(self.project.iterdir()), [])

    def test_manifest_failure_restores_owned_legacy_link_and_both_locks(self):
        selected = self.selection('testing')
        r.install(self.project, selected, self.registry, True)
        destination = self.project / '.agents/skills/testing'
        old_target = destination.readlink()
        old_lock = (self.project / '.agents/resource-lock.json').read_bytes()
        original = r.write_json
        def fail(path, value):
            if path == self.project / '.agents/resource-lock.json': raise OSError('Disk failure')
            return original(path, value)
        with patch.object(r, 'write_json', side_effect=fail):
            with self.assertRaises(OSError): official.install(self.project, selected, self.registry, True)
        self.assertEqual(destination.readlink(), old_target)
        self.assertEqual((self.project / '.agents/resource-lock.json').read_bytes(), old_lock)
        self.assertFalse((self.project / 'skills-lock.json').exists())

    def test_owned_official_copy_is_removed_but_unrelated_cli_entry_survives(self):
        official.install(self.project, self.selection('testing'), self.registry, True)
        lock = r.read_json(self.project / 'skills-lock.json')
        lock['skills']['user-skill'] = {'source': 'other/repo'}
        r.write_json(self.project / 'skills-lock.json', lock)
        r.uninstall(self.project, True)
        self.assertFalse((self.project / '.agents/skills/testing').exists())
        self.assertEqual(r.read_json(self.project / 'skills-lock.json')['skills'], {'user-skill': {'source': 'other/repo'}})

    def test_user_modified_copy_is_detected_and_preserved(self):
        official.install(self.project, self.selection('testing'), self.registry, True)
        path = self.project / '.agents/skills/testing/SKILL.md'
        path.write_text('User changes')
        self.assertFalse(r.doctor(self.project)['ok'])
        with self.assertRaisesRegex(ValueError, 'User changed'):
            r.uninstall(self.project, True)
        self.assertEqual(path.read_text(), 'User changes')

    def test_ui_projects_cannot_silently_omit_frontend_design(self):
        (self.project / 'package.json').write_text(json.dumps({'dependencies': {'react': '^19.0.0'}}))
        with self.assertRaisesRegex(ValueError, 'frontend-design'):
            official.install(self.project, self.selection('testing'), self.registry)
        selected = self.selection('testing')
        selected['omissions'] = {'frontend-design': 'User explicitly requests only a backend change in this monorepo.'}
        official.install(self.project, selected, self.registry)

    def test_react_vue_and_plain_html_recommend_the_official_design_skill(self):
        for dependency in ['react', 'vue', 'nuxt', 'next', 'svelte', 'astro']:
            with self.subTest(dependency=dependency):
                (self.project / 'package.json').write_text(json.dumps({'peerDependencies': {dependency: '*'}}))
                facts = r.inspect_project(self.project)
                self.assertEqual(facts['recommended_skills'][0]['repository'], 'anthropics/skills')
                self.assertEqual(facts['recommended_skills'][0]['skill'], 'frontend-design')
        (self.project / 'package.json').unlink()
        (self.project / 'index.html').write_text('<main>Interface</main>')
        self.assertTrue(r.inspect_project(self.project)['frontend']['detected'])

    def test_ui_design_installs_from_anthropic_alongside_a_personal_skill(self):
        source = self.root / 'anthropic/frontend-design'
        source.mkdir(parents=True)
        (source / 'SKILL.md').write_text('---\nname: frontend-design\ndescription: Design interfaces\n---\nDesign guidance\n')
        self.registry['sources'].append({'id': 'anthropics', 'repository': 'anthropics/skills', 'path': str(source.parent)})
        (self.project / 'package.json').write_text(json.dumps({'dependencies': {'vue': '^3.0.0'}}))
        official.install(self.project, self.selection('testing', 'frontend-design'), self.registry, True)
        self.assertEqual([call.args[0][3] for call in self.run.call_args_list], ['anthropics/skills', 'luckys/agent-skills'])
        self.assertTrue(r.doctor(self.project)['ok'])
        self.assertEqual(r.read_json(self.project / 'skills-lock.json')['skills']['frontend-design']['source'], 'anthropics/skills')

    def test_inventory_reports_languages_toolchains_and_resolved_versions(self):
        (self.project / 'package.json').write_text(json.dumps({'dependencies': {'vue': '^3.5.0'}, 'engines': {'node': '>=22'}, 'packageManager': 'pnpm@12.11.2'}))
        (self.project / 'main.ts').write_text('export const value = 1')
        (self.project / '.nvmrc').write_text('22.6.0')
        (self.project / 'pnpm-lock.yaml').write_text('importers:\n  .:\n    dependencies:\n      vue:\n        specifier: ^3.5.0\n        version: 3.5.13(typescript@5.7.2)\n')
        facts = r.inspect_project(self.project)
        self.assertEqual(facts['languages'], ['TypeScript'])
        self.assertEqual(facts['dependencies']['package.json']['vue'], '^3.5.0')
        self.assertEqual(facts['resolved_versions']['pnpm-lock.yaml']['.:vue'], '3.5.13')
        self.assertEqual(facts['toolchains']['.nvmrc'], '22.6.0')
        self.assertEqual(facts['toolchains']['package.json']['packageManager'], 'pnpm@12.11.2')

    def test_prepare_starts_with_only_the_official_personal_repository(self):
        destination = self.root / 'official-catalog.json'
        def fetched(repository, path, **kwargs):
            source = {'id': kwargs['source_id'], 'repository': repository, 'path': str(self.library), 'revision': 'a' * 40}
            current = r.read_json(path)
            current['sources'].append(source)
            r.write_json(path, current)
            return source
        with patch.object(r, 'fetch_source', side_effect=fetched) as fetch, patch.object(r, 'load_registry', side_effect=AssertionError('Local catalogs must not be read')):
            official.prepare(destination)
        self.assertEqual(fetch.call_count, 1)
        self.assertEqual(fetch.call_args.args[0], 'luckys/agent-skills')
        source = r.read_json(destination)['sources'][0]
        self.assertEqual(source['priority'], 0)
        self.assertEqual(source['repository'], 'luckys/agent-skills')

    def test_personal_catalog_is_ranked_before_a_community_equivalent(self):
        self.registry['sources'][0]['priority'] = 0
        folder = self.root / 'community/testing'
        folder.mkdir(parents=True)
        (folder / 'SKILL.md').write_text('---\nname: testing\ndescription: Community equivalent\n---\nGuidance\n')
        self.registry['sources'].append({'id': 'community', 'repository': 'other/skills', 'path': str(folder.parent), 'priority': 20})
        items, _ = r.catalog(self.registry)
        self.assertEqual([item['repository'] for item in items], ['luckys/agent-skills', 'other/skills'])

    def test_personal_design_skill_satisfies_frontend_coverage(self):
        self.skill('frontend-design')
        (self.project / 'package.json').write_text(json.dumps({'dependencies': {'react': '^19.0.0'}}))
        result = official.install(self.project, self.selection('frontend-design'), self.registry)
        self.assertEqual(result['plan'][0]['repository'], 'luckys/agent-skills')

    def test_owner_search_and_missing_catalog_never_use_a_local_working_copy(self):
        self.assertEqual(r.search_command('oop', 'luckys'), ['pnpx', 'skills', 'find', 'oop', '--owner', 'luckys'])
        self.assertEqual(r.load_registry(self.root / 'missing-catalog.json')['sources'], [])


if __name__ == '__main__': unittest.main()
