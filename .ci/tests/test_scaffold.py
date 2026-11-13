import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
CONFIG = json.loads((ROOT / ".ci/scaffold.json").read_text())


def load(path):
    spec = importlib.util.spec_from_file_location(path.stem, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class SourceGateTests(unittest.TestCase):
    def setUp(self):
        self.bootstrap = load(ROOT / ".ci/bootstrap.py")
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)

    def test_empty_repository_waits_without_deploying(self):
        self.assertFalse(self.bootstrap.code_present(self.root, CONFIG["required_code"]))

    def test_partial_application_source_fails(self):
        first = self.root / CONFIG["required_code"][0]
        first.parent.mkdir(parents=True, exist_ok=True)
        first.write_text("fixture")
        with self.assertRaisesRegex(ValueError, "incomplete"):
            self.bootstrap.code_present(self.root, CONFIG["required_code"])

    def test_complete_source_enables_full_pipeline(self):
        for name in CONFIG["required_code"]:
            path = self.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("fixture")
        self.assertTrue(self.bootstrap.code_present(self.root, CONFIG["required_code"]))


class GatewayTrustTests(unittest.TestCase):
    def setUp(self):
        self.gateway = load(ROOT / "deploy" / CONFIG["gateway"])
        self.sha = "a" * 40
        self.new = "https://github.com/" + CONFIG["repository"]
        self.old = "https://github.com/" + CONFIG["previous_repository"]

    def check_image(self, source, rollback=False):
        info = [{"Id": "sha256:fixture", "Config": {"Labels": {"org.opencontainers.image.source": source, "org.opencontainers.image.revision": self.sha}, "User": "10001"}}]
        if CONFIG["gateway"] != "cd_gateway.py":
            with patch.object(self.gateway, "run", return_value=json.dumps(info)):
                return self.gateway.verify(self.sha, allow_legacy=rollback)
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            for directory in ("inbox", "shared/deployments"):
                (root / directory).mkdir(parents=True)
            import hashlib
            import io
            payload = b"fixture-image"
            def run(args, **kwargs):
                return json.dumps(info) if args[:3] == ["docker", "image", "inspect"] else ""
            with patch.object(self.gateway, "ROOT", root), patch.object(self.gateway, "SHARED", root / "shared"), patch.object(self.gateway, "run", side_effect=run), patch.object(self.gateway.shutil, "disk_usage", return_value=type("Disk", (), {"free": 100 * 1024**3})()):
                return self.gateway.receive("image", self.sha, hashlib.sha256(payload).hexdigest(), io.BytesIO(payload))

    def test_new_repository_images_are_accepted(self):
        self.check_image(self.new)

    def test_old_repository_cannot_upload_new_images(self):
        with self.assertRaises(ValueError):
            self.check_image(self.old)

    def test_unrelated_repository_is_rejected(self):
        with self.assertRaises(ValueError):
            self.check_image("https://github.com/untrusted/source")

    def test_old_images_remain_available_for_explicit_rollback(self):
        if CONFIG["gateway"] == "cd_gateway.py":
            self.skipTest("Data platform retains verified existing release markers for rollback")
        self.check_image(self.old, rollback=True)


if __name__ == "__main__":
    unittest.main()
