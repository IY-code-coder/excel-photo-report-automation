"""左右にBefore・Afterを配置する基本レイアウト。"""

from core.sorter import BeforeAfterSorter
from templates.base import BaseTemplate


class TemplatePattern1(BaseTemplate):
    """左にBefore 5枚、右にAfter 5枚を配置する。"""

    SHEET_NAME = "PhotoReport"
    EXPECTED_COUNT = 5

    def apply(self, base_folder: str) -> None:
        sorter = BeforeAfterSorter(base_folder)
        before_images, after_images = sorter.get_validated_images(
            self.EXPECTED_COUNT
        )

        print(f"before: {len(before_images)}枚")
        print(f"after : {len(after_images)}枚")
        self.writer.paste_images_lr(
            self.SHEET_NAME,
            before_images,
            after_images,
        )
