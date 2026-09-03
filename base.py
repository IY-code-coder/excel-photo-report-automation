"""テンプレート処理の共通インターフェース。"""

from abc import ABC, abstractmethod

from core.excel_workbook_editor import ExcelWorkbookEditor


class BaseTemplate(ABC):
    """全レイアウトパターンの基底クラス。"""

    def __init__(self, template_path: str):
        self.template_path = template_path
        self.writer = ExcelWorkbookEditor(template_path)

    @abstractmethod
    def apply(self, image_source) -> None:
        """各レイアウトのルールに従って写真を配置する。"""

    def save(self, output_path: str) -> None:
        """編集したExcelを指定先へ保存する。"""
        self.writer.save(output_path)

    def close(self) -> None:
        """例外発生時も含め、Excelと一時ファイルを終了する。"""
        self.writer.close()
