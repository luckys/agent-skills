"""Evidence inventory and coverage checks for a complete project bootstrap."""
from __future__ import annotations

from pathlib import Path
import re

# These are discovery hints, not a prescribed stack or a list of skills to install.
PACKAGES = {
    'typescript': 'typescript', 'nuxt': 'nuxt', 'vue': 'vue', '@nuxt/ui': 'nuxt-ui',
    'tailwindcss': 'tailwind', 'better-auth': 'better-auth', 'drizzle-orm': 'drizzle',
    'drizzle-kit': 'drizzle', 'vitest': 'vitest', '@vue/test-utils': 'vue-testing',
    'pg': 'postgresql', 'react': 'react', 'next': 'next', 'svelte': 'svelte',
    '@sveltejs/kit': 'sveltekit', 'astro': 'astro', '@angular/core': 'angular',
    'prisma': 'prisma', '@prisma/client': 'prisma', 'express': 'express',
    'fastify': 'fastify', '@nestjs/core': 'nestjs', 'jest': 'jest',
    '@playwright/test': 'playwright', 'cypress': 'cypress', 'eslint': 'linting',
    '@nuxt/eslint': 'linting', 'oxlint': 'linting', 'axe-core': 'accessibility',
    'agent-browser': 'browser-testing', 'redis': 'redis', 'ioredis': 'redis',
    '@sentry/nuxt': 'sentry', '@sentry/node': 'sentry',
    '@opentelemetry/sdk-node': 'opentelemetry',
}
AREAS = ('requirements', 'architecture', 'implementation', 'testing', 'security',
         'ci', 'deployment', 'observability', 'operations', 'maintenance',
         'migrations', 'documentation')


def stack_snapshot(facts):
    packages = {name for dependencies in facts['dependencies'].values() for name in dependencies}
    resolved = {path: {key: value for key, value in versions.items()
                       if any(key.endswith(':' + package) or key.endswith('node_modules/' + package) or key == package for package in packages)}
                for path, versions in facts['resolved_versions'].items()}
    return {'dependencies': facts['dependencies'], 'resolved_versions': resolved,
            'toolchains': facts['toolchains'], 'languages': facts['languages']}


def augment(project, facts, paths):
    """Record evidence; an agent still reviews intent and semantic compatibility."""
    capabilities = {}
    def need(name, evidence):
        capabilities.setdefault(name, {'evidence': [], 'queries': [name.replace('-', ' ')]})['evidence'].append(evidence)

    for manifest, dependencies in facts['dependencies'].items():
        for package, declared in dependencies.items():
            if package in PACKAGES:
                parent = str(Path(manifest).parent)
                versions = {}
                for lock_path, resolved in facts['resolved_versions'].items():
                    if Path(lock_path).name == 'pnpm-lock.yaml':
                        importer = str(Path(parent).relative_to(Path(lock_path).parent)) if Path(parent).is_relative_to(Path(lock_path).parent) else None
                        if importer is not None and (importer + ':' + package) in resolved:
                            versions[lock_path] = resolved[importer + ':' + package]
                    else:
                        key = ('' if parent == '.' else parent + '/') + 'node_modules/' + package
                        if key in resolved or package in resolved:
                            versions[lock_path] = resolved.get(key, resolved.get(package))
                need(PACKAGES[package], {'path': manifest, 'package': package, 'declared': declared, 'resolved': versions})
        if 'nuxt' in dependencies and 'vue' not in dependencies:
            need('vue', {'path': manifest, 'reason': 'Nuxt uses Vue; inspect component and lockfile versions.'})

    for language in facts['languages']:
        if language not in {'HTML', 'CSS', 'SCSS', 'SQL', 'Shell', 'JavaScript'}:
            need(language.lower(), {'reason': 'Source files detected', 'language': language})
    if facts['frontend']['detected']:
        need('frontend-design', {'reason': 'User-facing framework or component files detected; confirm scope.'})

    signals = {area: [] for area in AREAS}
    signals['implementation'] = list(facts['manifests'])
    for capability, detail in capabilities.items():
        paths_for_capability = [entry['path'] for entry in detail['evidence'] if 'path' in entry]
        if capability in {'better-auth', 'sentry'}:
            signals['security'].extend(paths_for_capability)
        if capability in {'vitest', 'jest', 'playwright', 'vue-testing', 'accessibility', 'browser-testing'}:
            signals['testing'].extend(paths_for_capability)
        if capability in {'sentry', 'opentelemetry'}:
            signals['observability'].extend(paths_for_capability)
        if capability == 'linting':
            signals['maintenance'].extend(paths_for_capability)
    inventory = {'deployment': [], 'ci': [], 'observability': [], 'architecture': [], 'documentation': []}
    providers = {'vercel.json': 'vercel', 'netlify.toml': 'netlify', 'fly.toml': 'fly-io',
                 'railway.json': 'railway', 'railway.toml': 'railway', 'wrangler.toml': 'cloudflare',
                 'wrangler.jsonc': 'cloudflare', 'render.yaml': 'render'}
    sources = {'.ts', '.tsx', '.js', '.jsx', '.py', '.java', '.cs', '.kt', '.php', '.rb'}
    # Only return paths and signal locations. Never copy env values or arbitrary configuration text.
    for relative in paths:
        path = project / relative
        name = path.name.lower()
        parts = Path(relative).parts
        if name in providers:
            provider = providers[name]
            inventory['deployment'].append({'path': relative, 'target_hint': provider, 'review_required': True})
            signals['deployment'].append(relative)
            need(provider, {'path': relative, 'reason': 'Deployment configuration; confirm active vs obsolete.'})
        if path.suffix == '.tf':
            inventory['deployment'].append({'path': relative, 'target_hint': 'infrastructure-as-code', 'review_required': True})
            signals['deployment'].append(relative)
            need('terraform', {'path': relative, 'reason': 'Infrastructure definition; inspect providers, backend and target environments.'})
        if name.startswith('dockerfile') or name in {'compose.yml', 'compose.yaml', 'docker-compose.yml', 'docker-compose.yaml'}:
            inventory['deployment'].append({'path': relative, 'target_hint': 'container', 'review_required': True})
            signals['deployment'].append(relative)
            signals['operations'].append(relative)
            need('docker', {'path': relative, 'reason': 'Container build or Compose configuration; inspect purpose.'})
        if relative.startswith('.github/workflows/') or name in {'.gitlab-ci.yml', 'jenkinsfile', 'azure-pipelines.yml'} or relative.startswith('.circleci/'):
            platform = 'github-actions' if relative.startswith('.github/workflows/') else 'ci'
            inventory['ci'].append({'path': relative, 'platform': platform})
            signals['ci'].append(relative)
            need(platform, {'path': relative})
        if name in {'prometheus.yml', 'prometheus.yaml', 'otel-collector.yml', 'otel-collector.yaml'} or any(word in name for word in ('sentry.config', 'instrumentation.', 'telemetry.', 'logger.')):
            inventory['observability'].append({'path': relative, 'review_required': True})
            signals['observability'].append(relative)
        if 'migrations' in parts or 'drizzle' in parts or name == 'drizzle.config.ts':
            signals['migrations'].append(relative)
        if name.startswith(('test_', 'test.', 'vitest.config', 'playwright.config')) or '.test.' in name or '.spec.' in name:
            signals['testing'].append(relative)
        if path.suffix.lower() in {'.md', '.rst'}:
            inventory['documentation'].append(relative)
            signals['documentation'].append(relative)
            if any(word in name for word in ('requirements', 'stories', 'prd', 'roadmap', 'playbook', 'adr', 'architecture')):
                signals['requirements'].append(relative)
        if path.suffix.lower() not in sources or path.stat().st_size > 150_000:
            continue
        text = path.read_text(errors='replace')[:50_000]
        if re.search(r'\b(?:export\s+)?(?:abstract\s+)?class\s+\w+', text):
            need('oop', {'path': relative, 'reason': 'Class definitions; review object responsibilities.'})
        if re.search(r'\b(?:extends\s+(?:AggregateRoot|ValueObject|Entity)|implements\s+\w*Repository)\b', text):
            inventory['architecture'].append({'path': relative, 'signal': 'domain-model', 'review_required': True})
            signals['architecture'].append(relative)
            need('ddd', {'path': relative, 'reason': 'Domain primitives or repository contracts; confirm bounded contexts.'})
        if re.search(r'\b(?:console\.(?:error|warn|info)|logger\.(?:error|warn|info)|createLogger|useLogger)\s*\(', text):
            signals['observability'].append(relative)
        if 'health' in parts or any(word in name for word in ('health', 'ready', 'live.get')):
            signals['operations'].append(relative)

    facts['capabilities'] = dict(sorted(capabilities.items()))
    facts['unmapped_dependencies'] = {p: sorted(set(deps) - set(PACKAGES)) for p, deps in facts['dependencies'].items()}
    facts['lifecycle'] = {area: {'status': 'review-required' if signals[area] else 'unknown',
                               'evidence': sorted(set(signals[area]))[:25]} for area in AREAS}
    facts['context_inventory'] = {key: value[:60] for key, value in inventory.items()}
    facts['analysis_limits'] = ['Configuration paths and code signals require semantic review.',
                               'Inspect requirements and ADRs for desired architecture and planned deployment.',
                               'Unknown lifecycle areas are not evidence that a capability is unnecessary.']
    return facts


def validate_coverage(project, facts, selection, selected, previous, fingerprint):
    """Reject silent omissions, stale retained links, and unexamined lifecycle areas."""
    available = {item['id']: item for item in selected}
    for item in previous.get('resources', []):
        if item.get('id') in available:
            continue
        path = project / item['destination']
        if (path.is_symlink() and path.is_dir() and str(path.resolve()) == str(Path(item['target']).resolve())
                and fingerprint(path.resolve(), Path(item.get('source_root', item['target']))) == item['sha256']):
            available[item['id']] = item
    coverage = selection.get('coverage', {})
    omissions = selection.get('omissions', {})
    if not isinstance(coverage, dict) or not isinstance(omissions, dict):
        raise ValueError('Coverage and omissions must be mappings.')
    extra = selection.get('additional_capabilities', {})
    if not isinstance(extra, dict) or any(not isinstance(v, str) or not v.strip() for v in extra.values()):
        raise ValueError('Additional capabilities need project evidence or documented intent.')
    required = set(facts['capabilities']) | set(extra)
    for capability in sorted(required):
        record = coverage.get(capability, {})
        if isinstance(record, dict) and record.get('resources'):
            if not isinstance(record['resources'], list) or any(identity not in available for identity in record['resources']):
                raise ValueError(f'Coverage references an unavailable or changed skill: {capability}')
            if not str(record.get('reason', '')).strip():
                raise ValueError(f'Coverage needs a scope/version compatibility rationale: {capability}')
        elif not isinstance(omissions.get(capability), str) or not omissions[capability].strip():
            raise ValueError(f'Missing capability coverage: {capability}. Select reviewed skills or document a concrete omission.')
    assessment = selection.get('lifecycle', {})
    if required or facts['manifests']:
        for area in AREAS:
            record = assessment.get(area, {})
            if not isinstance(record, dict) or record.get('status') not in {'covered', 'unknown', 'not-applicable', 'gap'} or not str(record.get('reason', '')).strip():
                raise ValueError(f'Missing lifecycle assessment: {area}. Record current/desired state, evidence and unresolved decisions.')
            if not isinstance(record.get('resources', []), list) or any(identity not in available for identity in record.get('resources', [])):
                raise ValueError(f'Lifecycle assessment references an unavailable skill: {area}')
    return {'required': sorted(required), 'coverage': coverage, 'omissions': omissions,
            'additional_capabilities': extra, 'lifecycle': assessment, 'stack': stack_snapshot(facts)}
