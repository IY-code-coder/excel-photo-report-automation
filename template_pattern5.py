"""BeforeとAfterが別シートになっている例外レイアウト。"""

import os

from core.excel_workbook_editor import MSO_LINKED_PICTURE, MSO_PICTURE
from templates.base import BaseTemplate


class TemplatePattern5(BaseTemplate):
    """作業場所名を使い、Before・Afterの各シートへ5枚配置する。"""

    SHEET_NAMES = {
        "before": "SpecialReport_Before",
        "after": "SpecialReport_After",
    }
    SLOT_ORDER = [
        "エントランス",
        "廊下",
        "階段",
        "共用部",
        "駐車場",
    ]
    MIN_SHAPE_WIDTH = 150

    @staticmethod
    def _get_images(folder: str) -> dict[str, str]:
        if not os.path.isdir(folder):
            raise FileNotFoundError(f"写真フォルダが見つかりません → {folder}")

        images: dict[str, str] = {}
        for file_name in os.listdir(folder):
            if file_name.casefold().endswith((".jpg", ".jpeg", ".png")):
                category = os.path.splitext(file_name)[0]
                if category in images:
                    raise ValueError(f"同じ作業場所の写真が複数あります: {category}")
                images[category] = os.path.join(folder, file_name)
        return images

    def _apply_to_sheet(self, sheet_name: str, images: dict[str, str]) -> None:
        missing = [category for category in self.SLOT_ORDER if category not in images]
        extra = [category for category in images if category not in self.SLOT_ORDER]
        if missing or extra:
            messages = []
            if missing:
                messages.append("不足: " + ", ".join(missing))
            if extra:
                messages.append("未登録: " + ", ".join(extra))
            raise ValueError("写真名の検査に失敗しました。" + " / ".join(messages))

        worksheet = self.writer.wb.Sheets(sheet_name)
        shapes = [
            shape
            for shape in worksheet.Shapes
            if shape.Type in (MSO_PICTURE, MSO_LINKED_PICTURE)
            and shape.Width > self.MIN_SHAPE_WIDTH
        ]
        shapes = sorted(
            shapes,
            key=lambda shape: (round(shape.Top / 20), shape.Left),
        )
        ordered_images = [images[category] for category in self.SLOT_ORDER]
        self.writer._paste_one_group(
            worksheet,
            shapes,
            ordered_images,
            sheet_name,
        )

    def apply(self, base_folder: str) -> None:
        for side, sheet_name in self.SHEET_NAMES.items():
            images = self._get_images(os.path.join(base_folder, side))
            self._apply_to_sheet(sheet_name, images)
