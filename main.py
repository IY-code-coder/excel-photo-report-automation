"""Excel写真報告書自動作成ツールのエントリーポイント。"""

from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path

from config import (
    BASE_PHOTOS_FOLDER,
    CLIENT_CODES,
    OUTPUT_BASE,
    PATROL_REPORTS,
    PROPERTY_CONFIG,
    get_area_group,
    get_area_output_name,
    get_area_template_path,
    get_patrol_group,
    get_template_path,
)
from templates.template_pattern1 import TemplatePattern1
from templates.template_pattern2 import TemplatePattern2
from templates.template_pattern3 import TemplatePattern3
from templates.template_pattern4 import TemplatePattern4
from templates.template_pattern5 import TemplatePattern5


PATTERN_CLASSES = {
    1: TemplatePattern1,
    3: TemplatePattern3,
    5: TemplatePattern5,
}


def resolve_output_path(
    output_base: str | Path,
    file_name: str,
    extension: str = ".xlsm",
) -> str:
    """年月別フォルダを作成し、重複時は上書きか連番保存を選ぶ。"""
    now = datetime.now()
    month_folder = Path(output_base) / f"{now.year}年{now.month}月"
    month_folder.mkdir(parents=True, exist_ok=True)

    candidate = month_folder / f"{file_name}{extension}"
    if not candidate.exists():
        return str(candidate)

    answer = input(
        f"すでに「{candidate.name}」が存在します。上書きしますか？ (y/n): "
    ).strip().casefold()
    if answer == "y":
        return str(candidate)

    number = 2
    while True:
        numbered = month_folder / f"{file_name}_{number}{extension}"
        if not numbered.exists():
            print(f"→「{numbered.name}」として新規保存します")
            return str(numbered)
        number += 1


def process_single_property(property_name: str) -> bool:
    """パターン1・3・5の物件を1件処理する。"""
    setting = PROPERTY_CONFIG.get(property_name)
    if setting is None:
        print(f"エラー: 「{property_name}」は設定に登録されていません。")
        return False

    client_code, pattern = setting
    template_class = PATTERN_CLASSES.get(pattern)
    if template_class is None:
        print(f"エラー: パターン{pattern}は単一物件処理の対象外です。")
        return False

    property_folder = BASE_PHOTOS_FOLDER / client_code / property_name
    template_path = get_template_path(client_code, property_name)

    if not property_folder.is_dir():
        print(f"エラー: 写真フォルダが見つかりません → {property_folder}")
        return False
    if not os.path.isfile(template_path):
        print(f"エラー: テンプレートが見つかりません → {template_path}")
        return False

    template = None
    try:
        print(
            f"→ 対象: {property_name} / "
            f"依頼元コード: {client_code} / パターン: {pattern}"
        )
        output_path = resolve_output_path(OUTPUT_BASE, property_name)
        template = template_class(template_path)
        template.apply(str(property_folder))
        template.save(output_path)
        print(f"=== {property_name} 完了 ===")
        return True
    except Exception as error:
        print(f"エラー: 「{property_name}」の処理に失敗しました。\n詳細: {error}")
        return False
    finally:
        if template is not None:
            template.close()


def process_area_group(property_name: str) -> bool:
    """パターン4の同一エリア物件を、1つのExcelへまとめて処理する。"""
    setting = PROPERTY_CONFIG.get(property_name)
    if setting is None or setting[1] != 4:
        print(f"エラー: 「{property_name}」はパターン4の対象ではありません。")
        return False

    client_code, _ = setting
    try:
        template_path = get_area_template_path(property_name)
        output_name = get_area_output_name(property_name)
        group_properties = get_area_group(property_name)
    except ValueError as error:
        print(f"エラー: {error}")
        return False

    if not os.path.isfile(template_path):
        print(f"エラー: テンプレートが見つかりません → {template_path}")
        return False

    folders: list[str] = []
    missing: list[str] = []
    for name in group_properties:
        folder = BASE_PHOTOS_FOLDER / client_code / name
        if folder.is_dir():
            folders.append(str(folder))
        else:
            missing.append(name)

    if missing:
        print("エラー: 写真フォルダが見つかりません → " + ", ".join(missing))
        return False
    if not folders:
        print("エラー: 処理できる物件がありません。")
        return False

    template = None
    try:
        template = TemplatePattern4(template_path)
        template.apply_multiple(folders)
        extension = Path(template_path).suffix
        output_path = resolve_output_path(OUTPUT_BASE, output_name, extension)
        template.save(output_path)
        print(
            f"=== エリア処理完了（処理: {len(folders)}件 / "
            f"除外: {len(missing)}件） ==="
        )
        return True
    except Exception as error:
        print(f"エラー: エリア処理に失敗しました。\n詳細: {error}")
        return False
    finally:
        if template is not None:
            template.close()


def process_patrol(report_name: str) -> bool:
    """パターン2の複数物件を、掲載順に1つのExcelへ配置する。"""
    setting = PROPERTY_CONFIG.get(report_name)
    if setting is None or setting[1] != 2:
        print(f"エラー: 「{report_name}」はパターン2の対象ではありません。")
        return False

    client_code, _ = setting
    template_path = get_template_path(client_code, report_name)
    report_folder = BASE_PHOTOS_FOLDER / client_code / report_name
    order = get_patrol_group(client_code, report_name)

    if not os.path.isfile(template_path):
        print(f"エラー: テンプレートが見つかりません → {template_path}")
        return False
    if not report_folder.is_dir():
        print(f"エラー: 写真フォルダが見つかりません → {report_folder}")
        return False
    if not order:
        print(f"エラー: 「{report_name}」の掲載順が登録されていません。")
        return False

    folders = [report_folder / property_name for property_name in order]
    missing = [str(folder) for folder in folders if not folder.is_dir()]
    if missing:
        print("エラー: 次の物件フォルダが見つかりません → " + ", ".join(missing))
        return False

    template = None
    try:
        print("→ 読み込み順: " + ", ".join(order))
        output_name = input(
            f"保存ファイル名を入力してください（例: 2026年1月_{report_name}）: "
        ).strip()
        if not output_name:
            print("エラー: 保存ファイル名が入力されていません。")
            return False

        template = TemplatePattern2(template_path)
        template.apply([str(folder) for folder in folders])
        template.save(resolve_output_path(OUTPUT_BASE, output_name))
        print(f"=== {report_name} 完了 ===")
        return True
    except Exception as error:
        print(f"エラー: 「{report_name}」の処理に失敗しました。\n詳細: {error}")
        return False
    finally:
        if template is not None:
            template.close()


def process_single_mode() -> None:
    """入力された物件または報告書を1件処理する。"""
    target_name = input("対象名を入力してください: ").strip()
    setting = PROPERTY_CONFIG.get(target_name)
    if setting is None:
        print(f"エラー: 「{target_name}」は設定に登録されていません。")
        return

    pattern = setting[1]
    if pattern == 2:
        process_patrol(target_name)
    elif pattern == 4:
        process_area_group(target_name)
    else:
        process_single_property(target_name)


def process_batch_mode() -> None:
    """依頼元コード単位で対象を一括処理する。"""
    client_code = input(
        "依頼元コードを入力してください（" + "/".join(CLIENT_CODES) + "）: "
    ).strip().casefold()

    if client_code == "client_beta":
        results = {name: process_patrol(name) for name in PATROL_REPORTS}
        succeeded = [name for name, ok in results.items() if ok]
        failed = [name for name, ok in results.items() if not ok]
        print(f"完了: {len(succeeded)}件 / 失敗: {len(failed)}件")
        if failed:
            print("失敗: " + ", ".join(failed))
        return

    targets = [
        name
        for name, (registered_client, _) in PROPERTY_CONFIG.items()
        if registered_client == client_code
    ]
    if not targets:
        print(f"エラー: 「{client_code}」の対象が登録されていません。")
        return

    succeeded: list[str] = []
    failed: list[str] = []
    processed_templates: set[str] = set()

    for target_name in targets:
        pattern = PROPERTY_CONFIG[target_name][1]
        if pattern == 4:
            template_path = get_area_template_path(target_name)
            if template_path in processed_templates:
                continue
            processed_templates.add(template_path)
            ok = process_area_group(target_name)
        else:
            ok = process_single_property(target_name)

        (succeeded if ok else failed).append(target_name)

    print(f"完了: {len(succeeded)}件 / 失敗: {len(failed)}件")
    if failed:
        print("失敗: " + ", ".join(failed))


def main() -> None:
    mode = input(
        "1: 単一対象処理 / 2: 依頼元コードで一括処理 を選択してください: "
    ).strip()
    if mode == "1":
        process_single_mode()
    elif mode == "2":
        process_batch_mode()
    else:
        print("エラー: 1か2を入力してください。")


if __name__ == "__main__":
    main()
