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

from askai.__classpath__ import classpath
from askai.core.model.action_plan import ActionPlan
from askai.core.model.model_result import ModelResult
from langchain_core.messages import AIMessage

from fixtures.action_plan import stub_response


class TestClass(unittest.TestCase):

    RESPONSE_FILE: Path = Path(classpath.root_dir / "test/resources/llm-responses/task-splitter.txt")

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
            ('list my downloads', self.RESPONSES[0], stub_response(0)),
            ('list my downloads', self.RESPONSES[1], stub_response(0)),
            ('hello', self.RESPONSES[2], stub_response(1)),
            ('List my downloads and let me know if there is any image.', self.RESPONSES[3], stub_response(2)),
            ('List my downloads and let me know if there is any image.', self.RESPONSES[4], stub_response(2)),
        ]
        # fmt: on

        for question, response, expected in test_cases:
            with self.subTest(response=response):
                result = ActionPlan.create(question, AIMessage(response), ModelResult.default())
                self.assertEqual(result, expected)


# Program entry point.
if __name__ == "__main__":
    suite = unittest.TestLoader().loadTestsFromTestCase(TestClass)
    unittest.TextTestRunner(verbosity=2, failfast=True, stream=sys.stdout).run(suite)
