#!/usr/bin/env python3
"""update_manifest.py — 每日 nightly 发布后回写 bucket/cangjie-nightly.json

用法:
    python3 tools/update_manifest.py \
        --version 1.3.0-alpha.20260902010013 \
        --sdk-zip /path/to/cangjie-sdk-windows-x64-1.3.0-alpha.20260902010013.zip \
        [--hash <sha256>] \
        [--repo-root /path/to/nightly_build]

职责:
    1. 校验版本串格式，并校验 zip 文件名与版本串一致（release tag 与产物文件名必须同串，
       防止 2025-12 曾出现的 tag≠文件名 问题复发，详见 docs/scoop-support.md §3）;
    2. 确定 sha256: 优先 --hash 直传（流水线已算好时免去计算），否则用 hashlib 本地计算;
    3. 回写 manifest 的 version / url / hash 三处（保持键序、UTF-8 无 BOM、4 空格缩进）;
    4. 写回后自校验。

git add/commit/push 由调用方完成（docs/scoop-support.md §5.1），本脚本只改 manifest 文件。

环境假定: python3 必备（流水线环境保证）；仅依赖标准库（argparse/hashlib/json/re）。
退出码: 0 成功; 1 校验/自检失败; 2 命令行用法错误（argparse 标准）。
"""

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

REPO_ROOT_DEFAULT = Path(__file__).resolve().parent.parent
MANIFEST_REL = Path("bucket") / "cangjie-nightly.json"
DOWNLOAD_BASE = "https://gitcode.com/Cangjie/nightly_build/releases/download"
ASSET_PREFIX = "cangjie-sdk-windows-x64-"

VERSION_RE = re.compile(r"^[0-9.]+-[A-Za-z]+\.[0-9]+$")
SHA256_RE = re.compile(r"^[0-9a-fA-F]{64}$")


def die(msg):
    print("ERROR: " + msg, file=sys.stderr)
    sys.exit(1)


def local_sha256(path):
    """分块计算文件 sha256（252MB 级 zip 内存安全）。"""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main(argv):
    parser = argparse.ArgumentParser(
        prog="update-manifest",
        description="每日 nightly 发布后回写 bucket/cangjie-nightly.json 的 version/url/hash",
    )
    parser.add_argument(
        "--version", required=True, metavar="VER",
        help="nightly 版本串，须与 release tag 及产物文件名同串，如 1.3.0-alpha.20260902010013",
    )
    parser.add_argument(
        "--sdk-zip", required=True, metavar="ZIP",
        help="构建机上的 SDK zip 路径（用于文件名一致性校验与本地算 hash）",
    )
    parser.add_argument(
        "--hash", dest="hash_value", default=None, metavar="SHA256",
        help="可选：直接传入 zip 的 sha256（流水线已算好时免去本地计算）",
    )
    parser.add_argument(
        "--repo-root", default=str(REPO_ROOT_DEFAULT), metavar="DIR",
        help="nightly_build 仓库根目录（默认: 脚本所在目录的上一级）",
    )
    args = parser.parse_args(argv)

    version = args.version
    if not VERSION_RE.match(version):
        die("版本串格式不合法: " + version + "（应为 X.Y.Z-<pre>.<数字>）")

    repo_root = Path(args.repo_root)
    manifest_path = repo_root / MANIFEST_REL
    if not manifest_path.is_file():
        die("manifest 不存在: " + str(manifest_path))

    zip_path = Path(args.sdk_zip)
    if not zip_path.is_file():
        die("zip 不存在: " + str(zip_path))

    # 产物文件名与版本串一致性校验（tag 与文件名必须同串）
    expected_name = ASSET_PREFIX + version + ".zip"
    if zip_path.name != expected_name:
        die("zip 文件名 '" + zip_path.name + "' != 期望 '" + expected_name
            + "'（release tag 与产物文件名必须同串）")

    # sha256：--hash 直传（流水线已算好时），否则 hashlib 本地计算
    if args.hash_value:
        if not SHA256_RE.match(args.hash_value):
            die("--hash 格式不合法: " + args.hash_value + "（应为 64 位十六进制）")
        hash_value = args.hash_value.lower()
        hash_source = "--hash 直传"
    else:
        hash_value = local_sha256(zip_path)
        hash_source = "本地计算: " + str(zip_path)

    asset_url = DOWNLOAD_BASE + "/" + version + "/" + expected_name

    # 回写三处字段（保持键序与缩进；UTF-8 无 BOM）
    with open(manifest_path, encoding="utf-8") as f:
        data = json.load(f)
    data["version"] = version
    data["architecture"]["64bit"]["url"] = asset_url
    data["architecture"]["64bit"]["hash"] = hash_value
    with open(manifest_path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
        f.write("\n")

    # 自校验：重新解析并核对三处字段
    with open(manifest_path, encoding="utf-8") as f:
        check = json.load(f)
    if check["version"] != version:
        die("self-check failed: version")
    if check["architecture"]["64bit"]["hash"] != hash_value:
        die("self-check failed: hash")
    if not check["architecture"]["64bit"]["url"].endswith(expected_name):
        die("self-check failed: url")

    print("updated: " + str(manifest_path))
    print("  version : " + check["version"])
    print("  url     : " + check["architecture"]["64bit"]["url"])
    print("  hash    : " + check["architecture"]["64bit"]["hash"])
    print("  hash 来源: " + hash_source)


if __name__ == "__main__":
    main(sys.argv[1:])
