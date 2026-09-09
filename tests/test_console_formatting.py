from __future__ import annotations

import unittest

from moretzslmcontrol.userinterface.main_window import MainWindow


class ConsoleFormattingTest(unittest.TestCase):
    def test_import_error_uses_error_level(self) -> None:
        level, message = MainWindow._console_level_and_message(
            "Error importing base aberration: cannot identify image file"
        )

        self.assertEqual(level, "error")
        self.assertEqual(message, "importing base aberration: cannot identify image file")

    def test_colon_separated_level_is_removed_from_message(self) -> None:
        level, message = MainWindow._console_level_and_message("Warning: test warning")

        self.assertEqual(level, "warning")
        self.assertEqual(message, "test warning")


if __name__ == "__main__":
    unittest.main()
