"""公開用のサンプル設定。

このファイルに登場する依頼元コード、物件名、ファイル名はすべて架空です。
実際の業務データや顧客情報は含めていません。
"""

from __future__ import annotations

import os
import re
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent

# 環境変数を設定すると、コードを変更せず保存場所を切り替えられます。
BASE_PHOTOS_FOLDER = Path(
    os.getenv("PHOTO_REPORT_PHOTOS_DIR", BASE_DIR / "photos")
)
TEMPLATES_MASTER_DIR = Path(
    os.getenv("PHOTO_REPORT_TEMPLATES_DIR", BASE_DIR / "templates_master")
)
OUTPUT_BASE = Path(
    os.getenv("PHOTO_REPORT_OUTPUT_DIR", BASE_DIR / "outputs")
)


# (依頼元コード, パターン番号) → 処理対象名
# client_alpha ～ client_epsilon は、公開用に作成した架空の依頼元コードです。
PATTERN_GROUPS: dict[tuple[str, int], list[str]] = {
    ("client_alpha", 1): [
        "サンプル物件A01",
        "サンプル物件A02",
    ],
    ("client_alpha", 5): [
        "サンプル物件A03",
    ],
    ("client_beta", 2): [
        "サンプル報告書B01",
        "サンプル報告書B02",
    ],
    ("client_gamma", 3): [
        "サンプル物件C01",
        "サンプル物件C02",
    ],
    ("client_delta", 4): [
        "サンプル物件D01",
        "サンプル物件D02",
        "サンプル物件D03",
        "サンプル物件D04",
    ],
    ("client_epsilon", 1): [
        "サンプル物件E01",
        "サンプル物件E02",
    ],
}


# パターン2は、1つの報告書に複数物件をまとめて配置します。
PATROL_GROUPS: dict[str, list[str]] = {
    "サンプル報告書B01": [
        "サンプル物件B01",
        "サンプル物件B02",
    ],
    "サンプル報告書B02": [
        "サンプル物件B03",
        "サンプル物件B04",
    ],
}

PATROL_REPORTS = list(PATROL_GROUPS)


# パターン4は、複数物件が1つのエリア別Excelを共有します。
AREA_TEMPLATE_MAP: dict[str, str] = {
    "サンプル物件D01": "サンプルエリア01_定期報告書.xlsm",
    "サンプル物件D02": "サンプルエリア01_定期報告書.xlsm",
    "サンプル物件D03": "サンプルエリア02_定期報告書.xlsm",
    "サンプル物件D04": "サンプルエリア02_定期報告書.xlsm",
}


def _normalize_name(name: str) -> str:
    """照合用に半角・全角スペースを除去する。"""
    return name.replace(" ", "").replace("\u3000", "")


def get_template_path(client_code: str, target_name: str) -> str:
    """対象名に対応するExcelテンプレートのパスを返す。

    ファイル名の先頭に ``2026.01.01`` のような日付が付いている場合も、
    日付部分を除外して照合します。
    """
    search_dir = TEMPLATES_MASTER_DIR / client_code
    target = _normalize_name(target_name)

    if search_dir.is_dir():
        for file_path in search_dir.iterdir():
            if file_path.suffix.casefold() != ".xlsm":
                continue

            name_without_date = re.sub(
                r"^\d{4}\.\d{1,2}\.\d{1,2}\s*",
                "",
                file_path.stem,
            )
            if _normalize_name(name_without_date) == target:
                return str(file_path)

    return str(search_dir / f"{target_name}.xlsm")


def get_patrol_group(client_code: str, report_name: str) -> list[str]:
    """パターン2の報告書に含める物件を掲載順で返す。"""
    if client_code != "client_beta" or report_name not in PATROL_GROUPS:
        return []
    return PATROL_GROUPS[report_name].copy()


def get_area_template_path(property_name: str) -> str:
    """パターン4の物件が使用するエリア別テンプレートを返す。"""
    file_name = AREA_TEMPLATE_MAP.get(property_name)
    if not file_name:
        raise ValueError(
            f"「{property_name}」のエリア別テンプレートが登録されていません。"
        )
    return str(TEMPLATES_MASTER_DIR / "client_delta" / file_name)


def get_area_output_name(property_name: str) -> str:
    """パターン4の出力ファイル名を返す。"""
    file_name = AREA_TEMPLATE_MAP.get(property_name)
    if not file_name:
        raise ValueError(
            f"「{property_name}」のエリア別テンプレートが登録されていません。"
        )
    return Path(file_name).stem


def get_area_group(property_name: str) -> list[str]:
    """同じエリア別テンプレートを共有する物件名を返す。"""
    file_name = AREA_TEMPLATE_MAP.get(property_name)
    if not file_name:
        raise ValueError(
            f"「{property_name}」のエリア別テンプレートが登録されていません。"
        )
    return [
        name
        for name, mapped_file in AREA_TEMPLATE_MAP.items()
        if mapped_file == file_name
    ]


PROPERTY_CONFIG: dict[str, tuple[str, int]] = {
    property_name: (client_code, pattern)
    for (client_code, pattern), property_names in PATTERN_GROUPS.items()
    for property_name in property_names
}

CLIENT_CODES = sorted({client_code for client_code, _ in PATTERN_GROUPS})
