"""HEIC画像をJPEGへ変換する補助コマンド。"""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path

from PIL import Image, ImageOps


def convert_folder(source_root: Path, output_root: Path) -> tuple[int, int]:
    """フォルダ構成を保ったままHEICをJPEGへ変換する。"""
    try:
        import pillow_heif
    except ImportError as error:
        raise RuntimeError(
            "pillow-heifがインストールされていません。"
            "先に pip install -r requirements.txt を実行してください。"
        ) from error

    pillow_heif.register_heif_opener()

    converted = 0
    copied = 0

    # 出力先が変換元配下でも、生成したファイルを再処理しないよう
    # 開始時点のファイル一覧を確定します。
    source_paths = [
        path
        for path in source_root.rglob("*")
        if path.is_file() and output_root not in path.parents
    ]

    for source_path in source_paths:
        relative_path = source_path.relative_to(source_root)
        destination = output_root / relative_path
        destination.parent.mkdir(parents=True, exist_ok=True)

        if source_path.suffix.casefold() == ".heic":
            destination = destination.with_suffix(".jpg")
            with Image.open(source_path) as image:
                fixed_image = ImageOps.exif_transpose(image).convert("RGB")
                fixed_image.info.pop("exif", None)
                fixed_image.save(destination, "JPEG", quality=95)
            converted += 1
            print(f"変換完了: {destination}")
        elif source_path.suffix.casefold() in {".jpg", ".jpeg", ".png"}:
            shutil.copy2(source_path, destination)
            copied += 1

    return converted, copied


def main() -> None:
    parser = argparse.ArgumentParser(
        description="指定フォルダ内のHEICをJPEGへ一括変換します。"
    )
    parser.add_argument("source", type=Path, help="変換元フォルダ")
    parser.add_argument(
        "--output",
        type=Path,
        help="出力先。省略時は変換元フォルダ内のjpeg_outです。",
    )
    args = parser.parse_args()

    source_root = args.source.resolve()
    output_root = (args.output or source_root / "jpeg_out").resolve()

    if not source_root.is_dir():
        parser.error(f"変換元フォルダが見つかりません: {source_root}")
    if output_root == source_root or source_root in output_root.parents:
        # 出力先が変換元配下でも、rglob開始後に生成物を再取得しないよう
        # 対象一覧を先に確定する実装へ変える必要があるため禁止します。
        if output_root != source_root / "jpeg_out":
            parser.error("出力先は変換元の外側、または既定のjpeg_outを指定してください。")

    converted, copied = convert_folder(source_root, output_root)
    print(f"完了: HEIC変換 {converted}件 / 画像コピー {copied}件")


if __name__ == "__main__":
    main()
