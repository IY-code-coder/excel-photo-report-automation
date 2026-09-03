"""複数物件を含むエリア別Excelへ写真を配置するレイアウト。"""

import os

from core.excel_workbook_editor import MSO_LINKED_PICTURE, MSO_PICTURE
from templates.base import BaseTemplate


class TemplatePattern4(BaseTemplate):
    """1つのExcelを開いたまま、同じエリアの複数物件を処理する。"""

    SUBFOLDERS = ("①", "②")
    MIN_SHAPE_WIDTH = 150

    def _find_sheet(self, sheet_name: str):
        for sheet in self.writer.wb.Sheets:
            if sheet.Name == sheet_name:
                return sheet
        raise ValueError(f"シート「{sheet_name}」が見つかりません。")

    @staticmethod
    def _get_images(folder: str) -> list[str]:
        if not os.path.isdir(folder):
            raise FileNotFoundError(f"写真フォルダが見つかりません → {folder}")
        return [
            os.path.join(folder, file_name)
            for file_name in sorted(os.listdir(folder))
            if file_name.casefold().endswith((".jpg", ".jpeg", ".png"))
            and os.path.isfile(os.path.join(folder, file_name))
        ]

    def _apply_to_sheet(self, worksheet, images: list[str], label: str) -> None:
        shapes = [
            shape
            for shape in worksheet.Shapes
            if shape.Type in (MSO_PICTURE, MSO_LINKED_PICTURE)
            and shape.Width > self.MIN_SHAPE_WIDTH
        ]
        shapes = self.writer._sort_reading_order(shapes)
        self.writer._paste_one_group(worksheet, shapes, images, label)

    def _apply_property(self, base_folder: str) -> None:
        property_name = os.path.basename(os.path.normpath(base_folder))
        for suffix in self.SUBFOLDERS:
            folder = os.path.join(base_folder, suffix)
            sheet_name = f"{property_name}{suffix}"
            worksheet = self._find_sheet(sheet_name)
            images = self._get_images(folder)
            self._apply_to_sheet(worksheet, images, sheet_name)

    def apply(self, base_folder: str) -> None:
        self._apply_property(base_folder)

    def apply_multiple(self, base_folders: list[str]) -> None:
        for base_folder in base_folders:
            print("-" * 40)
            self._apply_property(base_folder)
