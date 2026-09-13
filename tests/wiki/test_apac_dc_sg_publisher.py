import importlib.util
import hashlib
import json
import os
import subprocess
import tempfile
import unittest
from xml.etree import ElementTree
from zipfile import ZipFile
from pathlib import Path
from types import SimpleNamespace


ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "deploy" / "knowledge-content" / "publish_apac_dc.py"
NAS_SCRIPT_PATH = ROOT / "deploy" / "knowledge-content" / "publish-apac-dc-on-sg-nas.sh"
MANIFEST_PATH = (
    ROOT / "deploy" / "knowledge-content" / "assets" / "apac-dc-en" / "manifest.json"
)
SPEC = importlib.util.spec_from_file_location("publish_apac_dc_sg_test", MODULE_PATH)
publisher = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(publisher)


class PublishApacDcSgTest(unittest.TestCase):
    def test_sg_publish_accepts_only_pma_sa_database(self):
        with self.assertRaisesRegex(RuntimeError, "pma_sa"):
            publisher.validate_database_url(
                "postgresql://pma:secret@db/pma_synology", "pma_sa", "SG"
            )

        publisher.validate_database_url(
            "postgresql://pma:secret@db/pma_sa", "pma_sa", "SG"
        )

    def test_sg_commit_requires_both_ovs_type_and_pma_sa_database(self):
        package = publisher.package_config("sg")

        with self.assertRaisesRegex(RuntimeError, "PMA_DB_TYPE=ovs"):
            publisher.validate_target_environment(
                "postgresql://pma:secret@db/pma_sa", "sp8d", package
            )
        publisher.validate_target_environment(
            "postgresql://pma:secret@db/pma_sa", "ovs", package
        )

    def test_sg_manifest_registers_26_english_modules_and_keeps_full_ppt(self):
        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))

        self.assertEqual(manifest["lang"], "en")
        self.assertEqual(manifest["topic"], "Industry-Knowledge")
        self.assertEqual(len(manifest["pages"]), 26)
        self.assertTrue(all(page["label"].strip() for page in manifest["pages"]))
        self.assertTrue(all(page["notes"].strip() for page in manifest["pages"]))
        self.assertTrue((MANIFEST_PATH.parent / manifest["source_ppt"]).is_file())
        self.assertTrue((MANIFEST_PATH.parent / manifest["cover"]).is_file())
        owner = publisher.choose_owner(
            [
                SimpleNamespace(id=1, username="admin", role="admin"),
                SimpleNamespace(id=21, username="nijie", role="ceo"),
            ],
            manifest,
        )
        self.assertEqual(owner.id, 21)

    def test_packaged_ppt_keeps_26_modules_and_adds_one_closing_slide(self):
        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        ppt_path = MANIFEST_PATH.parent / manifest["source_ppt"]
        expected_hash = "82784f409c7d36dd5f53b868f1a31b8acda691b3e1fb135b3302b73643f3393e"

        self.assertEqual(manifest["source_slide_count"], 27)
        self.assertEqual(hashlib.sha256(ppt_path.read_bytes()).hexdigest(), expected_hash)
        with ZipFile(ppt_path) as archive:
            slide_names = [
                name for name in archive.namelist()
                if name.startswith("ppt/slides/slide") and name.endswith(".xml")
            ]
            notes_names = [
                name for name in archive.namelist()
                if name.startswith("ppt/notesSlides/notesSlide") and name.endswith(".xml")
            ]
            self.assertEqual(len(slide_names), 27)
            self.assertEqual(len(notes_names), 27)
            for index in range(1, 27):
                root = ElementTree.fromstring(
                    archive.read(f"ppt/notesSlides/notesSlide{index}.xml")
                )
                text_runs = [
                    node.text or "" for node in root.iter() if node.tag.endswith("}t")
                ]
                if text_runs and text_runs[-1] == str(index):
                    text_runs.pop()
                self.assertEqual(
                    "\n".join(text_runs).rstrip(), manifest["pages"][index - 1]["notes"]
                )
            closing = ElementTree.fromstring(archive.read("ppt/slides/slide27.xml"))
            closing_text = " ".join(" ".join(
                node.text or "" for node in closing.iter() if node.tag.endswith("}t")
            ).split())
            self.assertIn("Thank You", closing_text)

    def test_sg_download_metadata_reports_all_27_download_slides(self):
        manifest = {
            "key": "apac-data-center-critical-comms-en",
            "download_key": "apac-data-center-critical-comms-en-ppt",
            "lang": "en",
            "title": "Critical Communications for APAC Data Centers",
            "desc": "English training deck",
            "topic": "Industry Knowledge",
            "accent": "#0C5663",
            "source_slide_count": 27,
            "pages": [{} for _ in range(26)],
        }
        row = SimpleNamespace()

        publisher.apply_download_metadata(
            row, manifest, "/courses/apac-data-center-critical-comms-en.pptx", 31_000_000,
            "/courses/covers/apac-data-center-critical-comms-en.png",
        )

        self.assertEqual(row.subtitle, "PPT · 27 slides")
        self.assertEqual(row.page_count, 0)

    def test_sg_package_selects_the_named_uploader_as_owner(self):
        users = [
            SimpleNamespace(id=1, username="admin", role="admin"),
            SimpleNamespace(id=21, username="nijie", role="ceo"),
        ]

        owner = publisher.choose_owner(users, {"owner_username": "nijie"})

        self.assertEqual(owner.id, 21)
        with self.assertRaisesRegex(RuntimeError, "named course owner"):
            publisher.choose_owner(users, {"owner_username": "missing-user"})

    def test_remote_files_are_restored_when_database_registration_fails(self):
        class FakeClient:
            is_configured = True

            def __init__(self):
                self.files = {
                    "/courses/apac-data-center-critical-comms-en.pptx": b"old-ppt",
                }

            def file_exists(self, path):
                return path in self.files

            def file_exists_strict(self, path):
                return path in self.files

            def download_file(self, path):
                return self.files.get(path)

            def upload_file(self, content, path, content_type="application/octet-stream"):
                self.files[path] = content
                return path

            def delete_file(self, path):
                self.files.pop(path, None)
                return True

        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        client = FakeClient()

        def fail_registration(*args, **kwargs):
            raise RuntimeError("database failed")

        with self.assertRaisesRegex(RuntimeError, "database failed"):
            publisher.publish_remote_and_register(
                client, manifest, MANIFEST_PATH.parent, True, 21,
                register_fn=fail_registration,
            )

        self.assertEqual(
            client.files["/courses/apac-data-center-critical-comms-en.pptx"], b"old-ppt"
        )
        self.assertNotIn(
            "/courses/covers/apac-data-center-critical-comms-en.png", client.files
        )

    def test_ambiguous_webdav_probe_stops_before_upload_or_delete(self):
        class UncertainClient:
            is_configured = True

            def __init__(self):
                self.mutations = []

            def file_exists_strict(self, path):
                raise RuntimeError("WebDAV existence check failed: 500")

            def upload_file(self, content, path, content_type="application/octet-stream"):
                self.mutations.append(("upload", path))
                return path

            def delete_file(self, path):
                self.mutations.append(("delete", path))
                return True

        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        client = UncertainClient()

        with self.assertRaisesRegex(RuntimeError, "existence check failed"):
            publisher.publish_remote_and_register(
                client, manifest, MANIFEST_PATH.parent, True, 21,
                register_fn=lambda *args, **kwargs: None,
            )

        self.assertEqual(client.mutations, [])

    def test_strict_webdav_probe_only_treats_404_as_missing(self):
        from app.utils.synology_webdav_client import SynologyWebDAVClient

        class Session:
            def __init__(self, status_code):
                self.status_code = status_code

            def head(self, url, timeout):
                return SimpleNamespace(status_code=self.status_code)

        fake = SimpleNamespace(
            is_configured=True,
            session=Session(404),
            timeout=30,
            _build_url=lambda path: "https://nas.invalid" + path,
        )
        self.assertFalse(SynologyWebDAVClient.file_exists_strict(fake, "/old.pptx"))

        fake.session = Session(500)
        with self.assertRaisesRegex(RuntimeError, "HTTP 500"):
            SynologyWebDAVClient.file_exists_strict(fake, "/old.pptx")

    def test_sg_nas_script_refuses_non_sg_target_before_writes(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            log = tmp_path / "docker.log"
            fake_docker = tmp_path / "docker"
            fake_docker.write_text(
                '#!/bin/sh\nprintf "%s\\n" "$*" >> "$FAKE_DOCKER_LOG"\nexit 1\n',
                encoding="utf-8",
            )
            fake_docker.chmod(0o755)
            env = os.environ.copy()
            env.update(
                {
                    "PMA_SUDO_BIN": "",
                    "PMA_DOCKER_BIN": str(fake_docker),
                    "FAKE_DOCKER_LOG": str(log),
                }
            )

            result = subprocess.run(
                ["bash", str(NAS_SCRIPT_PATH), "--commit"],
                cwd=ROOT,
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(result.returncode, 2)
            self.assertIn("SG/OVS", result.stdout)
            calls = log.read_text(encoding="utf-8").splitlines()
            self.assertEqual(len(calls), 1)
            self.assertTrue(calls[0].startswith("exec pma-app sh -c"))

    def test_sg_nas_script_builds_and_switches_the_sg_package(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            assets = tmp_path / "course_assets"
            log = tmp_path / "docker.log"
            fake_docker = tmp_path / "docker"
            fake_docker.write_text(
                """#!/bin/sh
printf '%s\n' "$*" >> "$FAKE_DOCKER_LOG"
if [ "$1" = "cp" ]; then
    case "$2" in
        pma-app:*) printf 'sg-course-html' > "$3" ;;
    esac
fi
exit 0
""",
                encoding="utf-8",
            )
            fake_docker.chmod(0o755)
            env = os.environ.copy()
            env.update(
                {
                    "PMA_SUDO_BIN": "",
                    "PMA_DOCKER_BIN": str(fake_docker),
                    "PMA_COURSE_ASSETS": str(assets),
                    "FAKE_DOCKER_LOG": str(log),
                }
            )

            result = subprocess.run(
                ["bash", str(NAS_SCRIPT_PATH), "--commit"],
                cwd=ROOT,
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertEqual(
                (assets / "apac-data-center-critical-comms-en.html").read_text(),
                "sg-course-html",
            )
            self.assertEqual(
                len(list((assets / "apac-data-center-critical-comms-en.thumbs").glob("*.png"))),
                26,
            )
            calls = log.read_text(encoding="utf-8")
            self.assertIn("publish_apac_dc.py --market sg", calls)
            self.assertIn("--market sg --commit --skip-assets --has-thumbs", calls)


if __name__ == "__main__":
    unittest.main()
