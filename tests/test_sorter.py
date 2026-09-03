import tempfile
import unittest
from pathlib import Path

from core.sorter import BeforeAfterSorter


class BeforeAfterSorterTest(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.base_folder = Path(self.temporary_directory.name)
        self.before_folder = self.base_folder / "before"
        self.after_folder = self.base_folder / "after"
        self.before_folder.mkdir()
        self.after_folder.mkdir()

    def tearDown(self):
        self.temporary_directory.cleanup()

    def _create_pair(self, file_name: str) -> None:
        (self.before_folder / file_name).touch()
        (self.after_folder / file_name).touch()

    def test_natural_sort_orders_numbers_as_numbers(self):
        for file_name in ("photo10.jpg", "photo2.jpg", "photo1.jpg"):
            self._create_pair(file_name)

        sorter = BeforeAfterSorter(str(self.base_folder))
        names = [Path(path).name for path in sorter.get_before_images()]

        self.assertEqual(
            names,
            ["photo1.jpg", "photo2.jpg", "photo10.jpg"],
        )

    def test_validated_images_returns_matching_pairs(self):
        for file_name in ("01.jpg", "02.jpg"):
            self._create_pair(file_name)

        sorter = BeforeAfterSorter(str(self.base_folder))
        before, after = sorter.get_validated_images(expected_count=2)

        self.assertEqual(len(before), 2)
        self.assertEqual(len(after), 2)

    def test_name_mismatch_raises_error(self):
        (self.before_folder / "01.jpg").touch()
        (self.after_folder / "02.jpg").touch()

        sorter = BeforeAfterSorter(str(self.base_folder))

        with self.assertRaisesRegex(ValueError, "beforeにだけ存在"):
            sorter.get_validated_images(expected_count=1)

    def test_missing_before_image_is_detected(self):
        (self.before_folder / "01.jpg").touch()
        (self.after_folder / "01.jpg").touch()
        (self.after_folder / "02.jpg").touch()

        sorter = BeforeAfterSorter(str(self.base_folder))

        with self.assertRaisesRegex(ValueError, "beforeの写真が不足"):
            sorter.get_validated_images(expected_count=2)

    def test_resized_files_are_ignored(self):
        self._create_pair("01.jpg")
        (self.before_folder / "01_resized.jpg").touch()

        sorter = BeforeAfterSorter(str(self.base_folder))

        self.assertEqual(len(sorter.get_before_images()), 1)


if __name__ == "__main__":
    unittest.main()
