#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Publish the CN APAC data-centre critical-communications training package.

The package creates one interactive HTML course, derives its speaker notes into
the Wiki, and registers the original PPT as a separate downloadable course.
"""

import argparse
import json
import os
import shutil
import sys
from pathlib import Path
from urllib.parse import urlparse


HERE = Path(__file__).resolve().parent
LIB = HERE / "lib"
ASSETS = HERE / "assets" / "apac-dc-cn"
MANIFEST_PATH = ASSETS / "manifest.json"
BUILD_DIR = Path(os.environ.get("APAC_DC_BUILD_DIR") or HERE / ".build" / "apac-cn")
sys.path.insert(0, str(LIB))

from build_apac_dc_course import build_course_html  # noqa: E402


def load_manifest():
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def project_root():
    return HERE.parent.parent


def validate_cn_database_url(database_url):
    database_name = urlparse(database_url).path.strip("/")
    if database_name != "pma_synology":
        raise RuntimeError(
            f"CN course publishing requires database pma_synology, got {database_name or 'unknown'}"
        )


def build_reader(manifest):
    output = BUILD_DIR / f"{manifest['key']}.html"
    count = build_course_html(MANIFEST_PATH, output)
    if count != len(manifest["pages"]):
        raise RuntimeError(f"page count mismatch: built={count} manifest={len(manifest['pages'])}")
    return output


def place_interactive_assets(manifest, html_path):
    course_assets = project_root() / "app" / "course_assets"
    course_assets.mkdir(parents=True, exist_ok=True)
    shutil.copy2(html_path, course_assets / f"{manifest['key']}.html")
    thumbs = course_assets / f"{manifest['key']}.thumbs"
    thumbs.mkdir(parents=True, exist_ok=True)
    for index, page in enumerate(manifest["pages"], 1):
        shutil.copy2(ASSETS / page["thumb"], thumbs / f"{index}.png")
    return True


def upload_original_ppt(client, source_path, course_key):
    source_path = Path(source_path)
    remote = f"/courses/{course_key}.pptx"
    if not client.is_configured:
        raise RuntimeError("NAS WebDAV storage is not configured")
    if not client.upload_file(source_path.read_bytes(), remote):
        raise RuntimeError(f"failed to upload {source_path.name} to {remote}")
    return remote


def upload_cover(client, source_path, course_key):
    source_path = Path(source_path)
    remote = f"/courses/covers/{course_key}{source_path.suffix.lower()}"
    if not client.is_configured:
        raise RuntimeError("NAS WebDAV storage is not configured")
    if not client.upload_file(source_path.read_bytes(), remote):
        raise RuntimeError(f"failed to upload cover to {remote}")
    return remote


def _common_metadata(row, manifest):
    row.title = manifest["title"]
    row.desc = manifest["desc"]
    row.topic = manifest["topic"]
    row.accent = manifest["accent"]
    row.cover_page = 1


def apply_interactive_metadata(row, manifest, has_thumbs):
    row.key = manifest["key"]
    _common_metadata(row, manifest)
    row.subtitle = manifest["subtitle"]
    row.media_type = "html"
    row.media_url = None
    row.cover_url = None
    row.page_count = len(manifest["pages"])
    row.has_thumbs = bool(has_thumbs)


def apply_download_metadata(row, manifest, media_url, file_size, cover_url):
    row.key = manifest["download_key"]
    _common_metadata(row, manifest)
    row.title = manifest["title"]
    row.subtitle = f"PPT · {len(manifest['pages'])} 页"
    row.media_type = "ppt"
    row.media_url = media_url
    row.cover_url = cover_url
    row.file_size = file_size
    row.page_count = 0
    row.has_thumbs = False


def register_courses_and_wiki(manifest, media_url, cover_url, has_thumbs):
    sys.path.insert(0, str(project_root()))
    from app import create_app, db
    from app.models.course import InteractiveCourse
    from app.models.user import User
    from app.services.course_knowledge import ingest_course_knowledge

    app = create_app()
    with app.app_context():
        admin = User.query.filter_by(role="admin").first()
        owner_id = admin.id if admin else None

        interactive = InteractiveCourse.query.filter_by(key=manifest["key"]).first()
        if not interactive:
            interactive = InteractiveCourse(key=manifest["key"], owner_id=owner_id)
            db.session.add(interactive)
        apply_interactive_metadata(interactive, manifest, has_thumbs)

        download = InteractiveCourse.query.filter_by(key=manifest["download_key"]).first()
        if not download:
            download = InteractiveCourse(key=manifest["download_key"], owner_id=owner_id)
            db.session.add(download)
        source_ppt = ASSETS / manifest["source_ppt"]
        apply_download_metadata(download, manifest, media_url, source_ppt.stat().st_size, cover_url)
        db.session.commit()

        article = ingest_course_knowledge(
            interactive.to_dict(), manifest["pages"], manifest["topic"], owner_id, scope="company"
        )
        interactive.article_id = article.id
        db.session.commit()
        return interactive.id, download.id, article.id


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--commit", action="store_true", help="upload and write CN course records")
    parser.add_argument("--skip-assets", action="store_true", help="host already placed HTML and cover")
    parser.add_argument("--has-thumbs", action="store_true", help="host placed the cover thumbnail")
    args = parser.parse_args()

    manifest = load_manifest()
    html_path = build_reader(manifest)
    print(f"[1/4] built {len(manifest['pages'])} pages: {html_path}")
    if not args.commit:
        print("[2-4/4] preview mode: skipped asset placement, WebDAV upload and database writes")
        return
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        raise SystemExit("DATABASE_URL is required for --commit")
    validate_cn_database_url(database_url)

    has_thumbs = args.has_thumbs
    if args.skip_assets:
        print("[2/4] host already placed course HTML and cover")
    else:
        has_thumbs = place_interactive_assets(manifest, html_path)
        print("[2/4] placed interactive course HTML and cover")

    sys.path.insert(0, str(project_root()))
    from app import create_app
    from app.utils.synology_webdav_client import get_synology_webdav_client

    app = create_app()
    with app.app_context():
        client = get_synology_webdav_client()
        source_ppt = ASSETS / manifest["source_ppt"]
        media_url = upload_original_ppt(client, source_ppt, manifest["key"])
        cover_url = upload_cover(client, ASSETS / manifest["cover"], manifest["key"])
    print(f"[3/4] uploaded original PPT: {media_url}")

    interactive_id, download_id, article_id = register_courses_and_wiki(
        manifest, media_url, cover_url, has_thumbs
    )
    print(
        f"[4/4] registered interactive={interactive_id}, download={download_id}, wiki={article_id}\n"
        f"course: /wiki/play/{manifest['key']}"
    )


if __name__ == "__main__":
    main()
