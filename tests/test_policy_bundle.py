import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('bundle', ROOT / 'scripts/policy_bundle.py')
bundle = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bundle)


class PolicyBundleTest(unittest.TestCase):
    def test_kit_and_design_roundtrip_preserves_source_bytes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for package in bundle.CONTENTS:
                artifact, sha = bundle.build(package, '0.1.0', root)
                installed = root / package
                manifest = bundle.install(artifact, sha, installed)
                for name in manifest['files']:
                    self.assertEqual((installed / name).read_bytes(), (ROOT / 'packages' / package / name).read_bytes())
                with self.assertRaises(ValueError):
                    bundle.install(artifact, sha, installed)

    def test_tampering_fails_before_destination_is_created(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            artifact, sha = bundle.build('kit', '0.1.0', root)
            with artifact.open('ab') as stream:
                stream.write(b'tampered')
            with self.assertRaises(ValueError):
                bundle.install(artifact, sha, root / 'installed')
            self.assertFalse((root / 'installed').exists())

    def test_traversal_and_symlinks_are_rejected_even_with_matching_outer_hash(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for name, mode in [('../escape', 0o100644), ('link', 0o120777)]:
                artifact = root / 'malicious.zip'
                with zipfile.ZipFile(artifact, 'w') as z:
                    entry = zipfile.ZipInfo(name)
                    entry.external_attr = mode << 16
                    z.writestr(entry, b'bad')
                with self.assertRaises(ValueError):
                    bundle.install(artifact, bundle.digest(artifact.read_bytes()), root / 'installed')
            self.assertFalse((root / 'escape').exists())

    def test_unmanifested_files_are_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            artifact, sha = bundle.build('kit', '0.1.0', root)
            with zipfile.ZipFile(artifact, 'a') as z:
                z.writestr('extra.txt', 'unexpected')
            with self.assertRaises(ValueError):
                bundle.install(artifact, bundle.digest(artifact.read_bytes()), root / 'installed')


if __name__ == '__main__':
    unittest.main()
