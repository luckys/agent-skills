import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.dont_write_bytecode = True
SCRIPTS = Path(__file__).resolve().parents[1] / 'skills/boost/scripts'
sys.path.insert(0, str(SCRIPTS))
import global_setup


class GlobalSetupTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.user = self.root / 'user'
        self.data = self.root / 'data'
        self.repository = Path(__file__).resolve().parents[1]
        self.original = {
            '.agents/skills/testing/SKILL.md': '---\nname: testing\ndescription: Tests\n---\n',
            '.config/opencode/agents/reviewer.md': 'Original reviewer\n',
            '.config/opencode/commands/review.md': 'Original workflow\n',
            '.agents/.skill-lock.json': '{"version": 3, "skills": {"testing": {}}, "dismissed": {}}\n',
            '.codex/config.toml': 'unchanged = true\n',
        }
        for name, content in self.original.items():
            path = self.user / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content)
        alias = self.user / '.claude/skills/testing'
        alias.parent.mkdir(parents=True)
        alias.symlink_to('../../.agents/skills/testing')
        self.seed = patch.object(global_setup, 'seed_sources', return_value=[])
        self.seed.start()
        self.addCleanup(self.seed.stop)

    def setup(self, apply=True):
        return global_setup.setup(self.user, self.repository, self.data, apply=apply)

    def assert_originals(self):
        for name, content in self.original.items():
            self.assertEqual((self.user / name).read_text(), content)
        self.assertEqual(os.readlink(self.user / '.claude/skills/testing'), '../../.agents/skills/testing')
        self.assertTrue((self.user / '.claude/skills/testing/SKILL.md').is_file())

    def test_preview_and_full_restore_preserve_files_aliases_and_native_config(self):
        self.setup(False)
        self.assert_originals()
        self.assertFalse(self.data.exists())
        result = self.setup()
        self.assertEqual({p.name for p in (self.user / '.agents/skills').iterdir()}, {'boost', 'flow'})
        self.assertEqual((self.user / '.codex/config.toml').read_text(), 'unchanged = true\n')
        self.assertEqual(self.setup()['status'], 'already configured')
        global_setup.restore(Path(result['backup']), True)
        self.assert_originals()
        self.assertFalse((self.user / '.codex/agents/boost.toml').is_symlink())

    def test_unmanaged_native_bridge_collision_aborts_before_retirement(self):
        path = self.user / '.gemini/antigravity-cli/skills'
        path.mkdir(parents=True)
        with self.assertRaisesRegex(ValueError, 'collision'):
            self.setup()
        self.assert_originals()
        self.assertFalse(self.data.exists())

    def test_failed_global_link_rolls_back_all_retired_resources(self):
        original = os.symlink
        def fail_bridge(target, destination, *args, **kwargs):
            if str(destination).endswith('/.gemini/config/agents'):
                raise OSError('Simulated disk failure')
            return original(target, destination, *args, **kwargs)
        with patch.object(global_setup.os, 'symlink', side_effect=fail_bridge):
            with self.assertRaises(OSError):
                self.setup()
        self.assert_originals()
        self.assertFalse((self.user / '.agents/global-setup.json').exists())

    def test_restore_refuses_changed_registry_and_foreign_global_link(self):
        result = self.setup()
        backup = Path(result['backup'])
        registry = self.user / '.agents/resource-sources.json'
        original = registry.read_bytes()
        registry.write_text('{}')
        with self.assertRaisesRegex(ValueError, 'config changed'):
            global_setup.restore(backup, True)
        registry.write_bytes(original)
        link = self.user / '.agents/skills/boost'
        link.unlink()
        link.symlink_to(self.root / 'foreign')
        with self.assertRaisesRegex(ValueError, 'link changed'):
            global_setup.restore(backup, True)
        self.assertEqual(os.readlink(link), str(self.root / 'foreign'))

    def test_missing_backup_aborts_before_removing_bridges(self):
        result = self.setup()
        backup = Path(result['backup'])
        (backup.parent / 'commands/review.md').unlink()
        with self.assertRaisesRegex(ValueError, 'entry missing'):
            global_setup.restore(backup, True)
        self.assertTrue((self.user / '.agents/skills/boost').is_symlink())

    def test_global_directory_alias_preserves_source_and_restores_original_alias(self):
        directory = self.user / '.config/opencode/agents'
        source = self.root / 'personal-agents'
        directory.rename(source)
        directory.symlink_to(source, target_is_directory=True)
        result = self.setup()
        self.assertEqual((source / 'reviewer.md').read_text(), 'Original reviewer\n')
        self.assertFalse(directory.is_symlink())
        self.assertTrue((directory / 'boost.md').is_symlink())
        (directory / 'user-agent.md').write_text('New user work')
        with self.assertRaisesRegex(ValueError, 'user directory entry'):
            global_setup.restore(Path(result['backup']), True)
        (directory / 'user-agent.md').unlink()
        global_setup.restore(Path(result['backup']), True)
        self.assertEqual(os.readlink(directory), str(source))
        self.assert_originals()

    def legacy_setup(self):
        result = self.setup()
        backup = Path(result['backup'])
        snapshot = json.loads(backup.read_text())
        legacy = {}
        for name, target in snapshot['created_links'].items():
            if name == '.config/opencode/commands/flow.md':
                (self.user / name).unlink()
                continue
            old_name = name.replace('boost', 'project-bootstrap').replace('flow', 'work-lifecycle')
            old_target = target.replace('boost', 'project-bootstrap').replace('flow', 'work-lifecycle')
            if old_name != name or old_target != target:
                (self.user / name).unlink()
                (self.user / old_name).symlink_to(old_target)
            legacy[old_name] = old_target
        snapshot['created_links'] = legacy
        global_setup.write_json(backup, snapshot)
        state_path = self.user / '.agents/global-setup.json'
        state = json.loads(state_path.read_text())
        state['global_skills'] = ['project-bootstrap', 'work-lifecycle']
        global_setup.write_json(state_path, state)
        return backup, legacy

    def test_short_names_upgrade_is_idempotent_and_original_restore_still_works(self):
        backup, legacy = self.legacy_setup()
        preview = global_setup.upgrade_short_names(self.user, self.repository)
        self.assertFalse(preview['apply'])
        self.assertTrue((self.user / '.agents/skills/project-bootstrap').is_symlink())
        result = global_setup.upgrade_short_names(self.user, self.repository, True)
        self.assertEqual(result['global_skills'], ['boost', 'flow'])
        self.assertEqual({path.name for path in (self.user / '.agents/skills').iterdir()}, {'boost', 'flow'})
        self.assertTrue((self.user / '.config/opencode/commands/flow.md').is_symlink())
        self.assertEqual(global_setup.upgrade_short_names(self.user, self.repository, True)['status'], 'already configured')
        global_setup.restore(backup, True)
        self.assert_originals()

    def test_short_names_collision_preserves_old_setup(self):
        backup, legacy = self.legacy_setup()
        collision = self.user / '.agents/skills/boost'
        collision.write_text('User work')
        with self.assertRaisesRegex(ValueError, 'collision'):
            global_setup.upgrade_short_names(self.user, self.repository, True)
        self.assertEqual(collision.read_text(), 'User work')
        for name, target in legacy.items():
            self.assertEqual(os.readlink(self.user / name), target)

    def test_short_names_failure_restores_links_and_restore_manifest(self):
        backup, legacy = self.legacy_setup()
        before = backup.read_bytes()
        state_path = self.user / '.agents/global-setup.json'
        state_before = state_path.read_bytes()
        original = os.symlink
        def fail_flow(target, destination, *args, **kwargs):
            if str(destination).endswith('/commands/flow.md'):
                raise OSError('Simulated disk failure')
            return original(target, destination, *args, **kwargs)
        with patch.object(global_setup.os, 'symlink', side_effect=fail_flow):
            with self.assertRaises(OSError):
                global_setup.upgrade_short_names(self.user, self.repository, True)
        self.assertEqual(backup.read_bytes(), before)
        self.assertEqual(state_path.read_bytes(), state_before)
        for name, target in legacy.items():
            self.assertEqual(os.readlink(self.user / name), target)
        self.assertFalse((self.user / '.agents/skills/boost').is_symlink())


if __name__ == '__main__':
    unittest.main()
