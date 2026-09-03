import hashlib
import os
import shutil
import tempfile

from PIL import Image, ImageOps

# Excelのポイント(pt)とピクセル(px)の変換比率（96dpi基準: 1pt = 96/72 px）
PT_TO_PX = 96 / 72

# リサイズ後の画像を保存する一時フォルダ
# （元の物件フォルダ内に保存すると、次回実行時にリサイズ済みファイルを
#   再度読み込んで増殖させる事故が起きるため、必ずここに分離する）
_TEMP_DIR = os.path.join(tempfile.gettempdir(), "excel_image_tool_resized")

# 起動のたびに前回分を掃除してから作り直す（肥大化防止）
if os.path.exists(_TEMP_DIR):
    shutil.rmtree(_TEMP_DIR)
os.makedirs(_TEMP_DIR, exist_ok=True)


class ImageProcessor:
    """画像の向き補正・形式変換・一時画像作成を担当するクラス"""

    def __init__(self, max_width: float, max_height: float):
        """
        Args:
            max_width : 貼り付け枠の最大幅（ピクセル基準。pt単位の場合はprocess()のunit引数で変換）
            max_height: 貼り付け枠の最大高さ（同上）
        """
        self.max_width = max_width
        self.max_height = max_height

    def is_landscape(self, image_path: str) -> bool:
        """画像が横向きかどうかを判定する

        Args:
            image_path: 画像ファイルのパス

        Returns:
            True = 横向き / False = 縦向き
        """
        with Image.open(image_path) as image:
            fixed_image = ImageOps.exif_transpose(image)
            return fixed_image.width >= fixed_image.height

    def prepare(self, image_path: str) -> str:
        """Excel貼り付け用に画像の向きと形式を整える

        Args: image_path:
            元画像のファイルパス

        Returns:
            補正後の一時画像ファイルパス
        """

        if not os.path.isfile(image_path):
            raise FileNotFoundError(f"画像が見つかりません → {image_path}")

        # 同名画像が別フォルダにあっても
        # 一時ファイル名が重ならないようにする
        abs_src = os.path.abspath(image_path)

        name_hash = hashlib.md5(abs_src.encode("utf-8")).hexdigest()[:8]

        base_name = os.path.splitext(os.path.basename(image_path))[0]

        prepared_path = os.path.join(
            _TEMP_DIR,
            f"{base_name}_{name_hash}_prepared.jpg",
        )

        try:
            with Image.open(image_path) as image:
                # スマートフォン画像などの
                # EXIF回転情報を実際の向きへ反映
                fixed_image = ImageOps.exif_transpose(image)

                # JPEGで保存できる形式へ統一
                if fixed_image.mode != "RGB":
                    fixed_image = fixed_image.convert("RGB")

                fixed_image.save(
                    prepared_path,
                    format="JPEG",
                    quality=95,
                )
                # 保存した一時画像を開き直してサイズを確認
            with Image.open(prepared_path) as saved_image:
                saved_size = saved_image.size

        except Exception as error:
            raise ValueError(
                f"画像の処理に失敗しました → {image_path}\n詳細: {error}"
            ) from error

        if not os.path.isfile(prepared_path):
            raise RuntimeError(f"処理後の画像を作成できませんでした → {prepared_path}")
        return prepared_path

    def prepare_cropped_to_ratio(
        self,
        image_path: str,
        target_ratio: float,
    ) -> str:
        """画像中央を、指定された縦横比に切り取る"""

        prepared_path = self.prepare(image_path)

        abs_src = os.path.abspath(image_path)
        hash_source = f"{abs_src}_{target_ratio:.6f}"

        name_hash = hashlib.md5(hash_source.encode("utf-8")).hexdigest()[:8]

        base_name = os.path.splitext(os.path.basename(image_path))[0]

        cropped_path = os.path.join(
            _TEMP_DIR,
            f"{base_name}_{name_hash}_cropped.jpg",
        )

        with Image.open(prepared_path) as image:
            image = image.convert("RGB")

            width, height = image.size
            current_ratio = width / height

            if current_ratio < target_ratio:
                # 縦長すぎる場合：上下を切る
                crop_height = int(width / target_ratio)
                top = (height - crop_height) // 2

                cropped_image = image.crop(
                    (
                        0,
                        top,
                        width,
                        top + crop_height,
                    )
                )

            elif current_ratio > target_ratio:
                # 横長すぎる場合：左右を切る
                crop_width = int(height * target_ratio)
                left = (width - crop_width) // 2

                cropped_image = image.crop(
                    (
                        left,
                        0,
                        left + crop_width,
                        height,
                    )
                )

            else:
                cropped_image = image.copy()

            cropped_image.save(
                cropped_path,
                format="JPEG",
                quality=95,
                dpi=(300, 300),
            )

        return cropped_path

    def get_image_size(self, image_path: str) -> tuple[int, int]:
        """画像の向き補正後の幅と高さを返す"""
        if not os.path.isfile(image_path):
            raise FileNotFoundError(f"画像が見つかりません → {image_path}")

        try:
            with Image.open(image_path) as image:
                fixed_image = ImageOps.exif_transpose(image)
                return fixed_image.size

        except Exception as error:
            raise ValueError(
                f"画像サイズを取得できませんでした → {image_path}\n詳細: {error}"
            ) from error

    def process(self, image_path: str, unit: str = "px") -> tuple[str, float, float]:
        """画像をリサイズして保存する

        Args:
            image_path: 元画像のパス
            unit: 戻り値の幅・高さの単位。"px"（ピクセル）または"pt"（Excelのポイント）

        Returns:
            (リサイズ後の画像ファイルパス, 幅, 高さ) ※幅・高さはunitで指定した単位
        """
        with Image.open(image_path) as source_image:
            image = ImageOps.exif_transpose(source_image)

            if unit == "pt":
                max_w_px = self.max_width * PT_TO_PX
                max_h_px = self.max_height * PT_TO_PX
            else:
                max_w_px = self.max_width
                max_h_px = self.max_height

            # 縦横比を保ったままリサイズ
            scale = min(max_w_px / image.width, max_h_px / image.height)
            new_w_px = int(image.width * scale)
            new_h_px = int(image.height * scale)
            image = image.resize((new_w_px * 2, new_h_px * 2), Image.LANCZOS)
            image = image.resize((new_w_px, new_h_px), Image.LANCZOS)

        # リサイズ後の画像を一時フォルダへ保存（元フォルダは汚さない）
        # ※元パスのハッシュを使い、同名ファイル(IMG_0001.jpgなど)が
        #   別フォルダ・別物件でも衝突しないようにする
        abs_src = os.path.abspath(image_path)
        name_hash = hashlib.md5(abs_src.encode("utf-8")).hexdigest()[:8]
        base_name = os.path.splitext(os.path.basename(image_path))[0]
        resized_path = os.path.join(_TEMP_DIR, f"{base_name}_{name_hash}_resized.jpg")

        print(f"リサイズ: {image.width}x{image.height}px (scale={scale:.3f})")
        image.save(resized_path, format="JPEG", quality=95, dpi=(300, 300))

        if unit == "pt":
            return resized_path, new_w_px / PT_TO_PX, new_h_px / PT_TO_PX
        else:
            return resized_path, new_w_px, new_h_px
