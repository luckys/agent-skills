#!/usr/bin/env python3
"""Discover and link reviewed project resources without executing their code."""
from __future__ import annotations

import argparse
from contextlib import contextmanager
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

import yaml

CLIENTS = {"codex", "opencode", "antigravity"}
SKIP = {".git", "node_modules", ".venv", "venv", "__pycache__", ".next", ".nuxt", "dist", "build", "target", "vendor", ".cache"}
NAME = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
REPOSITORY = Path(__file__).resolve().parents[3]
DATA = Path(os.environ.get("XDG_DATA_HOME", str(Path.home() / ".local/share"))) / "agent-resources"
REGISTRY = Path.home() / ".agents/resource-sources.json"
REMOTE_REGISTRY = DATA / 'remote-sources.json'
UI_FRAMEWORKS = {'react', 'react-dom', 'next', 'vue', 'nuxt', 'svelte', '@sveltejs/kit',
                 '@angular/core', 'solid-js', 'astro', 'preact', '@builder.io/qwik'}
LANGUAGES = {'.ts': 'TypeScript', '.tsx': 'TypeScript', '.js': 'JavaScript', '.jsx': 'JavaScript',
             '.py': 'Python', '.go': 'Go', '.rs': 'Rust', '.php': 'PHP', '.rb': 'Ruby',
             '.java': 'Java', '.kt': 'Kotlin', '.cs': 'C#', '.dart': 'Dart', '.html': 'HTML',
             '.css': 'CSS', '.scss': 'SCSS', '.sql': 'SQL', '.sh': 'Shell'}


def read_json(path):
    return json.loads(Path(path).read_text())


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=".resource-", dir=path.parent)
    try:
        with os.fdopen(fd, "w") as stream:
            json.dump(value, stream, indent=2, ensure_ascii=False)
            stream.write("\n")
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def frontmatter(path):
    text = path.read_text()
    if not text.startswith("---\n"):
        return {}
    parts = text.split("---", 2)
    if len(parts) != 3:
        raise ValueError("Unclosed YAML frontmatter")
    metadata = yaml.safe_load(parts[1]) or {}
    if not isinstance(metadata, dict):
        raise ValueError("Frontmatter must be a mapping")
    return metadata


def inside(path, boundary):
    return path.resolve().is_relative_to(boundary.resolve())


def fingerprint(path, boundary):
    if not inside(path, boundary):
        raise ValueError(f"Resource escapes its source: {path}")
    digest = hashlib.sha256()
    if path.is_file():
        return hashlib.sha256(path.read_bytes()).hexdigest()
    for current, dirs, files in os.walk(path, followlinks=False):
        dirs[:] = sorted(d for d in dirs if d not in SKIP)
        for directory in dirs:
            candidate = Path(current) / directory
            if candidate.is_symlink():
                raise ValueError(f"Directory symlink inside resource requires adaptation: {candidate}")
        for name in sorted(files):
            candidate = Path(current) / name
            if name.endswith((".pyc", ".pyo")):
                continue
            if not inside(candidate, boundary):
                raise ValueError(f"Supporting file escapes source: {candidate}")
            digest.update(str(candidate.relative_to(path)).encode())
            digest.update(b"\0")
            digest.update(candidate.read_bytes())
            digest.update(b"\0")
    return digest.hexdigest()


def load_registry(path):
    if path.exists():
        return read_json(path)
    return {"version": 1, "sources": []}


def search_command(query, owner=None):
    command = ['pnpx', 'skills', 'find', query]
    if owner:
        if not re.fullmatch(r'[A-Za-z0-9-]+', owner):
            raise ValueError('Use a valid GitHub owner for the skills.sh search.')
        command.extend(['--owner', owner])
    return command


def catalog(registry):
    resources, warnings = [], []
    formats = {"skill": sorted(CLIENTS), "antigravity-agent": ["antigravity"], "codex-agent": ["codex"],
               "opencode-agent": ["opencode"], "opencode-command": ["opencode"], "reference-workflow": sorted(CLIENTS)}
    for source in registry["sources"]:
        root = Path(source["path"]).expanduser().resolve()
        if not root.is_dir():
            warnings.append(f"Source unavailable: {source['id']} ({root})")
            continue
        candidates = [(p, "skill", "skill") for p in root.rglob("SKILL.md") if not any(part in SKIP for part in p.relative_to(root).parts)]
        directories = [(source.get("agent_directory", "agents"), "agent", source.get("agent_format", "claude-agent")),
                       (".agents/agents", "agent", "antigravity-agent"), (".opencode/agents", "agent", "opencode-agent"),
                       (".codex/agents", "agent", "codex-agent"),
                       (source.get("command_directory", "commands"), "workflow", source.get("command_format", "gemini-command")),
                       ("workflows", "workflow", "reference-workflow")]
        for directory, kind, format_name in directories:
            candidates.extend((p, kind, format_name) for p in sorted((root / directory).glob("*")) if p.is_file() and p.suffix in {".md", ".toml"})
        seen = set()
        for path, kind, format_name in candidates:
            if kind not in source.get('kinds', ['skill', 'agent', 'workflow']):
                continue
            try:
                meta = frontmatter(path) if path.suffix == ".md" else {}
                name = str(meta.get("name", path.parent.name)) if kind == "skill" else path.stem
                if not NAME.fullmatch(name) or len(name) > 64 or (kind == "skill" and not meta.get("description")):
                    raise ValueError("Invalid portable resource name or skill description")
                target = path.parent if kind == "skill" else path
                rid = f"{source['id']}:{kind}:{name}"
                if rid in seen:
                    rid = f"{rid}:{format_name}"
                    if rid in seen:
                        raise ValueError("Duplicate resource ID in source and format")
                seen.add(rid)
                resources.append({"id": rid, "name": name, "kind": kind, "format": format_name,
                                  "description": str(meta.get("description", name)), "path": str(target),
                                  "source_root": str(root), "source": source['id'], "revision": source.get("revision", "local"),
                                  "repository": source.get("repository"), "priority": source.get("priority", 10),
                                  "clients": formats.get(format_name, []), "sha256": fingerprint(target, root)})
            except (ValueError, OSError, yaml.YAMLError) as exc:
                warnings.append(f"{source['id']}:{path.relative_to(root)}: {exc}")
    resources.sort(key=lambda item: (item['priority'], item['name'], item['id']))
    return resources, warnings


def inspect_project(project):
    facts = {"project": str(project), "manifests": [], "scripts": {}, "dependencies": {}, "extensions": {}, "instructions": [],
             'toolchains': {}, 'resolved_versions': {}, 'lockfiles_not_parsed': []}
    visited = 0
    for current, dirs, files in os.walk(project, followlinks=False):
        depth = len(Path(current).relative_to(project).parts)
        dirs[:] = sorted(d for d in dirs if d not in SKIP and not d.startswith('.') and not (Path(current) / d).is_symlink()) if depth < 4 else []
        for name in sorted(files):
            path = Path(current) / name
            if not path.is_symlink() and name in {'.nvmrc', '.node-version', '.python-version', '.ruby-version'}:
                value = path.read_text().strip()
                if re.fullmatch(r'[A-Za-z0-9/._*-]{1,80}', value):
                    facts['toolchains'][str(path.relative_to(project))] = value
            if path.is_symlink() or name.startswith('.'):
                continue
            if name in {"AGENTS.md", "CLAUDE.md", "GEMINI.md"}:
                facts['instructions'].append(str(path.relative_to(project)))
            if name in {"package.json", "pyproject.toml", "requirements.txt", "Cargo.toml", "go.mod", "pom.xml", "build.gradle", "composer.json", "Gemfile"}:
                facts['manifests'].append(str(path.relative_to(project)))
            if name == "package.json":
                data = read_json(path)
                key = str(path.relative_to(project))
                facts['scripts'][key] = sorted(data.get('scripts', {}))
                deps = {**data.get('peerDependencies', {}), **data.get('dependencies', {}), **data.get('devDependencies', {})}
                facts['dependencies'][key] = {k: v if isinstance(v, str) and re.fullmatch(r'[\d.^~*<>=| x-]+', v) else 'custom' for k, v in deps.items()}
                facts['toolchains'][key] = {k: v for k, v in data.get('engines', {}).items() if isinstance(v, str) and len(v) < 100 and not any(token in v for token in ['://', '@'])}
                manager = data.get('packageManager', '')
                if isinstance(manager, str) and re.fullmatch(r'[a-z]+@[0-9][A-Za-z0-9.+-]*', manager):
                    facts['toolchains'][key]['packageManager'] = manager
            if name in {'package-lock.json', 'pnpm-lock.yaml'}:
                key = str(path.relative_to(project))
                if path.stat().st_size > 4_000_000:
                    facts['lockfiles_not_parsed'].append(key)
                else:
                    lock = read_json(path) if name.endswith('.json') else yaml.safe_load(path.read_text()) or {}
                    facts['resolved_versions'][key] = resolved_node_versions(lock, name)
            if path.suffix:
                facts['extensions'][path.suffix] = facts['extensions'].get(path.suffix, 0) + 1
            visited += 1
            if visited >= 4000:
                facts['truncated'] = True
                return frontend_facts(facts)
    facts['truncated'] = False
    return frontend_facts(facts)


def frontend_facts(facts):
    packages = {path: sorted(set(dependencies) & UI_FRAMEWORKS)
                for path, dependencies in facts['dependencies'].items() if set(dependencies) & UI_FRAMEWORKS}
    extensions = facts['extensions']
    ui_files = any(extensions.get(suffix) for suffix in ['.vue', '.svelte', '.jsx', '.tsx', '.astro', '.html'])
    facts['frontend'] = {'packages': packages, 'detected': bool(packages or ui_files)}
    facts['languages'] = sorted({LANGUAGES[suffix] for suffix in facts['extensions'] if suffix in LANGUAGES})
    facts['recommended_skills'] = [{'repository': 'anthropics/skills', 'skill': 'frontend-design',
                                   'reason': 'Detected UI framework dependencies or user-facing component files.'}] if packages or ui_files else []
    return facts


def resolved_node_versions(lock, filename):
    result = {}
    def version(value):
        if not isinstance(value, str): return None
        match = re.match(r'^\d+(?:\.\d+){0,3}(?:[-+][A-Za-z0-9.-]+)?', value)
        return match.group() if match else None
    if filename == 'package-lock.json':
        packages = lock.get('packages', {})
        for key, value in packages.items():
            if 'node_modules/' in key and isinstance(value, dict) and version(value.get('version')):
                result[key] = version(value['version'])
        if not packages:
            for name, value in lock.get('dependencies', {}).items():
                if isinstance(value, dict) and version(value.get('version')):
                    result[name] = version(value['version'])
    else:
        for importer, data in lock.get('importers', {}).items():
            dependencies = {**data.get('dependencies', {}), **data.get('devDependencies', {}), **data.get('optionalDependencies', {})}
            for name, value in dependencies.items():
                resolved = version(value.get('version') if isinstance(value, dict) else value)
                if resolved:
                    result[importer + ':' + name] = resolved
    return result


def destination(resource, project, clients):
    name, format_name = resource['name'], resource['format']
    if not set(resource['clients']) & set(clients):
        raise ValueError(f"No compatible client for {resource['id']}; adapt it before installation.")
    paths = {"skill": project / '.agents/skills' / name,
             "antigravity-agent": project / '.agents/agents' / f'{name}.md',
             "codex-agent": project / '.codex/agents' / f'{name}.toml',
             "opencode-agent": project / '.opencode/agents' / f'{name}.md',
             "opencode-command": project / '.opencode/commands' / f'{name}.md',
             "reference-workflow": project / '.agents/workflows' / f'{name}{Path(resource["path"]).suffix}'}
    if format_name not in paths:
        raise ValueError(f"Unsupported resource format: {format_name}")
    return paths[format_name]


def project_root(value):
    project = Path(value).expanduser().resolve()
    if not project.is_dir():
        raise ValueError("Project directory does not exist.")
    if project in {Path('/'), Path.home().resolve()}:
        raise ValueError("Choose an actual project, not the home or filesystem root.")
    return project


def check_parent(path, project):
    if not inside(path.parent, project):
        raise ValueError(f"Destination parent escapes project through a symlink: {path.parent}")
    for ancestor in [path.parent, *path.parent.parents]:
        if ancestor == project.parent:
            break
        if ancestor.exists() and not ancestor.is_dir():
            raise ValueError(f"Destination parent is not a directory: {ancestor}")


def project_lock(project):
    path = project / '.agents/resource-lock.json'
    check_parent(path, project)
    if path.is_symlink():
        raise ValueError("Resource lock must not be a symlink.")
    if path.exists():
        data = read_json(path)
        if data.get('version') != 1 or not isinstance(data.get('resources'), list):
            raise ValueError("Unsupported project resource lock; preserve it and resolve manually.")
        return path, data
    return path, {"version": 1, "resources": []}


@contextmanager
def locked_project(project):
    lock_path = project / '.agents/.resource-operation.lock'
    check_parent(lock_path, project)
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(lock_path, os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600)
    with os.fdopen(descriptor, 'w') as stream:
        fcntl.flock(stream, fcntl.LOCK_EX)
        yield


def install(project, selection, registry, apply=False):
    preview = _install(project, selection, registry, False)
    if not apply:
        return preview
    with locked_project(project):
        return _install(project, selection, registry, True)


def _install(project, selection, registry, apply=False):
    clients = selection.get('clients', sorted(CLIENTS))
    if not clients or not set(clients) <= CLIENTS:
        raise ValueError("Select at least one known client.")
    items, warnings = catalog(registry)
    lookup = {item['id']: item for item in items}
    lock_path, previous = project_lock(project)
    old = {item['destination']: item for item in previous['resources']}
    planned, destinations, identities = [], set(), set()
    for requested in selection.get('resources', []):
        resource = lookup.get(requested.get('id'))
        if resource is None:
            raise ValueError(f"Unknown resource: {requested.get('id')}")
        if requested.get('reviewed_sha256') != resource['sha256']:
            raise ValueError(f"Content changed or not reviewed: {resource['id']}")
        if not str(requested.get('reason', '')).strip():
            raise ValueError(f"Selection needs evidence/rationale: {resource['id']}")
        identity = (resource['kind'], resource['name'], resource['format'])
        if identity in identities:
            raise ValueError(f"Resolve overlapping resource names: {identity}")
        identities.add(identity)
        dest = destination(resource, project, clients)
        check_parent(dest, project)
        relative = str(dest.relative_to(project))
        if relative in destinations:
            raise ValueError(f"Duplicate destination: {relative}")
        destinations.add(relative)
        target = resource['path']
        action, owned = 'create', True
        if dest.is_symlink():
            existing = str(dest.resolve())
            entry = old.get(relative)
            if existing == str(Path(target).resolve()):
                action, owned = 'keep', bool(entry and entry.get('owned'))
            elif entry and entry.get('owned') and existing == str(Path(entry['target']).resolve()):
                action = 'replace-owned'
            else:
                raise ValueError(f"Foreign symlink collision: {dest}")
        elif dest.exists():
            raise ValueError(f"Existing user file/directory collision: {dest}")
        planned.append({"id": resource['id'], "destination": relative, "target": target,
                        "sha256": resource['sha256'], "source_root": resource['source_root'],
                        "revision": resource['revision'], "reason": requested['reason'], "owned": owned, "action": action})
    if not planned:
        raise ValueError("Selection is empty; no resources installed.")
    if not apply:
        return {"project": str(project), "apply": False, "plan": planned, "warnings": warnings}
    journal, created_dirs = [], []
    try:
        for item in planned:
            dest = project / item['destination']
            if item['action'] == 'keep':
                continue
            missing, parent = [], dest.parent
            while not parent.exists():
                missing.append(parent)
                parent = parent.parent
            for directory in reversed(missing):
                directory.mkdir()
                created_dirs.append(directory)
            original = os.readlink(dest) if dest.is_symlink() else None
            if original is not None:
                journal.append((dest, original))
                dest.unlink()
            dest.symlink_to(item['target'], target_is_directory=Path(item['target']).is_dir())
            if original is None:
                journal.append((dest, None))
        combined = {item['destination']: item for item in previous['resources']}
        for item in planned:
            combined[item['destination']] = {k: v for k, v in item.items() if k != 'action'}
        write_json(lock_path, {"version": 1, "clients": clients, "resources": list(combined.values()), "notes": selection.get('notes', [])})
    except BaseException:
        for dest, original in reversed(journal):
            if dest.is_symlink():
                dest.unlink()
            if original is not None:
                dest.symlink_to(original)
        for directory in reversed(created_dirs):
            try:
                directory.rmdir()
            except OSError:
                pass
        raise
    return {"project": str(project), "apply": True, "plan": planned, "warnings": warnings}


def doctor(project):
    lock_path, lock = project_lock(project)
    issues = [] if lock_path.exists() else ['No project resource lock; bootstrap has not installed a selection.']
    for item in lock['resources']:
        dest = project / item['destination']
        check_parent(dest, project)
        if item.get('installation') == 'skills-cli':
            try:
                from official import cli_lock
                _, official = cli_lock(project)
                if not dest.is_symlink() or str(dest.resolve()) != str(Path(item['target']).resolve()) or not dest.is_dir():
                    issues.append(f'Missing or modified upstream skill: {item["destination"]}')
                elif fingerprint(dest.resolve(), Path(item['source_root'])) != item['sha256']:
                    issues.append(f'Content changed since review: {item["id"]}')
                if official['skills'].get(item['name'], {}).get('source') != item['repository']:
                    issues.append(f'Official CLI source changed or missing: {item["name"]}')
            except (ValueError, OSError) as exc:
                issues.append(str(exc))
            continue
        if not dest.is_symlink() or str(dest.resolve()) != str(Path(item['target']).resolve()) or not dest.exists():
            issues.append(f"Missing, broken, or modified link: {item['destination']}")
            continue
        try:
            if fingerprint(Path(item['target']), Path(item['source_root'])) != item['sha256']:
                issues.append(f"Content changed since review: {item['id']}")
        except (ValueError, OSError) as exc:
            issues.append(str(exc))
    return {"project": str(project), "resources": len(lock['resources']), "issues": issues, "ok": not issues}


def uninstall(project, apply=False):
    preview = _uninstall(project, False)
    if not apply:
        return preview
    with locked_project(project):
        return _uninstall(project, True)


def _uninstall(project, apply=False):
    path, lock = project_lock(project)
    if any(item.get('installation') == 'skills-cli' for item in lock['resources']):
        from official import remove
        return remove(project, path, lock, apply)
    planned = []
    for item in lock['resources']:
        if not item.get('owned'):
            continue
        dest = project / item['destination']
        check_parent(dest, project)
        if not dest.is_symlink() or str(dest.resolve()) != str(Path(item['target']).resolve()):
            raise ValueError(f"User changed managed link; will not remove it: {dest}")
        planned.append((dest, os.readlink(dest)))
    if apply:
        removed = []
        try:
            for dest, target in planned:
                dest.unlink()
                removed.append((dest, target))
            lock['resources'] = [item for item in lock['resources'] if not item.get('owned')]
            write_json(path, lock)
        except BaseException:
            for dest, target in reversed(removed):
                dest.symlink_to(target)
            raise
    return {"apply": apply, "links": [str(dest.relative_to(project)) for dest, _ in planned]}


def fetch_source(repository, registry_path, ref=None, source_id=None, subdirectory=None):
    if not re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+', repository):
        raise ValueError('Use a public GitHub owner/repository without embedded credentials.')
    if ref and not re.fullmatch(r'[a-fA-F0-9]{40}', ref):
        raise ValueError('An explicit revision must be a full 40-character commit SHA.')
    source_id = source_id or repository.lower().replace('/', '-')
    if not NAME.fullmatch(source_id):
        raise ValueError('Source ID must be lowercase words separated by hyphens.')
    registry = load_registry(registry_path)
    if any(item['id'] == source_id and item.get('repository') != repository for item in registry['sources']):
        raise ValueError('Source ID already belongs to another repository or local source.')
    previous = next((item for item in registry['sources'] if item['id'] == source_id), {})
    if subdirectory is None:
        subdirectory = previous.get('subdirectory')
        if subdirectory is None and previous.get('revision'):
            previous_checkout = DATA / 'sources' / source_id / previous['revision']
            previous_path = Path(previous['path'])
            if previous_path.is_relative_to(previous_checkout):
                subdirectory = str(previous_path.relative_to(previous_checkout))
    subdirectory = subdirectory or '.'
    relative = Path(subdirectory)
    if relative.is_absolute() or '..' in relative.parts:
        raise ValueError('Source subdirectory must stay within the repository.')
    DATA.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='fetch-', dir=DATA) as temporary:
        checkout = Path(temporary) / 'repo'
        subprocess.run(['git', '-c', 'core.hooksPath=/dev/null', 'clone', '--quiet', '--depth', '1', f'https://github.com/{repository}.git', str(checkout)], check=True, timeout=120)
        if ref:
            subprocess.run(['git', '-c', 'core.hooksPath=/dev/null', '-C', str(checkout), 'fetch', '--quiet', '--depth', '1', 'origin', ref], check=True, timeout=120)
            subprocess.run(['git', '-c', 'core.hooksPath=/dev/null', '-C', str(checkout), 'checkout', '--quiet', '--detach', 'FETCH_HEAD'], check=True, timeout=30)
        sha = subprocess.check_output(['git', '-C', str(checkout), 'rev-parse', 'HEAD'], text=True).strip()
        destination_path = DATA / 'sources' / source_id / sha
        destination_path.parent.mkdir(parents=True, exist_ok=True)
        if not destination_path.exists():
            shutil.move(str(checkout), destination_path)
    source_path = destination_path / relative
    if not source_path.is_dir() or not inside(source_path, destination_path):
        raise ValueError('Source subdirectory is missing or escapes the cached checkout.')
    source = {**previous, "id": source_id, "repository": repository, "path": str(source_path),
              "subdirectory": str(relative), "revision": sha, "priority": previous.get('priority', 20)}
    registry['sources'] = [item for item in registry['sources'] if item['id'] != source_id] + [source]
    write_json(registry_path, registry)
    return source


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--registry', type=Path, default=REMOTE_REGISTRY)
    commands = parser.add_subparsers(dest='command', required=True)
    for name in ['inspect', 'doctor', 'unlink']:
        child = commands.add_parser(name)
        child.add_argument('--project', default=str(Path.cwd()))
        if name == 'unlink':
            child.add_argument('--apply', action='store_true')
    child = commands.add_parser('catalog')
    child.add_argument('--query', default='')
    child.add_argument('--limit', type=int, default=25)
    child = commands.add_parser('search')
    child.add_argument('query')
    child.add_argument('--owner', help='Restrict skills.sh search to this GitHub owner.')
    commands.add_parser('prepare')
    child = commands.add_parser('fetch')
    child.add_argument('repository')
    child.add_argument('--ref')
    child.add_argument('--id')
    child.add_argument('--subdir', help='Limit a repository source to this relative directory.')
    for name in ['install', 'link']:
        child = commands.add_parser(name)
        child.add_argument('--project', default=str(Path.cwd()))
        child.add_argument('--selection', type=Path, required=True)
        child.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    try:
        registry = load_registry(args.registry)
        if args.command == 'inspect':
            result = inspect_project(project_root(args.project))
        elif args.command == 'catalog':
            items, warnings = catalog(registry)
            terms = args.query.lower().split()
            matches = [item for item in items if all(term in (item['name'] + ' ' + item['description'] + ' ' + item['source']).lower() for term in terms)]
            result = {"resources": matches[:max(args.limit, 0)], "matching": len(matches), "total": len(items), "warnings": warnings}
        elif args.command == 'search':
            subprocess.run(search_command(args.query, args.owner), check=True, timeout=60, stdin=subprocess.DEVNULL)
            return
        elif args.command == 'prepare':
            from official import prepare
            result = prepare(args.registry)
        elif args.command == 'fetch':
            result = fetch_source(args.repository, args.registry, args.ref, args.id, args.subdir)
        elif args.command == 'link':
            selected = read_json(args.selection)
            native_only(selected, registry)
            result = install(project_root(args.project), selected, registry, args.apply)
        elif args.command == 'install':
            from official import install as install_official
            result = install_official(project_root(args.project), read_json(args.selection), registry, args.apply)
        elif args.command == 'doctor':
            result = doctor(project_root(args.project))
        else:
            result = uninstall(project_root(args.project), args.apply)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        if args.command == 'doctor' and not result['ok']:
            raise SystemExit(1)
    except (ValueError, OSError, subprocess.SubprocessError) as exc:
        print(f'Error: {exc}', file=sys.stderr)
        raise SystemExit(1)


def native_only(selection, registry):
    items, _ = catalog(registry)
    lookup = {item['id']: item for item in items}
    if any(lookup.get(item.get('id'), {}).get('kind') == 'skill' for item in selection.get('resources', [])):
        raise ValueError('Portable skills must use install and pnpx skills add from their upstream repository; link is only for native profiles and reference workflows.')


if __name__ == '__main__':
    main()
