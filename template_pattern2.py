"""複数物件を1枚の月次報告書へまとめるレイアウト。"""

import os

from core.sorter import BeforeAfterSorter
from templates.base import BaseTemplate


class TemplatePattern2(BaseTemplate):
    """物件ごとにBefore 5枚・After 5枚を縦方向へ配置する。"""

    SHEET_KEYWORD = "MonthlyPhotoReport"
    IMAGES_PER_SIDE = 5
    PICTURE_NAME_PREFIX = "Picture"

    def _get_sheet_name(self) -> str:
        for sheet in self.writer.wb.Sheets:
            if self.SHEET_KEYWORD in sheet.Name:
                return sheet.Name
        raise ValueError(
            f"シート名に「{self.SHEET_KEYWORD}」を含むシートがありません。"
        )

    def apply(self, base_folders: list[str]) -> None:
        sheet_name = self._get_sheet_name()
        worksheet = self.writer.wb.Sheets(sheet_name)
        all_shapes = self.writer._get_picture_shapes(
            worksheet,
            name_prefix=self.PICTURE_NAME_PREFIX,
        )
        all_shapes.sort(key=lambda shape: shape.Top)

        slots_per_property = self.IMAGES_PER_SIDE * 2
        expected_slots = len(base_folders) * slots_per_property
        if len(all_shapes) != expected_slots:
            raise ValueError(
                "写真枠の総数が一致しません。"
                f"必要: {expected_slots}個 / 実際: {len(all_shapes)}個"
            )

        for index, base_folder in enumerate(base_folders):
            sorter = BeforeAfterSorter(base_folder)
            before_images, after_images = sorter.get_validated_images(
                self.IMAGES_PER_SIDE
            )

            start = index * slots_per_property
            property_shapes = all_shapes[start : start + slots_per_property]
            left_group, right_group = self.writer._split_left_right(property_shapes)
            property_label = os.path.basename(os.path.normpath(base_folder))

            self.writer._paste_one_group(
                worksheet,
                left_group,
                before_images,
                f"{property_label}_Before",
            )
            self.writer._paste_one_group(
                worksheet,
                right_group,
                after_images,
                f"{property_label}_After",
            )
