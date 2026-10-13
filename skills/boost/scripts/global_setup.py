#!/usr/bin/env python3
"""Retire manually installed globals into a reversible local library."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess

from resources import DATA, REPOSITORY, write_json

UPSTREAM = {
    'mattpocock': ('mattpocock/skills', '49dd158d1076134a641b33efb035946536778336', ''),
    'addyosmani': ('addyosmani/agent-skills', '1be8e34187e34647bb83adc3a1323b26ae6f6abe', ''),
    'pstack': ('cursor/plugins', '11713c683fe4add4fd403ea880580abbc9e0875f', 'pstack'),
}


def global_links(user_root, repository):
    links = {
        '.agents/skills/boost': repository / 'skills/boost',
        '.agents/skills/flow': repository / 'skills/flow',
        '.agents/agents/boost.md': repository / 'agents/boost.md',
        '.agents/adapters/codex': repository / 'adapters/codex',
        '.agents/adapters/opencode': repository / 'adapters/opencode',
        '.codex/agents/boost.toml': user_root / '.agents/adapters/codex/boost.toml',
        '.config/opencode/agents/boost.md': user_root / '.agents/adapters/opencode/boost.md',
        '.config/opencode/commands/boost.md': user_root / '.agents/adapters/opencode/boost-command.md',
        '.config/opencode/commands/flow.md': user_root / '.agents/adapters/opencode/flow-command.md',
        '.gemini/antigravity-cli/skills': user_root / '.agents/skills',
        '.gemini/config/agents': user_root / '.agents/agents',
    }
    discovery = user_root / '.agents/library/find-skills'
    if discovery.is_symlink():
        links['.agents/library/find-skills'] = discovery.resolve()
        links['.agents/skills/find-skills'] = discovery
    return links


def originals(user_root):
    entries = []
    for directory, archive_directory in [('.agents/skills', 'skills'), ('.claude/skills', 'claude-aliases'),
                                         ('.config/opencode/agents', 'agents'), ('.config/opencode/commands', 'commands')]:
        path = user_root / directory
        if path.is_symlink():
            entries.append({'original': directory, 'archive': f'directory-links/{archive_directory}',
                            'directory_link': True, 'source_path': str(path.resolve())})
            continue
        if path.is_dir():
            entries.extend({'original': str(child.relative_to(user_root)), 'archive': f'{archive_directory}/{child.name}'} for child in sorted(path.iterdir()))
    for name in ['.agents/.skill-lock.json', '.agents/resource-sources.json']:
        path = user_root / name
        if path.exists() or path.is_symlink():
            entries.append({'original': name, 'archive': Path(name).name})
    return entries


def seed_sources(seed, data_root):
    sources = []
    for source_id, (repository, revision, subdirectory) in UPSTREAM.items():
        cached = data_root / 'sources' / source_id / revision
        if not cached.exists():
            origin = seed / ('cursor' if source_id == 'pstack' else source_id) if seed else None
            if origin is None or not origin.is_dir():
                raise ValueError(f'Pinned source missing: {source_id}. Fetch it or supply --seed with reviewed checkouts.')
            actual = subprocess.check_output(['git', '-C', str(origin), 'rev-parse', 'HEAD'], text=True).strip()
            if actual != revision:
                raise ValueError(f'Unexpected source revision for {source_id}')
            cached.parent.mkdir(parents=True, exist_ok=True)
            temporary = cached.with_name(cached.name + '.preparing')
            try:
                shutil.copytree(origin, temporary, symlinks=True)
                temporary.rename(cached)
            finally:
                if temporary.exists():
                    shutil.rmtree(temporary)
        sources.append({'id': source_id, 'repository': repository, 'path': str(cached / subdirectory), 'revision': revision, 'priority': 10})
    return sources


def setup(user_root, repository, data_root, seed=None, apply=False):
    state_path = user_root / '.agents/global-setup.json'
    links = global_links(user_root, repository)
    if state_path.exists():
        state = json.loads(state_path.read_text())
        if all((user_root / name).is_symlink() and os.readlink(user_root / name) == str(target) for name, target in links.items()):
            actual_skills = {path.name for path in (user_root / '.agents/skills').iterdir()}
            expected_skills = {Path(name).name for name in links if name.startswith('.agents/skills/')}
            if actual_skills != expected_skills:
                raise ValueError('Extra global skills appeared; review them before migrating again.')
            return {'status': 'already configured', 'backup': state['backup']}
        raise ValueError('Existing managed global setup has changed; inspect it before migrating again.')
    entries = originals(user_root)
    retiring = {entry['original'] for entry in entries}
    for name in links:
        path = user_root / name
        if (path.exists() or path.is_symlink()) and name not in retiring:
            raise ValueError(f'Existing global resource collision: {path}')
        current = path.parent
        while current != user_root:
            if current.is_symlink() and str(current.relative_to(user_root)) not in retiring:
                raise ValueError(f'Global parent symlink needs review: {current}')
            current = current.parent
    if not apply:
        return {'retire': entries, 'links': {name: str(target) for name, target in links.items()}, 'apply': False}
    sources = seed_sources(seed, data_root)
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    archive = data_root / 'library' / ('retired-' + stamp)
    archive.mkdir(parents=True)
    snapshot = {'version': 1, 'user_root': str(user_root), 'entries': entries, 'created_links': {}, 'created_dirs': [], 'generated_files': {}}
    write_json(archive / 'restore.json', snapshot)
    moved, created = [], []
    try:
        for entry in entries:
            original, saved = user_root / entry['original'], archive / entry['archive']
            saved.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(original), saved)
            moved.append((original, saved))
        for name, target in links.items():
            path = user_root / name
            missing, parent = [], path.parent
            while not parent.exists():
                missing.append(parent)
                parent = parent.parent
            path.parent.mkdir(parents=True, exist_ok=True)
            snapshot['created_dirs'].extend(str(directory.relative_to(user_root)) for directory in reversed(missing))
            path.symlink_to(target, target_is_directory=target.is_dir())
            created.append(path)
            snapshot['created_links'][name] = str(target)
        registry = {'version': 1, 'sources': [
            {'id': 'personal', 'path': str(repository), 'priority': 0, 'agent_format': 'antigravity-agent'},
            *sources,
            {'id': 'installed-library', 'path': str(archive), 'priority': 30, 'agent_format': 'opencode-agent', 'command_format': 'opencode-command'},
        ]}
        local_config = user_root / 'Software/ai-config-files'
        if local_config.is_dir():
            registry['sources'].append({'id': 'local-config', 'path': str(local_config), 'priority': 25, 'agent_format': 'opencode-agent', 'command_format': 'opencode-command'})
        for index, entry in enumerate(entries):
            if entry.get('directory_link'):
                source_path = Path(entry['source_path'])
                if any(source_path.is_relative_to(Path(source['path'])) for source in registry['sources']):
                    continue
                source = {'id': f'retired-directory-{index}', 'path': entry['source_path'], 'priority': 30}
                if entry['original'].endswith('/agents'):
                    source.update({'agent_directory': '.', 'agent_format': 'opencode-agent'})
                elif entry['original'].endswith('/commands'):
                    source.update({'command_directory': '.', 'command_format': 'opencode-command'})
                registry['sources'].append(source)
        old_lock_path = archive / '.skill-lock.json'
        skill_lock = json.loads(old_lock_path.read_text()) if old_lock_path.exists() else {'version': 3, 'skills': {}}
        skill_lock['skills'] = {}
        for name, data in {'.agents/resource-sources.json': registry, '.agents/.skill-lock.json': skill_lock}.items():
            path = user_root / name
            write_json(path, data)
            snapshot['generated_files'][name] = hashlib.sha256(path.read_bytes()).hexdigest()
        write_json(archive / 'restore.json', snapshot)
        write_json(state_path, {'version': 1, 'backup': str(archive / 'restore.json'), 'global_skills': ['boost', 'flow']})
    except BaseException:
        for name in snapshot['generated_files']:
            (user_root / name).unlink(missing_ok=True)
        for path in reversed(created):
            if path.is_symlink():
                path.unlink()
        for name in reversed(snapshot['created_dirs']):
            try:
                (user_root / name).rmdir()
            except OSError:
                pass
        for original, saved in reversed(moved):
            original.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(saved), original)
        raise
    return {'status': 'configured', 'retired': len(entries), 'global_skills': ['boost', 'flow'], 'backup': str(archive / 'restore.json')}


def upgrade_short_names(user_root, repository, apply=False):
    """Update owned global links while preserving the original restore manifest."""
    state_path = user_root / '.agents/global-setup.json'
    state_bytes = state_path.read_bytes()
    state = json.loads(state_bytes)
    snapshot_path = Path(state['backup'])
    snapshot_bytes = snapshot_path.read_bytes()
    snapshot = json.loads(snapshot_bytes)
    old_links = snapshot['created_links']
    links = {name: str(target) for name, target in global_links(user_root, repository).items()}
    for name, target in old_links.items():
        path = user_root / name
        if not path.is_symlink() or os.readlink(path) != target:
            raise ValueError(f'Managed global link changed: {path}')
    for name, expected in snapshot['generated_files'].items():
        path = user_root / name
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise ValueError(f'Managed global config changed: {path}')
    for name in links:
        path = user_root / name
        if name not in old_links and (path.exists() or path.is_symlink()):
            raise ValueError(f'Short-name collision: {path}')
    removed = {name: target for name, target in old_links.items() if links.get(name) != target}
    created = {name: target for name, target in links.items() if old_links.get(name) != target}
    if not removed and not created:
        return {'status': 'already configured', 'global_skills': ['boost', 'flow']}
    if not apply:
        return {'remove_links': removed, 'create_links': created, 'apply': False}
    checkpoint = snapshot_path.parent / 'before-short-names.json'
    if not checkpoint.exists():
        write_json(checkpoint, {'state': state, 'snapshot': snapshot})
    removed_done, created_done, created_dirs = [], [], []
    try:
        for name, target in removed.items():
            (user_root / name).unlink()
            removed_done.append((name, target))
        for name, target in created.items():
            path = user_root / name
            missing, parent = [], path.parent
            while not parent.exists():
                missing.append(parent)
                parent = parent.parent
            path.parent.mkdir(parents=True, exist_ok=True)
            created_dirs.extend(str(directory.relative_to(user_root)) for directory in reversed(missing))
            path.symlink_to(target)
            created_done.append(path)
        snapshot['created_links'] = links
        snapshot['created_dirs'].extend(created_dirs)
        write_json(snapshot_path, snapshot)
        state['global_skills'] = ['boost', 'flow']
        write_json(state_path, state)
    except BaseException:
        for path in reversed(created_done):
            path.unlink()
        for name in reversed(created_dirs):
            (user_root / name).rmdir()
        for name, target in reversed(removed_done):
            (user_root / name).symlink_to(target)
        snapshot_path.write_bytes(snapshot_bytes)
        state_path.write_bytes(state_bytes)
        raise
    return {'status': 'short names configured', 'global_skills': ['boost', 'flow'], 'backup': str(snapshot_path)}


def restore(snapshot_path, apply=False):
    snapshot = json.loads(snapshot_path.read_text())
    user_root = Path(snapshot['user_root'])
    for name, target in snapshot['created_links'].items():
        path = user_root / name
        if not path.is_symlink() or os.readlink(path) != target:
            raise ValueError(f'Global link changed; will not overwrite it: {path}')
    for name, expected in snapshot['generated_files'].items():
        path = user_root / name
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise ValueError(f'Global config changed; reconcile before restore: {path}')
    occupied = set(snapshot['created_links']) | set(snapshot['generated_files'])
    for entry in snapshot['entries']:
        path = user_root / entry['original']
        if entry.get('directory_link') and path.is_dir() and not path.is_symlink():
            if entry['original'] not in snapshot.get('created_dirs', []):
                raise ValueError(f'Restore directory is not owned: {path}')
            for child in path.iterdir():
                if str(child.relative_to(user_root)) not in occupied:
                    raise ValueError(f'Restore would replace a user directory entry: {child}')
        elif (path.exists() or path.is_symlink()) and entry['original'] not in occupied:
            raise ValueError(f'Restore collision: {path}')
        saved = snapshot_path.parent / entry['archive']
        if not saved.exists() and not saved.is_symlink():
            raise ValueError(f'Backup entry missing: {saved}')
    if apply:
        removed_links, removed_files, moved = [], {}, []
        try:
            for name, target in reversed(list(snapshot['created_links'].items())):
                (user_root / name).unlink()
                removed_links.append((name, target))
            for name in snapshot['generated_files']:
                path = user_root / name
                removed_files[name] = path.read_bytes()
                path.unlink()
            for name in reversed(snapshot.get('created_dirs', [])):
                try:
                    (user_root / name).rmdir()
                except OSError:
                    pass
            for entry in snapshot['entries']:
                target = user_root / entry['original']
                saved = snapshot_path.parent / entry['archive']
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(saved), target)
                moved.append((target, saved))
            (user_root / '.agents/global-setup.json').unlink(missing_ok=True)
        except BaseException:
            for target, saved in reversed(moved):
                shutil.move(str(target), saved)
            for name, data in removed_files.items():
                (user_root / name).parent.mkdir(parents=True, exist_ok=True)
                (user_root / name).write_bytes(data)
            for name, target in reversed(removed_links):
                (user_root / name).parent.mkdir(parents=True, exist_ok=True)
                (user_root / name).symlink_to(target)
            raise
    return {'restore': str(snapshot_path), 'entries': len(snapshot['entries']), 'apply': apply}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--user-root', type=Path, default=Path.home())
    parser.add_argument('--repository', type=Path, default=REPOSITORY)
    parser.add_argument('--data-root', type=Path, default=DATA)
    parser.add_argument('--seed', type=Path)
    parser.add_argument('--restore', type=Path)
    parser.add_argument('--upgrade-names', action='store_true')
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    try:
        if args.restore:
            result = restore(args.restore, args.apply)
        elif args.upgrade_names:
            result = upgrade_short_names(args.user_root.resolve(), args.repository.resolve(), args.apply)
        else:
            result = setup(args.user_root.resolve(), args.repository.resolve(), args.data_root.resolve(), args.seed, args.apply)
        print(json.dumps(result, indent=2))
    except (ValueError, OSError, subprocess.SubprocessError) as exc:
        parser.exit(1, f'Error: {exc}\n')


if __name__ == '__main__':
    main()
