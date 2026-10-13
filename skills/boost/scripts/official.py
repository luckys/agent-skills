"""Install reviewed upstream skills through the official skills CLI."""
from __future__ import annotations

import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

import resources as r

SOURCES = [('personal', 'luckys/agent-skills', '.', 0)]
REPO = re.compile(r'^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$')


def prepare(registry_path):
    """Refresh review checkouts; these are never project installation sources."""
    with tempfile.TemporaryDirectory(prefix='boost-catalog-') as temporary:
        path = Path(temporary) / 'sources.json'
        r.write_json(path, {'version': 1, 'sources': []})
        for source_id, repository, subdirectory, priority in SOURCES:
            source = r.fetch_source(repository, path, source_id=source_id, subdirectory=subdirectory)
            current = r.read_json(path)
            current['sources'][-1]['priority'] = priority
            r.write_json(path, current)
        result = r.read_json(path)
    r.write_json(registry_path, result)
    return {'registry': str(registry_path), 'sources': [s['id'] for s in result['sources']],
            'installation': 'pnpx skills add <repository> --skill <name>'}


def command(repository, name, clients):
    if not REPO.fullmatch(repository) or not r.NAME.fullmatch(name):
        raise ValueError('Use an upstream owner/repository and a portable skill name.')
    agents = sorted(set(clients) & {'codex', 'opencode'}) or ['codex']
    return ['pnpx', 'skills', 'add', repository, '--skill', name, '--agent', *agents, '--yes', '--json']


def cli_lock(project):
    path = project / 'skills-lock.json'
    r.check_parent(path, project)
    if path.is_symlink():
        raise ValueError('The official skills lock must not be a symlink.')
    data = r.read_json(path) if path.exists() else {'version': 1, 'skills': {}}
    if data.get('version') != 1 or not isinstance(data.get('skills'), dict):
        raise ValueError('Unsupported official skills lock; preserve it and reconcile manually.')
    return path, data


def package_path(item):
    return r.DATA / 'installed-skills' / item['repository'].replace('/', '--') / item['name'] / item['sha256']


def cache_package(item, stage):
    destination = package_path(item)
    if destination.exists():
        if r.fingerprint(destination, destination.parent) != item['sha256']:
            raise ValueError(f'Downloaded package was modified; preserve it and reconcile: {destination}')
        return
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.package-', dir=destination.parent) as temporary:
        prepared = Path(temporary) / 'bundle'
        shutil.copytree(stage / item['destination'], prepared)
        prepared.rename(destination)


def plan(project, selection, registry):
    clients = selection.get('clients', sorted(r.CLIENTS))
    if not clients or not set(clients) <= r.CLIENTS:
        raise ValueError('Select at least one known client.')
    candidates, warnings = r.catalog(registry)
    lookup = {item['id']: item for item in candidates}
    lock_path, previous = r.project_lock(project)
    _, official_lock = cli_lock(project)
    owned = {item['destination']: item for item in previous['resources']}
    requested = selection.get('resources', [])
    if not requested:
        raise ValueError('Selection is empty.')
    selected, names = [], set()
    for entry in requested:
        item = lookup.get(entry.get('id'))
        if item is None or item['kind'] != 'skill':
            raise ValueError('install accepts reviewed portable skills; use link separately for native profiles.')
        repository = item.get('repository')
        if not repository or not REPO.fullmatch(repository):
            raise ValueError(f'No upstream repository for {item["id"]}; refresh the official catalog instead of installing a local copy.')
        if entry.get('reviewed_sha256') != item['sha256'] or not str(entry.get('reason', '')).strip():
            raise ValueError(f'Content changed or not reviewed with a rationale: {item["id"]}')
        if item['name'] in names:
            raise ValueError('Resolve overlapping skill names before installation.')
        names.add(item['name'])
        destination = '.agents/skills/' + item['name']
        path = project / destination
        r.check_parent(path, project)
        old = owned.get(destination)
        action, is_owned = 'create', True
        if path.is_symlink():
            if not old or not old.get('owned') or str(path.resolve()) != str(Path(old['target']).resolve()):
                raise ValueError(f'Foreign symlink collision: {path}')
            if old.get('installation') == 'skills-cli' and str(path.resolve()) == str(package_path(item).resolve()) and r.fingerprint(path.resolve(), package_path(item).parent) == item['sha256']:
                action = 'keep'
            else:
                action = 'replace-owned'
        elif path.exists():
            if not path.is_dir():
                raise ValueError(f'Existing user file collision: {path}')
            actual = r.fingerprint(path, project)
            registered = official_lock['skills'].get(item['name'], {}).get('source') == repository
            managed = old and old.get('installation') == 'skills-cli'
            if managed and old.get('owned') and actual == old['sha256']:
                action = 'replace-owned'
            else:
                raise ValueError(f'Existing or user-modified skill collision: {path}')
        recorded_source = official_lock['skills'].get(item['name'], {}).get('source')
        if old and old.get('installation') == 'skills-cli' and recorded_source != old.get('repository'):
            raise ValueError(f'User changed the official CLI source record: {item["name"]}')
        if recorded_source and recorded_source != repository and not (old and old.get('owned')):
            raise ValueError(f'Official lock source collision: {item["name"]}')
        selected.append({**item, 'destination': destination, 'target': str(package_path(item)), 'source_root': str(package_path(item).parent),
                         'review_source': item['path'], 'installation': 'skills-cli', 'reason': entry['reason'],
                         'owned': is_owned, 'action': action, 'command': command(repository, item['name'], clients)})
    if r.inspect_project(project)['frontend']['detected'] and not any(item['name'] == 'frontend-design' and item['repository'] in {'luckys/agent-skills', 'anthropics/skills'} for item in selected):
        omitted = selection.get('omissions', {}).get('frontend-design', '')
        if not isinstance(omitted, str) or not omitted.strip():
            raise ValueError('UI project detected: review and select anthropics/skills frontend-design, or document a concrete omission reason.')
    return {'project': str(project), 'plan': selected, 'warnings': warnings}, lock_path, previous


def download(item, stage):
    completed = subprocess.run(item['command'], cwd=stage, stdin=subprocess.DEVNULL,
                               capture_output=True, text=True, timeout=120)
    if completed.returncode:
        raise ValueError(f'Official CLI installation failed for {item["repository"]}:{item["name"]} (exit {completed.returncode}); no project resources changed.')
    try:
        receipts = json.loads(completed.stdout)
    except ValueError as exc:
        raise ValueError('The official CLI did not return JSON installation receipts.') from exc
    if not isinstance(receipts, list) or not any(entry.get('name') == item['name'] and entry.get('status') == 'installed' for entry in receipts):
        raise ValueError(f'The official CLI did not install {item["name"]}.')
    bundle = stage / item['destination']
    if bundle.is_symlink() or not bundle.is_dir() or r.fingerprint(bundle, stage) != item['sha256']:
        raise ValueError(f'Upstream content changed since review: {item["id"]}. Refresh and review before retrying.')
    _, metadata = cli_lock(stage)
    if metadata['skills'].get(item['name'], {}).get('source') != item['repository']:
        raise ValueError('The official CLI receipt has an unexpected repository source.')
    return metadata['skills'][item['name']]


def install(project, selection, registry, apply=False):
    preview, _, _ = plan(project, selection, registry)
    if not apply:
        return {**preview, 'apply': False}
    if not shutil.which('pnpx'):
        raise ValueError('pnpx is required to install upstream skills.')
    with tempfile.TemporaryDirectory(prefix='boost-official-') as temporary:
        stage = Path(temporary)
        receipts = {}
        for item in preview['plan']:
            if item['action'] != 'keep':
                receipts[item['name']] = download(item, stage)
                cache_package(item, stage)
        with r.locked_project(project):
            current, lock_path, previous = plan(project, selection, registry)
            official_path, official_lock = cli_lock(project)
            lock_bytes = lock_path.read_bytes() if lock_path.exists() else None
            official_bytes = official_path.read_bytes() if official_path.exists() else None
            journal = []
            with tempfile.TemporaryDirectory(prefix='.boost-publish-', dir=project / '.agents') as publishing:
                publishing = Path(publishing)
                try:
                    for item in current['plan']:
                        if item['action'] == 'keep':
                            continue
                        bundle = package_path(item)
                        if not bundle.is_dir() or r.fingerprint(bundle, bundle.parent) != item['sha256']:
                            raise ValueError('Project changed during download; retry from a fresh preview.')
                        (publishing / item['name']).symlink_to(bundle, target_is_directory=True)
                    for item in current['plan']:
                        if item['action'] == 'keep':
                            continue
                        dest = project / item['destination']
                        dest.parent.mkdir(parents=True, exist_ok=True)
                        backup = publishing / ('old-' + item['name'])
                        if dest.exists() or dest.is_symlink():
                            dest.rename(backup)
                            journal.append((dest, backup))
                        else:
                            journal.append((dest, None))
                        (publishing / item['name']).rename(dest)
                    merged = {item['destination']: item for item in previous['resources']}
                    for item in current['plan']:
                        merged[item['destination']] = {k: v for k, v in item.items() if k not in {'action', 'path', 'description', 'priority', 'clients', 'format', 'review_source'}}
                        if item['name'] in receipts:
                            official_lock['skills'][item['name']] = receipts[item['name']]
                    r.write_json(official_path, official_lock)
                    r.write_json(lock_path, {'version': 1, 'clients': selection.get('clients', sorted(r.CLIENTS)),
                                            'resources': list(merged.values()), 'notes': selection.get('notes', []),
                                            'omissions': selection.get('omissions', {})})
                except BaseException:
                    for dest, backup in reversed(journal):
                        if dest.is_symlink(): dest.unlink()
                        elif dest.exists(): shutil.rmtree(dest)
                        if backup is not None: backup.rename(dest)
                    for path, contents in [(official_path, official_bytes), (lock_path, lock_bytes)]:
                        if contents is None: path.unlink(missing_ok=True)
                        else: path.write_bytes(contents)
                    raise
    return {**current, 'apply': True}


def remove(project, lock_path, lock, apply=False):
    official_path, official_lock = cli_lock(project)
    planned = []
    for item in lock['resources']:
        if not item.get('owned'):
            continue
        path = project / item['destination']
        r.check_parent(path, project)
        if item.get('installation') == 'skills-cli':
            if not path.is_symlink() or str(path.resolve()) != str(Path(item['target']).resolve()) or not path.is_dir() or r.fingerprint(path.resolve(), Path(item['source_root'])) != item['sha256']:
                raise ValueError(f'User changed upstream skill; will not remove it: {path}')
            if official_lock['skills'].get(item['name'], {}).get('source') != item['repository']:
                raise ValueError(f'Official CLI source changed; preserve it: {item["name"]}')
        elif not path.is_symlink() or str(path.resolve()) != str(Path(item['target']).resolve()):
            raise ValueError(f'User changed managed link; will not remove it: {path}')
        planned.append((path, item))
    if apply:
        original_lock = lock_path.read_bytes()
        original_official = official_path.read_bytes() if official_path.exists() else None
        moved = []
        with tempfile.TemporaryDirectory(prefix='.boost-remove-', dir=project / '.agents') as temporary:
            try:
                for index, (path, item) in enumerate(planned):
                    backup = Path(temporary) / str(index)
                    path.rename(backup)
                    moved.append((path, backup))
                    if item.get('installation') == 'skills-cli':
                        official_lock['skills'].pop(item['name'], None)
                r.write_json(official_path, official_lock)
                updated = {**lock, 'resources': [item for item in lock['resources'] if not item.get('owned')]}
                r.write_json(lock_path, updated)
            except BaseException:
                for path, backup in reversed(moved): backup.rename(path)
                lock_path.write_bytes(original_lock)
                if original_official is None: official_path.unlink(missing_ok=True)
                else: official_path.write_bytes(original_official)
                raise
    return {'apply': apply, 'links': [str(path.relative_to(project)) for path, _ in planned]}
