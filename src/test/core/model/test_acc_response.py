#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
   @project: HsPyLib-AskAI
   @package: askai.test.core.support
      @file: test_utilities.py
   @created: Fri, 22 Mar 2024
    @author: "<B>H</B>ugo <B>S</B>aporetti <B>J</B>unior
      @site: "https://github.com/yorevs/hspylib")
   @license: MIT - Please refer to <https://opensource.org/licenses/MIT>

   Copyright (c) 2024, HomeSetup
"""
import sys
import unittest
from pathlib import Path

from askai.core.model.acc_response import AccResponse
from hspylib.core.tools.commons import dirname

from fixtures.acc_response_stubs import stub_response


class TestClass(unittest.TestCase):
    """TODO"""

    TEST_DIR = dirname(__file__)

    RESPONSE_FILE: Path = Path(TEST_DIR + "/resources/llm-responses/acc-response.txt")

    RESPONSE_FILE_TEXT: str = RESPONSE_FILE.read_text()

    RESPONSES: list[str] = list(filter(None, map(str.strip, RESPONSE_FILE_TEXT.split("---"))))

    # Setup tests
    def setUp(self):
        pass

    # Teardown tests
    def tearDown(self):
        pass

    # TEST CASES ----------

    def test_should_extract_and_parse_llm_responses(self):
        # fmt: off
        # Question, AI response, expected ActionPlan object.
        test_cases = [
            (self.RESPONSES[0], stub_response(0)),
        ]
        # fmt: on

        for response, expected in test_cases:
            with self.subTest(response=response):
                result = AccResponse.parse_response(response)
                self.assertEqual(result, expected)


# Program entry point.
if __name__ == "__main__":
    suite = unittest.TestLoader().loadTestsFromTestCase(TestClass)
    unittest.TextTestRunner(verbosity=2, failfast=True, stream=sys.stdout).run(suite)
