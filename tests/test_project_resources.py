import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.dont_write_bytecode = True
SCRIPT = Path(__file__).resolve().parents[1] / 'skills/boost/scripts/resources.py'
spec = importlib.util.spec_from_file_location('resources', SCRIPT)
resources = importlib.util.module_from_spec(spec)
spec.loader.exec_module(resources)


class ProjectResourcesTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.library = self.root / 'library'
        self.project = self.root / 'project'
        self.project.mkdir()
        self.skill('testing', 'Use for the observed test runner.')
        self.registry = {'sources': [{'id': 'personal', 'path': str(self.library)}]}

    def skill(self, name, description):
        path = self.library / 'skills' / name
        path.mkdir(parents=True)
        (path / 'SKILL.md').write_text(f'---\nname: {name}\ndescription: {description}\n---\n\n# Guidance\n')
        return path

    def selection(self, *names):
        catalog, _ = resources.catalog(self.registry)
        return {'clients': ['codex', 'opencode', 'antigravity'], 'resources': [
            {'id': item['id'], 'reviewed_sha256': item['sha256'], 'reason': 'Actual project evidence'}
            for item in catalog if item['name'] in names]}

    def test_preview_has_no_effect_and_install_is_idempotent(self):
        selected = self.selection('testing')
        resources.install(self.project, selected, self.registry)
        self.assertEqual(list(self.project.iterdir()), [])
        resources.install(self.project, selected, self.registry, True)
        dest = self.project / '.agents/skills/testing'
        self.assertEqual(dest.resolve(), self.library / 'skills/testing')
        original = (self.project / '.agents/resource-lock.json').read_bytes()
        second = resources.install(self.project, selected, self.registry, True)
        self.assertEqual(second['plan'][0]['action'], 'keep')
        self.assertEqual((self.project / '.agents/resource-lock.json').read_bytes(), original)
        self.assertTrue(resources.doctor(self.project)['ok'])

    def test_all_collisions_are_checked_before_creating_any_links(self):
        self.skill('writing', 'Use for documents.')
        existing = self.project / '.agents/skills/writing'
        existing.mkdir(parents=True)
        (existing / 'own.txt').write_text('User work')
        with self.assertRaisesRegex(ValueError, 'collision'):
            resources.install(self.project, self.selection('testing', 'writing'), self.registry, True)
        self.assertFalse((self.project / '.agents/skills/testing').exists())
        self.assertEqual((existing / 'own.txt').read_text(), 'User work')
        self.assertFalse((self.project / '.agents/resource-lock.json').exists())

    def test_foreign_and_broken_links_are_preserved(self):
        dest = self.project / '.agents/skills/testing'
        dest.parent.mkdir(parents=True)
        dest.symlink_to(self.root / 'missing')
        with self.assertRaisesRegex(ValueError, 'Foreign symlink'):
            resources.install(self.project, self.selection('testing'), self.registry, True)
        self.assertEqual(os.readlink(dest), str(self.root / 'missing'))

    def test_changed_supporting_file_invalidates_review(self):
        selected = self.selection('testing')
        (self.library / 'skills/testing/helper.py').write_text('print("unreviewed")')
        with self.assertRaisesRegex(ValueError, 'not reviewed'):
            resources.install(self.project, selected, self.registry, True)
        self.assertEqual(list(self.project.iterdir()), [])

    def test_symlinked_project_directory_cannot_modify_global_library(self):
        outside = self.root / 'outside'
        outside.mkdir()
        (self.project / '.agents').symlink_to(outside, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, 'escapes project'):
            resources.install(self.project, self.selection('testing'), self.registry, True)
        self.assertEqual(list(outside.iterdir()), [])

    def test_failure_during_linking_rolls_back_partial_install(self):
        self.skill('writing', 'Use for documents.')
        original = os.symlink
        def fail_second(target, destination, *args, **kwargs):
            if str(destination).endswith('/writing'):
                raise OSError('Simulated disk failure')
            return original(target, destination, *args, **kwargs)
        with patch.object(resources.os, 'symlink', side_effect=fail_second):
            with self.assertRaises(OSError):
                resources.install(self.project, self.selection('testing', 'writing'), self.registry, True)
        self.assertFalse((self.project / '.agents/skills/testing').is_symlink())
        self.assertFalse((self.project / '.agents/resource-lock.json').exists())

    def test_uninstall_preserves_preexisting_matching_user_link(self):
        dest = self.project / '.agents/skills/testing'
        dest.parent.mkdir(parents=True)
        dest.symlink_to(self.library / 'skills/testing', target_is_directory=True)
        resources.install(self.project, self.selection('testing'), self.registry, True)
        result = resources.uninstall(self.project, True)
        self.assertEqual(result['links'], [])
        self.assertTrue(dest.is_symlink())

    def test_uninstall_refuses_user_changes_to_managed_links(self):
        resources.install(self.project, self.selection('testing'), self.registry, True)
        dest = self.project / '.agents/skills/testing'
        dest.unlink()
        dest.write_text('User replacement')
        with self.assertRaisesRegex(ValueError, 'User changed'):
            resources.uninstall(self.project, True)
        self.assertEqual(dest.read_text(), 'User replacement')

    def test_doctor_detects_content_drift_and_owned_uninstall_works(self):
        resources.install(self.project, self.selection('testing'), self.registry, True)
        (self.library / 'skills/testing/SKILL.md').write_text('Changed after review')
        self.assertFalse(resources.doctor(self.project)['ok'])
        resources.uninstall(self.project, True)
        self.assertFalse((self.project / '.agents/skills/testing').is_symlink())

    def test_discovery_and_linking_do_not_run_bundled_code(self):
        marker = self.root / 'executed'
        (self.library / 'skills/testing/helper.py').write_text(f'from pathlib import Path\nPath({str(marker)!r}).touch()\n')
        resources.install(self.project, self.selection('testing'), self.registry, True)
        resources.doctor(self.project)
        self.assertFalse(marker.exists())

    def test_unsupported_agent_format_does_not_silently_gain_permissions(self):
        path = self.library / 'agents/reviewer.md'
        path.parent.mkdir()
        path.write_text('---\ndescription: Review\ntools: Read, Grep\n---\nRead-only review')
        with self.assertRaisesRegex(ValueError, 'No compatible client'):
            resources.install(self.project, self.selection('reviewer'), self.registry, True)
        self.assertEqual(list(self.project.iterdir()), [])

    def test_native_command_and_reference_workflow_with_same_name_are_distinct(self):
        for folder in ['commands', 'workflows']:
            directory = self.library / folder
            directory.mkdir()
            (directory / 'review.md').write_text('---\ndescription: Review\n---\nRead the current diff.')
        self.registry['sources'][0]['command_format'] = 'opencode-command'
        items, warnings = resources.catalog(self.registry)
        candidates = [item for item in items if item['name'] == 'review']
        self.assertEqual(len(candidates), 2)
        self.assertNotEqual(candidates[0]['id'], candidates[1]['id'])
        self.assertEqual(warnings, [])
        resources.install(self.project, self.selection('review'), self.registry, True)
        self.assertTrue((self.project / '.opencode/commands/review.md').is_symlink())
        self.assertTrue((self.project / '.agents/workflows/review.md').is_symlink())

    def test_monorepo_inventory_keeps_package_stacks_distinct_and_ignores_secrets(self):
        web = self.project / 'apps/web'
        web.mkdir(parents=True)
        (web / 'package.json').write_text(json.dumps({'dependencies': {'vue': '^3.5.0'}, 'scripts': {'test': 'secret-command'}}))
        (self.project / '.env').write_text('TOKEN=private')
        result = resources.inspect_project(self.project)
        self.assertEqual(result['dependencies']['apps/web/package.json'], {'vue': '^3.5.0'})
        self.assertEqual(result['scripts']['apps/web/package.json'], ['test'])
        self.assertNotIn('secret-command', json.dumps(result))
        self.assertNotIn('private', json.dumps(result))

    def test_fetch_keeps_existing_source_subdirectory_and_priority(self):
        data = self.root / 'cache'
        old_revision, new_revision = 'a' * 40, 'b' * 40
        registry_path = self.root / 'sources.json'
        resources.write_json(registry_path, {'sources': [{
            'id': 'pstack', 'repository': 'cursor/plugins', 'priority': 10,
            'revision': old_revision, 'path': str(data / 'sources/pstack' / old_revision / 'pstack')}]})
        def downloaded_source(command, **kwargs):
            if 'clone' in command:
                (Path(command[-1]) / 'pstack').mkdir(parents=True)
        with patch.object(resources, 'DATA', data), patch.object(resources.subprocess, 'run', side_effect=downloaded_source), patch.object(resources.subprocess, 'check_output', return_value=new_revision + '\n'):
            source = resources.fetch_source('cursor/plugins', registry_path, source_id='pstack')
        self.assertEqual(source['priority'], 10)
        self.assertEqual(source['subdirectory'], 'pstack')
        self.assertEqual(Path(source['path']), data / 'sources/pstack' / new_revision / 'pstack')
        self.assertEqual(resources.read_json(registry_path)['sources'][0]['revision'], new_revision)

    def test_fetch_rejects_escaping_subdirectory_before_network_or_registry_changes(self):
        registry_path = self.root / 'sources.json'
        with patch.object(resources.subprocess, 'run') as network:
            with self.assertRaisesRegex(ValueError, 'within the repository'):
                resources.fetch_source('owner/repo', registry_path, subdirectory='../outside')
            network.assert_not_called()
        self.assertFalse(registry_path.exists())


if __name__ == '__main__':
    unittest.main()
