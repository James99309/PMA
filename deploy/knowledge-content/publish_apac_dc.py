#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Publish the CN or SG APAC data-centre critical-communications training package.

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


def package_config(market):
    packages = {
        "cn": {
            "assets": HERE / "assets" / "apac-dc-cn",
            "database": "pma_synology",
            "db_type": "sp8d",
            "target": "CN",
            "build_name": "apac-cn",
        },
        "sg": {
            "assets": HERE / "assets" / "apac-dc-en",
            "database": "pma_sa",
            "db_type": "ovs",
            "target": "SG",
            "build_name": "apac-sg",
        },
    }
    return packages[market]


def load_manifest(assets=ASSETS):
    return json.loads((Path(assets) / "manifest.json").read_text(encoding="utf-8"))


def project_root():
    return HERE.parent.parent


def validate_database_url(database_url, expected_database, target):
    database_name = urlparse(database_url).path.strip("/")
    if database_name != expected_database:
        raise RuntimeError(
            f"{target} course publishing requires database {expected_database}, "
            f"got {database_name or 'unknown'}"
        )


def validate_cn_database_url(database_url):
    validate_database_url(database_url, "pma_synology", "CN")


def validate_target_environment(database_url, db_type, package):
    validate_database_url(database_url, package["database"], package["target"])
    if db_type != package["db_type"]:
        raise RuntimeError(
            f"{package['target']} course publishing requires "
            f"PMA_DB_TYPE={package['db_type']}, got {db_type or 'unset'}"
        )


def build_reader(manifest, assets=ASSETS, build_dir=BUILD_DIR):
    assets = Path(assets)
    output = Path(build_dir) / f"{manifest['key']}.html"
    count = build_course_html(assets / "manifest.json", output)
    if count != len(manifest["pages"]):
        raise RuntimeError(f"page count mismatch: built={count} manifest={len(manifest['pages'])}")
    return output


def place_interactive_assets(manifest, html_path, assets=ASSETS):
    assets = Path(assets)
    course_assets = project_root() / "app" / "course_assets"
    course_assets.mkdir(parents=True, exist_ok=True)
    shutil.copy2(html_path, course_assets / f"{manifest['key']}.html")
    thumbs = course_assets / f"{manifest['key']}.thumbs"
    thumbs.mkdir(parents=True, exist_ok=True)
    for index, page in enumerate(manifest["pages"], 1):
        shutil.copy2(assets / page["thumb"], thumbs / f"{index}.png")
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


def _remote_paths(manifest, assets):
    cover_suffix = (Path(assets) / manifest["cover"]).suffix.lower()
    return (
        f"/courses/{manifest['key']}.pptx",
        f"/courses/covers/{manifest['key']}{cover_suffix}",
    )


def snapshot_remote_files(client, remote_paths):
    snapshots = {}
    for remote_path in remote_paths:
        existed = client.file_exists_strict(remote_path)
        content = client.download_file(remote_path) if existed else None
        if existed and content is None:
            raise RuntimeError(f"failed to back up existing WebDAV file: {remote_path}")
        snapshots[remote_path] = (existed, content)
    return snapshots


def restore_remote_files(client, snapshots):
    failures = []
    for remote_path, (existed, content) in snapshots.items():
        restored = (
            client.upload_file(content, remote_path)
            if existed
            else client.delete_file(remote_path)
        )
        if not restored:
            failures.append(remote_path)
    if failures:
        raise RuntimeError("WebDAV rollback failed: " + ", ".join(failures))


def _common_metadata(row, manifest):
    row.title = manifest["title"]
    row.desc = manifest["desc"]
    row.topic = manifest["topic"]
    row.accent = manifest["accent"]
    row.cover_page = 1


def choose_owner(users, manifest):
    desired_username = (manifest.get("owner_username") or "").strip()
    if desired_username:
        for user in users:
            if user.username == desired_username:
                return user
        raise RuntimeError(f"named course owner does not exist: {desired_username}")
    for user in users:
        if user.role == "admin":
            return user
    if users:
        return users[0]
    raise RuntimeError("no admin or CEO account is available to own the course")


def resolve_owner_id(manifest):
    sys.path.insert(0, str(project_root()))
    from app import create_app
    from app.models.user import User

    app = create_app()
    with app.app_context():
        managers = User.query.filter(User.role.in_(("admin", "ceo"))).order_by(User.id).all()
        return choose_owner(managers, manifest).id


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
    slide_count = manifest.get("source_slide_count") or len(manifest["pages"])
    row.subtitle = (
        f"PPT · {slide_count} slides"
        if manifest.get("lang") == "en"
        else f"PPT · {slide_count} 页"
    )
    row.media_type = "ppt"
    row.media_url = media_url
    row.cover_url = cover_url
    row.file_size = file_size
    row.page_count = 0
    row.has_thumbs = False


def register_courses_and_wiki(
    manifest, media_url, cover_url, has_thumbs, assets=ASSETS, owner_id=None
):
    assets = Path(assets)
    sys.path.insert(0, str(project_root()))
    from app import create_app, db
    from app.models.course import InteractiveCourse
    from app.services.course_knowledge import ingest_course_knowledge
    from app.services.wiki.paths import wiki_article_path

    app = create_app()
    with app.app_context():
        if owner_id is None:
            from app.models.user import User
            managers = User.query.filter(User.role.in_(("admin", "ceo"))).order_by(User.id).all()
            owner_id = choose_owner(managers, manifest).id

        article_path = wiki_article_path(manifest["topic"], (manifest["key"] + "-deck")[:200])
        article_existed = article_path.exists()
        article_content = article_path.read_bytes() if article_existed else None
        try:
            interactive = InteractiveCourse.query.filter_by(key=manifest["key"]).first()
            if not interactive:
                interactive = InteractiveCourse(key=manifest["key"], owner_id=owner_id)
                db.session.add(interactive)
            apply_interactive_metadata(interactive, manifest, has_thumbs)

            download = InteractiveCourse.query.filter_by(key=manifest["download_key"]).first()
            if not download:
                download = InteractiveCourse(key=manifest["download_key"], owner_id=owner_id)
                db.session.add(download)
            source_ppt = assets / manifest["source_ppt"]
            apply_download_metadata(
                download, manifest, media_url, source_ppt.stat().st_size, cover_url
            )
            db.session.flush()

            article = ingest_course_knowledge(
                interactive.to_dict(), manifest["pages"], manifest["topic"], owner_id,
                scope="company", commit=False,
            )
            interactive.article_id = article.id
            db.session.commit()
            return interactive.id, download.id, article.id
        except Exception:
            db.session.rollback()
            if article_existed:
                article_path.parent.mkdir(parents=True, exist_ok=True)
                article_path.write_bytes(article_content)
            elif article_path.exists():
                article_path.unlink()
            raise


def publish_remote_and_register(
    client, manifest, assets, has_thumbs, owner_id, register_fn=None
):
    assets = Path(assets)
    register_fn = register_fn or register_courses_and_wiki
    snapshots = snapshot_remote_files(client, _remote_paths(manifest, assets))
    try:
        media_url = upload_original_ppt(
            client, assets / manifest["source_ppt"], manifest["key"]
        )
        cover_url = upload_cover(client, assets / manifest["cover"], manifest["key"])
        ids = register_fn(
            manifest, media_url, cover_url, has_thumbs, assets, owner_id=owner_id
        )
        return media_url, ids
    except Exception as publish_error:
        try:
            restore_remote_files(client, snapshots)
        except Exception as rollback_error:
            raise RuntimeError(f"{publish_error}; {rollback_error}") from publish_error
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--market", choices=("cn", "sg"), default="cn")
    parser.add_argument("--commit", action="store_true", help="upload and write course records")
    parser.add_argument("--skip-assets", action="store_true", help="host already placed HTML and cover")
    parser.add_argument("--has-thumbs", action="store_true", help="host placed the cover thumbnail")
    args = parser.parse_args()

    package = package_config(args.market)
    assets = package["assets"]
    build_dir = Path(
        os.environ.get("APAC_DC_BUILD_DIR") or HERE / ".build" / package["build_name"]
    )
    manifest = load_manifest(assets)
    html_path = build_reader(manifest, assets, build_dir)
    print(f"[1/4] built {len(manifest['pages'])} pages: {html_path}")
    if not args.commit:
        print("[2-4/4] preview mode: skipped asset placement, WebDAV upload and database writes")
        return
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        raise SystemExit("DATABASE_URL is required for --commit")
    validate_target_environment(database_url, os.environ.get("PMA_DB_TYPE"), package)

    # Resolve the named uploader before any host, WebDAV or database mutation.
    owner_id = resolve_owner_id(manifest)

    has_thumbs = args.has_thumbs
    if args.skip_assets:
        print("[2/4] host already placed course HTML and cover")
    else:
        has_thumbs = place_interactive_assets(manifest, html_path, assets)
        print("[2/4] placed interactive course HTML and cover")

    sys.path.insert(0, str(project_root()))
    from app import create_app
    from app.utils.synology_webdav_client import get_synology_webdav_client

    app = create_app()
    with app.app_context():
        client = get_synology_webdav_client()
        media_url, ids = publish_remote_and_register(
            client, manifest, assets, has_thumbs, owner_id
        )
    print(f"[3/4] uploaded original PPT: {media_url}")

    interactive_id, download_id, article_id = ids
    print(
        f"[4/4] registered interactive={interactive_id}, download={download_id}, wiki={article_id}\n"
        f"course: /wiki/play/{manifest['key']}"
    )


if __name__ == "__main__":
    main()
