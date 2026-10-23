#!/usr/bin/env python3
"""Build and install local, checksum-pinned policy/assets bundles; no network or publication."""
import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]
MAX_BYTES = 20 * 1024 * 1024
CONTENTS = {
    'kit': ['AGENTS.md', 'CLAUDE.md', 'ai-kit.yaml', 'config', 'adapters', 'profiles', 'skills', 'contracts'],
    'design-system': ['tokens.css', 'tokens.json', 'assets', 'README.md', 'package.json'],
}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def build(package, version, output, root=ROOT):
    if package not in CONTENTS or not re.fullmatch(r'\d+\.\d+\.\d+(?:-[a-z0-9.-]+)?', version):
        raise ValueError('Unknown package or invalid version')
    source = root / 'packages' / package
    files = []
    for name in CONTENTS[package]:
        path = source / name
        if path.is_symlink() or not path.exists():
            raise ValueError(f'Missing or symlinked source: {name}')
        files.extend([path] if path.is_file() else sorted(path.rglob('*')))
    data = {}
    for file in files:
        if file.is_symlink():
            raise ValueError('Symlinks are not distributable')
        if file.is_file():
            data[file.relative_to(source).as_posix()] = file.read_bytes()
    if sum(map(len, data.values())) > MAX_BYTES:
        raise ValueError('Bundle too large')
    sha = subprocess.check_output(['git', '-C', str(root), 'rev-parse', 'HEAD'], text=True).strip()
    dirty = bool(subprocess.check_output(['git', '-C', str(root), 'status', '--porcelain'], text=True))
    manifest = {'schema_version': 1, 'package': package, 'version': version,
                'source_commit': sha, 'source_dirty': dirty,
                'files': {name: {'sha256': digest(value), 'bytes': len(value)} for name, value in sorted(data.items())}}
    output.mkdir(parents=True, exist_ok=True)
    target = output / f'{package}-v{version}.zip'
    with zipfile.ZipFile(target, 'x', compression=zipfile.ZIP_STORED) as archive:
        for name, value in sorted({**data, 'BUNDLE-MANIFEST.json': json.dumps(manifest, sort_keys=True, indent=2).encode()}.items()):
            info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.external_attr = 0o100644 << 16
            archive.writestr(info, value)
    checksum = digest(target.read_bytes())
    target.with_suffix('.sha256').write_text(f'{checksum}  {target.name}\n')
    return target, checksum


def install(artifact, expected_sha, destination):
    if not re.fullmatch(r'[a-f0-9]{64}', expected_sha):
        raise ValueError('Expected explicit SHA-256')
    if artifact.stat().st_size > MAX_BYTES or digest(artifact.read_bytes()) != expected_sha:
        raise ValueError('Artifact checksum/size mismatch')
    if destination.exists() or destination.is_symlink():
        raise ValueError('Destination must not exist; updates need a new version directory')
    with zipfile.ZipFile(artifact) as archive:
        entries = archive.infolist()
        names = [entry.filename for entry in entries]
        if len(set(names)) != len(names) or sum(e.file_size for e in entries) > MAX_BYTES:
            raise ValueError('Duplicate members or oversized contents')
        for entry in entries:
            name = PurePosixPath(entry.filename)
            if name.is_absolute() or '..' in name.parts or '\\' in entry.filename or entry.is_dir() or (entry.external_attr >> 16) & 0o170000 != 0o100000:
                raise ValueError('Unsafe member')
        manifest = json.loads(archive.read('BUNDLE-MANIFEST.json'))
        if manifest.get('schema_version') != 1 or manifest.get('package') not in CONTENTS:
            raise ValueError('Unsupported manifest')
        if set(names) != set(manifest['files']) | {'BUNDLE-MANIFEST.json'}:
            raise ValueError('Unmanifested or missing contents')
        data = {}
        for name, spec in manifest['files'].items():
            value = archive.read(name)
            if digest(value) != spec['sha256'] or len(value) != spec['bytes']:
                raise ValueError('Content checksum mismatch')
            data[name] = value
        # Verify all bytes before creating a version directory. Never extractall().
        with tempfile.TemporaryDirectory(dir=destination.parent) as tmp:
            stage = Path(tmp) / 'verified'
            stage.mkdir()
            for name, value in data.items():
                file = stage / name
                file.parent.mkdir(parents=True, exist_ok=True)
                file.write_bytes(value)
            (stage / 'BUNDLE-MANIFEST.json').write_text(json.dumps(manifest, indent=2) + '\n')
            os.rename(stage, destination)
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    create = sub.add_parser('build')
    create.add_argument('--package', choices=CONTENTS, required=True)
    create.add_argument('--version', required=True)
    create.add_argument('--output-dir', type=Path, required=True)
    consume = sub.add_parser('install')
    consume.add_argument('--artifact', type=Path, required=True)
    consume.add_argument('--sha256', required=True)
    consume.add_argument('--destination', type=Path, required=True)
    args = parser.parse_args()
    if args.command == 'build':
        target, checksum = build(args.package, args.version, args.output_dir)
        print(json.dumps({'artifact': str(target), 'sha256': checksum}))
    else:
        print(json.dumps(install(args.artifact, args.sha256, args.destination)))


if __name__ == '__main__':
    main()
