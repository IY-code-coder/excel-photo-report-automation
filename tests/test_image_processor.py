import tempfile
import unittest
from pathlib import Path

from PIL import Image

from core.image_processor import ImageProcessor


class ImageProcessorTest(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.base_folder = Path(self.temporary_directory.name)

    def tearDown(self):
        self.temporary_directory.cleanup()

    def _create_image(
        self,
        path: Path,
        size: tuple[int, int] = (400, 200),
    ) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        Image.new("RGB", size, color=(80, 140, 200)).save(path)

    def test_crop_matches_target_ratio(self):
        source = self.base_folder / "source.jpg"
        self._create_image(source)
        processor = ImageProcessor(max_width=100, max_height=100)

        cropped_path = processor.prepare_cropped_to_ratio(
            str(source),
            target_ratio=1.0,
        )

        with Image.open(cropped_path) as cropped:
            self.assertEqual(cropped.size, (200, 200))

    def test_resize_keeps_aspect_ratio(self):
        source = self.base_folder / "source.jpg"
        self._create_image(source)
        processor = ImageProcessor(max_width=100, max_height=100)

        resized_path, width, height = processor.process(str(source))

        self.assertTrue(Path(resized_path).is_file())
        self.assertEqual((width, height), (100, 50))

    def test_same_name_in_different_folders_has_different_temp_path(self):
        first = self.base_folder / "first" / "photo.jpg"
        second = self.base_folder / "second" / "photo.jpg"
        self._create_image(first)
        self._create_image(second)
        processor = ImageProcessor(max_width=100, max_height=100)

        first_path = processor.prepare(str(first))
        second_path = processor.prepare(str(second))

        self.assertNotEqual(first_path, second_path)


if __name__ == "__main__":
    unittest.main()
