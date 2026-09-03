import os
import re


class BeforeAfterSorter:
    """before/afterフォルダから画像を振り分けるクラス"""

    SUPPORTED_EXTENSIONS = (".jpg", ".jpeg", ".png")

    def __init__(self, base_folder: str):
        """
        Args:
            base_folder: 物件フォルダのパス（beforeフォルダ・afterフォルダを含む親フォルダ）
        """
        self.base_folder = base_folder
        self.before_folder = os.path.join(base_folder, "before")
        self.after_folder = os.path.join(base_folder, "after")

    @staticmethod
    def _natural_sort_key(file_name: str) -> list:
        """ファイルに含まれる数字を数値として並べ替えるためのキーを返す"""
        return [
            int(part) if part.isdigit() else part.casefold()
            for part in re.split(r"(\d+)", file_name)
        ]

    @staticmethod
    def _get_file_stem(image_path: str) -> str:
        """拡張子を除いたファイル名を比較用に返す"""
        file_name = os.path.basename(image_path)
        return os.path.splitext(file_name)[0].casefold()

    def _get_images(self, folder: str) -> list[str]:
        """指定フォルダから画像ファイルの一覧を自然順で取得する"""
        if not os.path.isdir(folder):
            raise FileNotFoundError(f"画像フォルダが見つかりません → {folder}")

        file_names = [
            file_name
            for file_name in os.listdir(folder)
            if file_name.lower().endswith(self.SUPPORTED_EXTENSIONS)
            and "_resized" not in file_name.lower()
            and os.path.isfile(os.path.join(folder, file_name))
        ]

        file_names.sort(key=self._natural_sort_key)

        return [os.path.join(folder, file_name) for file_name in file_names]

    def get_before_images(self) -> list[str]:
        """beforeフォルダの画像一覧を返す"""
        return self._get_images(self.before_folder)

    def get_after_images(self) -> list[str]:
        """afterフォルダの画像一覧を返す"""
        return self._get_images(self.after_folder)

    def get_validated_images(
        self,
        expected_count: int | None = None,
    ) -> tuple[list[str], list[str]]:
        """before・afterを検査し、正常な画像一覧を返す"""

        before_images = self.get_before_images()
        after_images = self.get_after_images()

        before_names = [self._get_file_stem(path) for path in before_images]
        after_names = [self._get_file_stem(path) for path in after_images]

        errors = []

        # before・afterの枚数差を確認
        if len(before_images) != len(after_images):
            errors.append(
                "beforeとafterの写真枚数が一致しません。\n"
                f"  before: {len(before_images)}枚\n"
                f"  after : {len(after_images)}枚"
            )

        # テンプレートが必要とする枚数を確認
        if expected_count is not None:
            for label, images in (
                ("before", before_images),
                ("after", after_images),
            ):
                actual_count = len(images)

                if actual_count < expected_count:
                    errors.append(
                        f"{label}の写真が不足しています。\n"
                        f"  必要: {expected_count}枚\n"
                        f"  実際: {actual_count}枚\n"
                        "  存在するファイル: "
                        + ", ".join(os.path.basename(path) for path in images)
                    )

                elif actual_count > expected_count:
                    extra_images = images[expected_count:]
                    errors.append(
                        f"{label}の写真が多すぎます。\n"
                        f"  必要: {expected_count}枚\n"
                        f"  実際: {actual_count}枚\n"
                        "  余分な可能性があるファイル: "
                        + ", ".join(
                            os.path.basename(path) for path in extra_images
                        )
                    )

        # beforeにだけある名前・afterにだけある名前を確認
        only_before = [name for name in before_names if name not in after_names]
        only_after = [name for name in after_names if name not in before_names]

        if only_before:
            errors.append("beforeにだけ存在するファイル名: " + ", ".join(only_before))

        if only_after:
            errors.append("afterにだけ存在するファイル名: " + ", ".join(only_after))

        if errors:
            property_name = os.path.basename(os.path.normpath(self.base_folder))

            raise ValueError(
                f"【{property_name}】写真検査に失敗しました。\n"
                + "\n".join(errors)
                + "\nExcelへの貼り付けと保存は行いません。"
            )

        return before_images, after_images

    def get_pairs(
        self,
        expected_count: int | None = None,
    ) -> list[tuple[str, str]]:
        """検査済みのbefore・afterをペアにして返す"""

        before_images, after_images = self.get_validated_images(expected_count)

        return list(zip(before_images, after_images))
