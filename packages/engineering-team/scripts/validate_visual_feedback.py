"""Offline integrity checks, never quality approval or execution of manifest commands."""
import argparse
import hashlib
import json
import math
from pathlib import Path, PurePosixPath
import re
import struct
import sys
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


def validate(task_path, evidence_path, root, expected_head):
    if not re.fullmatch('[a-f0-9]{40}', expected_head):
        raise ValueError('expected head must be a full SHA')
    task, evidence = read_json(task_path), read_json(evidence_path)
    for name, document in [('task', task), ('evidence', evidence)]:
        Draft202012Validator(read_json(CONTRACTS / (name + '.v1.schema.json'))).validate(document)
    if evidence['task_sha256'] != hashlib.sha256(read_bounded(task_path, MAX_JSON_BYTES)).hexdigest():
        raise ValueError('stale task digest')
    if evidence['head_sha'] != expected_head:
        raise ValueError('stale head SHA')
    viewports = unique(task['viewports'], 'id')
    criteria = unique(task['criteria'], 'id')
    if {item['kind'] for item in task['criteria']} != {'visual', 'functional', 'accessibility'}:
        raise ValueError('visual, functional and accessibility criteria are required')
    artifact_bytes(root, task['reference']['artifact'])
    captured = unique(evidence['screenshots'], 'viewport_id')
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


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--task', required=True, type=Path)
    parser.add_argument('--evidence', required=True, type=Path)
    parser.add_argument('--root', required=True, type=Path)
    parser.add_argument('--expected-head', required=True)
    args = parser.parse_args(argv)
    try:
        status = validate(args.task, args.evidence, args.root, args.expected_head)
    except Exception as exc:
        # Avoid echoing arbitrary paths, document contents or schema data in logs.
        print('Visual evidence invalid: ' + type(exc).__name__, file=sys.stderr)
        return 1
    print('Visual evidence integrity OK (' + status + '); not quality, independence or merge approval')
    return 0


if __name__ == '__main__':
    sys.exit(main())
