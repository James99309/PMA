import json
import re
import sys
import tempfile
import unittest
from pathlib import Path


LIB = Path(__file__).resolve().parents[2] / "deploy" / "knowledge-content" / "lib"
sys.path.insert(0, str(LIB))

from build_apac_dc_course import build_course_html  # noqa: E402


class BuildApacDcCourseTest(unittest.TestCase):
    def test_cn_manifest_has_26_rendered_pages_and_notes(self):
        manifest_path = (
            Path(__file__).resolve().parents[2]
            / "deploy"
            / "knowledge-content"
            / "assets"
            / "apac-dc-cn"
            / "manifest.json"
        )
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

        self.assertEqual(len(manifest["pages"]), 26)
        self.assertTrue(all(page["label"].strip() for page in manifest["pages"]))
        self.assertTrue(all(page["notes"].strip() for page in manifest["pages"]))
        self.assertTrue(
            all((manifest_path.parent / page["image"]).is_file() for page in manifest["pages"])
        )
        self.assertTrue(
            all((manifest_path.parent / page["thumb"]).is_file() for page in manifest["pages"])
        )

    def test_builds_self_contained_course_with_server_readable_notes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "slide-01.webp").write_bytes(b"RIFFfake-webp")
            manifest = {
                "title": "亚太数据中心关键通信",
                "subtitle": "中文培训课件",
                "pages": [
                    {
                        "label": "园区统一架构",
                        "notes": "统一核心，避免一期、二期被切成碎片。",
                        "image": "slide-01.webp",
                    }
                ],
            }
            manifest_path = root / "manifest.json"
            manifest_path.write_text(json.dumps(manifest, ensure_ascii=False), encoding="utf-8")
            output = root / "course.html"

            count = build_course_html(manifest_path, output)

            html = output.read_text(encoding="utf-8")
            packed = re.search(
                r'<script type="__bundler/template"[^>]*>(.*?)</script>', html, re.S
            ).group(1)
            notes_template = json.loads(packed)
            self.assertEqual(count, 1)
            self.assertIn("亚太数据中心关键通信", html)
            self.assertIn('data-label="园区统一架构"', notes_template)
            self.assertIn(
                'data-speaker-notes="统一核心，避免一期、二期被切成碎片。"',
                notes_template,
            )
            self.assertIn("data:image/webp;base64,UklGRmZha2Utd2VicA==", html)
            self.assertIn('type="__bundler/template"', html)
            self.assertIn("location.hash", html)
            self.assertNotIn("slide-01.webp\"", html)

    def test_rejects_manifest_page_whose_image_is_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest_path = root / "manifest.json"
            manifest_path.write_text(
                json.dumps(
                    {
                        "title": "课程",
                        "pages": [{"label": "第一页", "notes": "讲义", "image": "missing.webp"}],
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(FileNotFoundError, "missing.webp"):
                build_course_html(manifest_path, root / "course.html")

    def test_builds_english_course_chrome_from_manifest_language(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "slide-01.webp").write_bytes(b"RIFFfake-webp")
            manifest_path = root / "manifest.json"
            manifest_path.write_text(
                json.dumps(
                    {
                        "lang": "en",
                        "title": "Critical Communications",
                        "pages": [
                            {
                                "label": "One campus, one architecture",
                                "notes": "Plan the core before the buildings.",
                                "image": "slide-01.webp",
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            build_course_html(manifest_path, root / "course.html")

            output = (root / "course.html").read_text(encoding="utf-8")
            self.assertIn('<html lang="en">', output)
            self.assertIn('aria-label="Previous slide"', output)
            self.assertIn('aria-label="Next slide"', output)


if __name__ == "__main__":
    unittest.main()
