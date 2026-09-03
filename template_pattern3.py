"""作業区分ごとに写真を配置する2ページレイアウト。"""

from __future__ import annotations

import os

from templates.base import BaseTemplate


class TemplatePattern3(BaseTemplate):
    """Before/Afterを使用せず、ファイル名の区分で配置する。"""

    SHEET_NAME = "CategoryPhotoReport"
    PAGE_LAYOUT = [
        [
            "エントランス清掃",
            "エントランス清掃",
            "設備清掃",
            "共用部清掃",
        ],
        [
            "駐輪場清掃",
            "駐車場清掃",
            "ごみ置き場清掃",
        ],
    ]

    def _get_images_by_category(self, base_folder: str) -> dict[str, list[str]]:
        categories = {
            category
            for page in self.PAGE_LAYOUT
            for category in page
        }
        category_images: dict[str, list[str]] = {
            category: [] for category in categories
        }

        for file_name in sorted(os.listdir(base_folder)):
            if not file_name.casefold().endswith((".jpg", ".jpeg", ".png")):
                continue
            matched = False
            for category in categories:
                if file_name.startswith(category):
                    category_images[category].append(
                        os.path.join(base_folder, file_name)
                    )
                    matched = True
                    break
            if not matched:
                raise ValueError(f"作業区分を判定できない写真です: {file_name}")

        return category_images

    def apply(self, base_folder: str) -> None:
        category_images = self._get_images_by_category(base_folder)
        required_counts: dict[str, int] = {}
        for page in self.PAGE_LAYOUT:
            for category in page:
                required_counts[category] = required_counts.get(category, 0) + 1

        errors = []
        for category, required in required_counts.items():
            actual = len(category_images[category])
            if actual != required:
                errors.append(
                    f"{category}: 必要{required}枚 / 実際{actual}枚"
                )
        if errors:
            raise ValueError("写真枚数が一致しません。\n" + "\n".join(errors))

        used_count = {category: 0 for category in required_counts}
        ordered_images: list[str] = []
        for page in self.PAGE_LAYOUT:
            for category in page:
                index = used_count[category]
                ordered_images.append(category_images[category][index])
                used_count[category] += 1

        self.writer.paste_images_in_order(self.SHEET_NAME, ordered_images)
