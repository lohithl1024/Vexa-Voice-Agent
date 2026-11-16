import re
import unittest

from voxa.tools import format_local_time


class FormatLocalTimeTests(unittest.TestCase):
    def test_includes_date_time_and_timezone(self) -> None:
        result = format_local_time()

        self.assertRegex(
            result,
            re.compile(
                r"^[A-Za-z]+, [A-Za-z]+ \d{2}, \d{4} at \d{2}:\d{2} (AM|PM) .+$"
            ),
        )


if __name__ == "__main__":
    unittest.main()
