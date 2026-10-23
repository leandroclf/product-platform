"""Offline validation of self-reported release provenance."""
import tempfile
from pathlib import Path
import unittest

from scripts.build_release_manifest import make_manifest


class ReleaseManifestTests(unittest.TestCase):
    def test_manifest_contains_source_and_both_hashes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "pkg.tgz").write_bytes(b"npm")
            (root / "pkg.whl").write_bytes(b"python")
            value = make_manifest(root, tag="harness-v1.2.3", source_sha="a" * 40,
                                  repository="leandroclf/product-platform",
                                  generated_at="2026-10-18T00:00:00Z")
            self.assertEqual(value["source_commit"], "a" * 40)
            self.assertEqual(len(value["artifacts"]), 2)
            self.assertEqual([a["bytes"] for a in value["artifacts"]], [3, 6])
            self.assertEqual(value["provenance_level"], "self-reported-not-attested")

    def test_missing_artifacts_and_bad_tag_fail(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "pkg.tgz").write_bytes(b"npm")
            with self.assertRaises(ValueError):
                make_manifest(root, tag="harness-v1.2.3", source_sha="a"*40,
                              repository="leandroclf/product-platform")
            (root / "pkg.whl").write_bytes(b"wheel")
            for tag in ("../oops", "harness-main", "harness-vx"):
                with self.assertRaises(ValueError):
                    make_manifest(root, tag=tag, source_sha="a"*40,
                                  repository="leandroclf/product-platform")

    def test_symlinked_artifact_is_blocked(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "pkg.tgz").write_bytes(b"npm")
            (root / "pkg.whl").symlink_to(root / "pkg.tgz")
            with self.assertRaises(ValueError):
                make_manifest(root, tag="harness-v1.2.3", source_sha="a"*40,
                              repository="leandroclf/product-platform")

class ReleaseToolchainTests(unittest.TestCase):
    def test_records_toolchain_and_rejects_missing_wheel(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'a.tgz').write_bytes(b'npm')
            (root / 'b.tgz').write_bytes(b'npm')
            with self.assertRaises(ValueError):
                make_manifest(root, tag='harness-v1.2.3', source_sha='a'*40,
                              repository='leandroclf/product-platform')
            (root / 'b.tgz').unlink()
            (root / 'b.whl').write_bytes(b'wheel')
            result = make_manifest(root, tag='harness-v1.2.3', source_sha='a'*40,
                                   repository='leandroclf/product-platform', toolchain={'python': '3.12.0'})
            self.assertEqual(result['toolchain'], {'python': '3.12.0'})


if __name__ == "__main__":
    unittest.main()
