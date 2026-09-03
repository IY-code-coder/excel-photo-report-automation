import os
import shutil
import tempfile
import pywintypes
import win32com.client as win32

from core.image_processor import ImageProcessor

MSO_PICTURE = 13
MSO_LINKED_PICTURE = 11


class ExcelWorkbookEditor:
    """デスクトップ版Excelを操作し、写真の置換と保存を行う。"""

    def __init__(self, template_path: str, visible: bool = False):
        self.image_processor = ImageProcessor(
            max_width=1,
            max_height=1,
        )

        self.template_path = os.path.abspath(template_path)

        # テンプレートを一時フォルダにコピーしてそちらを開く
        # （元のテンプレートファイルを汚さないため）
        ext = os.path.splitext(self.template_path)[1]
        tmp = tempfile.NamedTemporaryFile(suffix=ext, delete=False)
        tmp.close()
        shutil.copy2(self.template_path, tmp.name)
        self._tmp_path = tmp.name

        self.app = win32.Dispatch("Excel.Application")
        self.app.Visible = visible
        self.app.DisplayAlerts = False
        self.wb = self.app.Workbooks.Open(self._tmp_path)

    def _split_left_right(self, placeholders):
        if len(placeholders) == 0:
            return [], []
        lefts = [s.Left for s in placeholders]
        min_left, max_left = min(lefts), max(lefts)
        threshold = (min_left + max_left) / 2
        left_group = [s for s in placeholders if s.Left <= threshold]
        right_group = [s for s in placeholders if s.Left > threshold]
        left_group.sort(key=lambda s: s.Top)
        right_group.sort(key=lambda s: s.Top)
        return left_group, right_group

    def _sort_reading_order(self, placeholders):
        return sorted(placeholders, key=lambda s: (round(s.Top), s.Left))

    def _build_slot(self, ws, shape):
        return {
            "left": shape.Left,
            "top": shape.Top,
            "width": shape.Width,
            "height": shape.Height,
        }

    def _get_picture_shapes(self, ws, name_prefix="図"):
        """シート内から名前がname_prefixで始まる画像Shapeを集めて返す"""
        pictures = []
        for shape in ws.Shapes:
            if shape.Type in (
                MSO_PICTURE,
                MSO_LINKED_PICTURE,
            ) and shape.Name.startswith(name_prefix):
                pictures.append(shape)
        return pictures

    def _paste_one_group(
        self,
        ws,
        shapes,
        images,
        label,
    ):
        """template pictureを新しい写真へ置き換える"""

        if len(shapes) != len(images):
            raise ValueError(
                f"{label}の写真数が一致しません。"
                f"template picture: {len(shapes)} 個 / "
                f"画像: {len(images)}枚"
            )

        # Excelの図形を削除すると番号がずれるため、
        # 削除前に必要な情報をすべて保存する
        paste_items = []

        for shape, img_path in zip(shapes, images):
            paste_items.append(
                {
                    "original_name": str(shape.Name),
                    "left": float(shape.Left),
                    "top": float(shape.Top),
                    "width": float(shape.Width),
                    "height": float(shape.Height),
                    "img_path": img_path,
                }
            )

        # ここからは保存した情報だけを使う
        for item in paste_items:
            original_name = item["original_name"]
            slot_left = item["left"]
            slot_top = item["top"]
            slot_width = item["width"]
            slot_height = item["height"]
            img_path = item["img_path"]

            # template pictureの縦横比
            target_ratio = slot_width / slot_height

            # template pictureと同じ比率になるよう中央を切り取る
            processed_path = self.image_processor.prepare_cropped_to_ratio(
                img_path,
                target_ratio,
            )

            # image_width, image_height = (
            #     self.image_processor.get_image_size(
            #         processed_path
            #     )
            # )

            new_picture = None

            try:
                new_picture = ws.Shapes.AddPicture(
                    Filename=os.path.abspath(processed_path),
                    LinkToFile=False,
                    SaveWithDocument=True,
                    Left=slot_left,
                    Top=slot_top,
                    Width=slot_width,
                    Height=slot_height,
                )

                new_picture.LockAspectRatio = True

                # 元のtemplate pictureの中央へ配置
                new_picture.Left = slot_left
                new_picture.Top = slot_top

                # 新しい写真を貼れた後で、
                # 名前を指定して元写真を削除する
                ws.Shapes.Item(original_name).Delete()

            except Exception:
                if new_picture is not None:
                    try:
                        new_picture.Delete()
                    except pywintypes.com_error:
                        pass
                raise

    def paste_images_lr(
        self,
        sheet_name: str,
        left_images: list[str],
        right_images: list[str],
        name_prefix: str = "図",
    ) -> None:
        ws = self.wb.Sheets(sheet_name)
        placeholders = self._get_picture_shapes(ws, name_prefix)
        if len(placeholders) == 0:
            print(f"警告: シート'{sheet_name}'にサンプル画像が見つかりません")
            return

        left_group, right_group = self._split_left_right(placeholders)
        self._paste_one_group(ws, left_group, left_images, "左(Before)")
        self._paste_one_group(ws, right_group, right_images, "右(After)")

    def paste_images_in_order(self, sheet_name: str, ordered_images: list[str]) -> None:
        ws = self.wb.Sheets(sheet_name)
        placeholders = self._get_picture_shapes(ws)

        if len(placeholders) == 0:
            print(f"警告: シート'{sheet_name}'にサンプル画像が見つかりません")
            return
        sorted_shapes = self._sort_reading_order(placeholders)

        self._paste_one_group(ws, sorted_shapes, ordered_images, "枠")

    def close(self) -> None:
        """保存の成否にかかわらずExcelと一時Excelを終了する"""

        workbook = getattr(self, "wb", None)
        app = getattr(self, "app", None)
        temp_path = getattr(self, "_tmp_path", None)

        # Excelファイルを閉じる
        if workbook is not None:
            try:
                workbook.Close(SaveChanges=False)
            except Exception as error:
                print(f"警告: Excelファイルを閉じる際に問題が発生しました → {error}")
            finally:
                self.wb = None

        # Excel本体を終了する
        if app is not None:
            try:
                app.Quit()
            except Exception as error:
                print(f"警告: Excelを終了する際に問題が発生しました → {error}")
            finally:
                self.app = None

        # 今回使用した一時Excelを削除する
        if temp_path and os.path.isfile(temp_path):
            try:
                os.remove(temp_path)
            except Exception as error:
                print(
                    "警告: 一時Excelを削除できませんでした → "
                    f"{temp_path}\n詳細: {error}"
                )

    def save(self, output_path: str) -> None:
        output_path = os.path.abspath(output_path)
        ext = os.path.splitext(output_path)[1].lower()
        file_format = 52 if ext == ".xlsm" else 51

        try:
            self.wb.SaveAs(output_path, FileFormat=file_format)
            print(f"完了: {output_path} に保存しました")

        except Exception as e:
            print(f"SaveAsエラー: {e}")
            print("上書き保存を試みます...")
            self.wb.Save()
            shutil.copy2(self._tmp_path, output_path)
            print(f"完了: {output_path} にコピーしました")

        finally:
            self.close()
