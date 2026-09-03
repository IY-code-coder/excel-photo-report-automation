import unittest
from pathlib import Path

from config import (
    AREA_TEMPLATE_MAP,
    PROPERTY_CONFIG,
    get_area_group,
    get_area_output_name,
    get_patrol_group,
)


class ConfigTest(unittest.TestCase):
    def test_all_registered_names_have_client_and_pattern(self):
        for name, value in PROPERTY_CONFIG.items():
            self.assertTrue(name)
            self.assertEqual(len(value), 2)
            self.assertTrue(value[0].startswith("client_"))
            self.assertIn(value[1], {1, 2, 3, 4, 5})

    def test_patrol_group_returns_copy_in_display_order(self):
        group = get_patrol_group("client_beta", "サンプル報告書B01")
        self.assertEqual(group, ["サンプル物件B01", "サンプル物件B02"])

        group.append("変更")
        self.assertNotIn(
            "変更",
            get_patrol_group("client_beta", "サンプル報告書B01"),
        )

    def test_area_group_uses_same_template(self):
        property_name = "サンプル物件D01"
        template_name = AREA_TEMPLATE_MAP[property_name]
        group = get_area_group(property_name)

        self.assertGreaterEqual(len(group), 1)
        self.assertTrue(
            all(AREA_TEMPLATE_MAP[name] == template_name for name in group)
        )
        self.assertEqual(
            get_area_output_name(property_name),
            Path(template_name).stem,
        )


if __name__ == "__main__":
    unittest.main()
