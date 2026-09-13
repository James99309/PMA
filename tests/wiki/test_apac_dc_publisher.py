import importlib.util
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace


ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "deploy" / "knowledge-content" / "publish_apac_dc.py"
NAS_SCRIPT_PATH = ROOT / "deploy" / "knowledge-content" / "publish-apac-dc-on-nas.sh"
WIKI_TEMPLATE_PATH = ROOT / "app" / "templates" / "knowledge" / "at_wiki.html"
SPEC = importlib.util.spec_from_file_location("publish_apac_dc", MODULE_PATH)
publisher = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(publisher)


class FakeWebDav:
    is_configured = True

    def __init__(self, succeeds=True):
        self.succeeds = succeeds
        self.uploads = []

    def upload_file(self, content, remote_path):
        self.uploads.append((content, remote_path))
        return self.succeeds


class PublishApacDcTest(unittest.TestCase):
    def test_nas_script_exits_before_copy_when_cn_preflight_fails(self):
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
            self.assertIn("不是 CN/SP8D", result.stdout)
            calls = log.read_text(encoding="utf-8").splitlines()
            self.assertEqual(len(calls), 1)
            self.assertTrue(calls[0].startswith("exec pma-app sh -c"))
            self.assertNotIn("cp ", calls[0])

    def test_nas_script_restores_html_and_thumbnails_when_second_switch_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            assets = tmp_path / "course_assets"
            assets.mkdir()
            live_html = assets / "apac-data-center-critical-comms-cn.html"
            live_thumbs = assets / "apac-data-center-critical-comms-cn.thumbs"
            live_html.write_text("old-html", encoding="utf-8")
            live_thumbs.mkdir()
            (live_thumbs / "1.png").write_bytes(b"old-thumb")

            fake_docker = tmp_path / "docker"
            fake_docker.write_text(
                """#!/bin/sh
if [ "$1" = "cp" ]; then
    case "$2" in
        pma-app:*) printf "new-html" > "$3" ;;
    esac
fi
exit 0
""",
                encoding="utf-8",
            )
            fake_docker.chmod(0o755)
            fake_mv = tmp_path / "mv"
            fake_mv.write_text(
                """#!/bin/sh
case "$1" in
    *.thumbs.old.*) ;;
    *.thumbs.*)
        case "$2" in *.thumbs) exit 9 ;; esac
        ;;
esac
exec /bin/mv "$@"
""",
                encoding="utf-8",
            )
            fake_mv.chmod(0o755)
            env = os.environ.copy()
            env.update(
                {
                    "PMA_SUDO_BIN": "",
                    "PMA_DOCKER_BIN": str(fake_docker),
                    "PMA_COURSE_ASSETS": str(assets),
                    "PATH": f"{tmp_path}:{env['PATH']}",
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

            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(live_html.read_text(encoding="utf-8"), "old-html")
            self.assertEqual((live_thumbs / "1.png").read_bytes(), b"old-thumb")

    def test_nas_script_checks_cn_target_before_any_publication_write(self):
        script = NAS_SCRIPT_PATH.read_text(encoding="utf-8")

        preflight = script.index("\nassert_cn_target\n")
        first_container_copy = script.index('run_docker exec "$APP_CONTAINER" mkdir')
        first_host_write = script.index('run_sudo mkdir -p "$COURSE_ASSETS"')

        self.assertLess(preflight, first_container_copy)
        self.assertLess(preflight, first_host_write)
        self.assertIn('PMA_DB_TYPE:-', script)
        self.assertIn('*/pma_synology', script)

    def test_nas_script_stages_assets_before_atomic_rename(self):
        script = NAS_SCRIPT_PATH.read_text(encoding="utf-8")

        self.assertIn('STAGED_HTML="$COURSE_ASSETS/.$KEY.html.$$"', script)
        self.assertIn('STAGED_THUMBS="$COURSE_ASSETS/.$KEY.thumbs.$$"', script)
        self.assertIn('OLD_HTML="$COURSE_ASSETS/.$KEY.html.old.$$"', script)
        self.assertIn('run_sudo mv "$STAGED_HTML" "$LIVE_HTML"', script)
        self.assertIn('run_sudo mv "$STAGED_THUMBS" "$LIVE_THUMBS"', script)

    def test_cn_publish_refuses_singapore_database(self):
        with self.assertRaisesRegex(RuntimeError, "pma_synology"):
            publisher.validate_cn_database_url("postgresql://pma:secret@db/pma_sa")

        publisher.validate_cn_database_url("postgresql://pma:secret@db/pma_synology")

    def test_uploads_original_ppt_to_deterministic_cn_course_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "中文讲义.pptx"
            source.write_bytes(b"ppt-content")
            client = FakeWebDav()

            remote = publisher.upload_original_ppt(
                client, source, "apac-data-center-critical-comms-cn"
            )

            self.assertEqual(remote, "/courses/apac-data-center-critical-comms-cn.pptx")
            self.assertEqual(
                client.uploads,
                [(b"ppt-content", "/courses/apac-data-center-critical-comms-cn.pptx")],
            )

    def test_applies_interactive_and_download_metadata_without_duplication_fields(self):
        manifest = {
            "key": "apac-dc-cn",
            "download_key": "apac-dc-cn-ppt",
            "title": "亚太数据中心关键通信",
            "subtitle": "中文培训 · 26 讲",
            "desc": "课程说明",
            "topic": "行业知识",
            "accent": "#0C5663",
            "cover": "cover.png",
            "pages": [{"label": "一", "notes": "讲义", "image": "1.webp"}],
        }
        interactive = SimpleNamespace()
        download = SimpleNamespace()

        publisher.apply_interactive_metadata(interactive, manifest, has_thumbs=True)
        publisher.apply_download_metadata(
            download, manifest, "/courses/apac-dc-cn.pptx", 27_000_000, "/courses/covers/apac-dc-cn.png"
        )

        self.assertEqual(interactive.key, "apac-dc-cn")
        self.assertEqual(interactive.media_type, "html")
        self.assertEqual(interactive.page_count, 1)
        self.assertTrue(interactive.has_thumbs)
        self.assertEqual(download.key, "apac-dc-cn-ppt")
        self.assertEqual(download.media_type, "ppt")
        self.assertEqual(download.media_url, "/courses/apac-dc-cn.pptx")
        self.assertEqual(download.file_size, 27_000_000)
        self.assertEqual(download.title, "亚太数据中心关键通信")
        self.assertEqual(download.subtitle, "PPT · 1 页")
        self.assertNotIn("讲义", download.title + download.subtitle)

    def test_ppt_download_cards_prefer_the_uploaded_cover(self):
        template = WIKI_TEMPLATE_PATH.read_text(encoding="utf-8")
        ppt_panel = template.split("{# ── PPT 下载 ── #}", 1)[1]

        cover_check = ppt_panel.index("{% if c.cover_url %}")
        cover_route = ppt_panel.index("knowledge_wiki.course_cover")
        fallback = ppt_panel.index('<div class="kb-mark">EVERTAC')
        self.assertLess(cover_check, cover_route)
        self.assertLess(cover_route, fallback)

    def test_uploads_cover_with_its_real_file_extension(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "cover.png"
            source.write_bytes(b"png-content")
            client = FakeWebDav()

            remote = publisher.upload_cover(client, source, "apac-dc-cn")

            self.assertEqual(remote, "/courses/covers/apac-dc-cn.png")
            self.assertEqual(client.uploads, [(b"png-content", remote)])


if __name__ == "__main__":
    unittest.main()
