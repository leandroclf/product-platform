"""Offline integrity checks, never quality approval or execution of manifest commands."""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path, PurePosixPath
import re
import struct
import subprocess
import stat
import sys
import tempfile
import zlib

from jsonschema import Draft202012Validator

CONTRACTS = Path(__file__).resolve().parents[2] / 'kit/contracts/visual-feedback'
MAX_JSON_BYTES = 256 * 1024
MAX_ARTIFACT_BYTES = 25 * 1024 * 1024


def read_bounded(path, limit):
    with Path(path).open('rb') as stream:
        raw = stream.read(limit + 1)
    if len(raw) > limit:
        raise ValueError('file exceeds size limit')
    return raw


def read_json(path):
    raw = read_bounded(path, MAX_JSON_BYTES)
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError('duplicate JSON key')
            result[key] = value
        return result
    def finite_float(value):
        parsed = float(value)
        if not math.isfinite(parsed):
            raise ValueError('nonfinite JSON number')
        return parsed
    return json.loads(raw, object_pairs_hook=pairs, parse_float=finite_float,
                      parse_constant=lambda _: (_ for _ in ()).throw(ValueError('nonfinite JSON number')))


def artifact_bytes(root, artifact):
    relative = PurePosixPath(artifact['path'])
    if relative.is_absolute() or '..' in relative.parts or '\\' in artifact['path'] or not relative.parts:
        raise ValueError('artifact must be a relative contained path')
    root = Path(root).resolve(strict=True)
    path = (root / relative).resolve(strict=True)
    if not path.is_relative_to(root) or not path.is_file():
        raise ValueError('artifact escapes evidence root or is not a file')
    raw = read_bounded(path, MAX_ARTIFACT_BYTES)
    if hashlib.sha256(raw).hexdigest() != artifact['sha256']:
        raise ValueError('artifact digest mismatch')
    return raw


def png_dimensions(raw):
    # Verify PNG container and CRCs, not rendered visual content or decoded pixels.
    if not raw.startswith(b'\x89PNG\r\n\x1a\n'):
        raise ValueError('screenshot must be PNG')
    offset, dimensions, image_data = 8, None, False
    while offset + 12 <= len(raw):
        length = struct.unpack('>I', raw[offset:offset + 4])[0]
        end = offset + 12 + length
        if end > len(raw):
            raise ValueError('truncated PNG')
        kind = raw[offset + 4:offset + 8]
        payload = raw[offset + 8:end - 4]
        if zlib.crc32(kind + payload) & 0xffffffff != struct.unpack('>I', raw[end - 4:end])[0]:
            raise ValueError('PNG CRC mismatch')
        if dimensions is None:
            if kind != b'IHDR' or length != 13:
                raise ValueError('PNG requires first IHDR')
            dimensions = struct.unpack('>II', payload[:8])
            if not all(dimensions):
                raise ValueError('PNG dimensions must be positive')
        elif kind == b'IHDR':
            raise ValueError('duplicate PNG IHDR')
        image_data |= kind == b'IDAT' and length > 0
        if kind == b'IEND':
            if length or end != len(raw) or not image_data:
                raise ValueError('invalid PNG ending or no image data')
            return dimensions
        offset = end
    raise ValueError('incomplete PNG')


def unique(items, key):
    values = [item[key] for item in items]
    if len(set(values)) != len(values):
        raise ValueError('duplicate ' + key)
    return set(values)


def validate_v2(task, evidence, root):
    states = unique(task['ux']['states'], 'id')
    if states != {'ready', 'loading', 'empty', 'error', 'disabled'}:
        raise ValueError('all UX states require explicit applicability/behavior')
    applicable = {s['id'] for s in task['ux']['states'] if s['applicable']}
    if 'ready' not in applicable:
        raise ValueError('ready state must be applicable')
    widths = [v['width'] for v in task['viewports']]
    if min(widths) > 480 or max(widths) < 1024:
        raise ValueError('mobile and desktop viewports required')
    paths = task['impact']['paths']
    if len(paths) != len(set(paths)):
        raise ValueError('duplicate impact path')
    for name in paths:
        p = PurePosixPath(name)
        if p.is_absolute() or '..' in p.parts or '\\' in name or not p.parts or '.git' in p.parts:
            raise ValueError('invalid impact path')
    behaviors = unique(task['impact']['preserved_behaviors'], 'id')
    regressions = unique(task['regressions'], 'id')
    criterion_ids = {c['id'] for c in task['criteria']}
    covered = set()
    for regression in task['regressions']:
        covered.update(regression['behavior_ids'])
        if not set(regression['behavior_ids']) <= behaviors or not set(regression['criterion_ids']) <= criterion_ids:
            raise ValueError('regression refers to unknown behavior or criterion')
    if covered != behaviors:
        raise ValueError('preserved behavior has no regression coverage')
    captures = [(s['viewport_id'], s['state_id']) for s in evidence['screenshots']]
    expected = {(v['id'], state) for v in task['viewports'] for state in applicable}
    if len(set(captures)) != len(captures) or not set(captures) <= expected:
        raise ValueError('duplicate or unknown viewport/state capture')
    results = unique(evidence['regression_results'], 'id')
    budgets = unique(task['performance_budgets'], 'id')
    measured = unique(evidence['performance_results'], 'id')
    if not results <= regressions or not measured <= budgets:
        raise ValueError('unknown regression or performance result')
    if evidence['status'] != 'blocked' and (set(captures) != expected or results != regressions or measured != budgets):
        raise ValueError('missing state, regression or performance evidence')
    for check in evidence['checks']:
        for artifact in check['artifacts']:
            artifact_bytes(root, artifact)
    for result in evidence['regression_results'] + evidence['performance_results']:
        artifact_bytes(root, result['artifact'])


def validate(task_path, evidence_path, root, expected_head):
    if not re.fullmatch('[a-f0-9]{40}', expected_head):
        raise ValueError('expected head must be a full SHA')
    task, evidence = read_json(task_path), read_json(evidence_path)
    version = task.get('schema_version') if isinstance(task, dict) else None
    if type(version) is not int or version not in (1, 2):
        raise ValueError('unsupported visual contract version')
    for name, document in [('task', task), ('evidence', evidence)]:
        Draft202012Validator(read_json(CONTRACTS / (name + f'.v{version}.schema.json'))).validate(document)
    if evidence['task_sha256'] != hashlib.sha256(read_bounded(task_path, MAX_JSON_BYTES)).hexdigest():
        raise ValueError('stale task digest')
    if evidence['head_sha'] != expected_head:
        raise ValueError('stale head SHA')
    viewports = unique(task['viewports'], 'id')
    criteria = unique(task['criteria'], 'id')
    if {item['kind'] for item in task['criteria']} != {'visual', 'functional', 'accessibility'}:
        raise ValueError('visual, functional and accessibility criteria are required')
    artifact_bytes(root, task['reference']['artifact'])
    if version == 2:
        validate_v2(task, evidence, root)
    captured = (unique(evidence['screenshots'], 'viewport_id') if version == 1
                else {s['viewport_id'] for s in evidence['screenshots']})
    checked = unique(evidence['checks'], 'criterion_id')
    if not captured <= viewports or not checked <= criteria:
        raise ValueError('unknown viewport or criterion')
    if evidence['status'] != 'blocked' and (captured != viewports or checked != criteria):
        raise ValueError('missing screenshot or criterion')
    if evidence['status'] == 'assessed' and any(item['status'] == 'not-run' for item in evidence['checks']):
        raise ValueError('assessed evidence has unexecuted checks')
    for capture in evidence['screenshots']:
        width, height = png_dimensions(artifact_bytes(root, capture['artifact']))
        viewport = next(item for item in task['viewports'] if item['id'] == capture['viewport_id'])
        if width != viewport['width'] or height < viewport['height']:
            raise ValueError('PNG dimensions do not match viewport/full-page capture')
    budget = task['budget']
    exceeded = (evidence['iterations'] > budget['max_iterations'] or
                evidence['elapsed_seconds'] > budget['max_elapsed_seconds'] or
                evidence['cost_usd'] is not None and evidence['cost_usd'] > budget['max_cost_usd'])
    unknown_cost = evidence['model_execution'] == 'live' and evidence['cost_usd'] is None
    if (exceeded or unknown_cost) and evidence['status'] != 'blocked':
        raise ValueError('budget exceeded or unknown live-model cost requires blocked status')
    return evidence['status']


def checkout_git(checkout, *args):
    # Read-only Git commands: never inherit credentials, Git overrides, fsmonitor,
    # external diff drivers or global config from an authenticated agent process.
    env = {'PATH': os.defpath, 'LC_ALL': 'C', 'GIT_CONFIG_NOSYSTEM': '1',
           'GIT_CONFIG_GLOBAL': os.devnull, 'GIT_OPTIONAL_LOCKS': '0'}
    with tempfile.TemporaryFile() as output:
        subprocess.run(['git', '--no-replace-objects', '-c', 'core.fsmonitor=false',
                        '-C', str(checkout), *args], env=env, check=True,
                       stdout=output, stderr=subprocess.DEVNULL, timeout=15)
        output.seek(0)
        raw = output.read(MAX_JSON_BYTES + 1)
        if len(raw) > MAX_JSON_BYTES:
            raise ValueError('Git output exceeds limit')
        return raw


def verify_source_bytes(checkout, expected_head):
    """Git stat-cache/mtime are not proof of unchanged content. Never run filters."""
    entries = checkout_git(checkout, 'ls-tree', '-r', '-z', expected_head).split(b'\0')
    total_bytes = 0
    for entry in filter(None, entries):
        metadata, raw_path = entry.split(b'\t', 1)
        mode, kind, oid = metadata.split(b' ')
        if kind != b'blob' or mode not in (b'100644', b'100755'):
            raise ValueError('source symlinks/submodules need separate materialized-input evidence')
        path = checkout / os.fsdecode(raw_path)
        if path.is_symlink() or not path.resolve(strict=True).is_relative_to(checkout) or not path.is_file():
            raise ValueError('source file is missing or escapes checkout')
        raw = read_bounded(path, MAX_ARTIFACT_BYTES)
        total_bytes += len(raw)
        if total_bytes > 256 * 1024 * 1024:
            raise ValueError('source snapshot exceeds verification budget')
        blob = hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest().encode()
        executable = bool(path.stat().st_mode & stat.S_IXUSR)
        if blob != oid or executable != (mode == b'100755'):
            raise ValueError('source bytes/mode differ from captured commit; recapture evidence')


def require_acceptance(task_path, evidence_path, root, expected_head, checkout):
    status = validate(task_path, evidence_path, root, expected_head)
    task, evidence = read_json(task_path), read_json(evidence_path)
    if task['schema_version'] != 2 or status != 'assessed':
        raise ValueError('acceptance requires assessed v2 evidence')
    png_dimensions(artifact_bytes(root, task['reference']['artifact']))
    if task['ux']['patterns_status'] == 'not-assessed':
        raise ValueError('interaction patterns not assessed')
    if task['ux']['patterns_status'] == 'existing' and not task['ux']['pattern_refs']:
        raise ValueError('existing patterns require references')
    if any(c['status'] != 'pass' for c in evidence['checks'] + evidence['regression_results']):
        raise ValueError('unexecuted or failed acceptance/regression check')
    for budget in task['performance_budgets']:
        result = next(r for r in evidence['performance_results'] if r['id'] == budget['id'])
        if result['before'] != budget['baseline'] or result['after'] > budget['max_after']:
            raise ValueError('performance baseline mismatch or budget exceeded')
    checkout = Path(checkout).resolve(strict=True)
    if checkout_git(checkout, 'rev-parse', '--show-toplevel').decode().strip() != str(checkout):
        raise ValueError('checkout must be the repository root')
    if checkout_git(checkout, 'rev-parse', 'HEAD').decode().strip() != expected_head:
        raise ValueError('checkout HEAD differs from captured HEAD')
    if checkout_git(checkout, 'rev-parse', 'HEAD^{tree}').decode().strip() != evidence['source_tree_sha']:
        raise ValueError('source tree differs from captured tree')
    indexed = checkout_git(checkout, 'ls-files', '-v', '-z').split(b'\0')
    if any(not entry.startswith(b'H ') for entry in indexed if entry):
        raise ValueError('index flags may hide code changes; use a full ordinary checkout')
    # Do not use git status/diff against the worktree: refreshing stat information
    # can invoke a repository-defined clean filter. Compare cached index only,
    # enumerate untracked names, then hash the source bytes ourselves.
    if checkout_git(checkout, 'ls-files', '--others', '--exclude-standard', '-z'):
        raise ValueError('checkout is dirty; recapture evidence')
    try:
        checkout_git(checkout, 'diff-index', '--cached', '--quiet', '--no-ext-diff', '--no-textconv', 'HEAD', '--')
    except subprocess.CalledProcessError as exc:
        raise ValueError('checkout index is dirty; recapture evidence') from exc
    verify_source_bytes(checkout, expected_head)
    checkout_git(checkout, 'merge-base', '--is-ancestor', task['base_sha'], expected_head)
    changed = checkout_git(checkout, 'diff', '--no-ext-diff', '--no-textconv', '--name-only',
                           '--no-renames', '-z', task['base_sha'], expected_head).decode().split('\0')
    if not set(filter(None, changed)) <= set(task['impact']['paths']):
        raise ValueError('delivered change exceeds declared impact scope')
    return 'pass'


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--task', required=True, type=Path)
    parser.add_argument('--evidence', required=True, type=Path)
    parser.add_argument('--root', required=True, type=Path)
    parser.add_argument('--expected-head', required=True)
    parser.add_argument('--require-acceptance', action='store_true')
    parser.add_argument('--checkout', type=Path)
    args = parser.parse_args(argv)
    try:
        if args.require_acceptance:
            if not args.checkout:
                raise ValueError('acceptance requires a checkout')
            require_acceptance(args.task, args.evidence, args.root, args.expected_head, args.checkout)
            print('Visual acceptance prerequisites PASS; technical judgment and GitHub approval remain required')
            return 0
        if args.checkout:
            raise ValueError('checkout requires explicit acceptance mode')
        status = validate(args.task, args.evidence, args.root, args.expected_head)
    except Exception as exc:
        # Avoid echoing arbitrary paths, document contents or schema data in logs.
        print('Visual evidence invalid: ' + type(exc).__name__, file=sys.stderr)
        return 1
    print('Visual evidence integrity OK (' + status + '); not quality, independence or merge approval')
    return 0


if __name__ == '__main__':
    sys.exit(main())
