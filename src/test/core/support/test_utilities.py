#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
   @project: HsPyLib-AskAI
   @package: askai.test.core.support
      @file: test_utilities.py
   @created: Fri, 22 Mar 2024
    @author: "<B>H</B>ugo <B>S</B>aporetti <B>J</B>unior")"
      @site: "https://github.com/yorevs/hspylib")
   @license: MIT - Please refer to <https://opensource.org/licenses/MIT>

   Copyright (c) 2024, HomeSetup
"""

import sys
import unittest


class TestClass(unittest.TestCase):

    # TEST CASES ----------

    # Test singletons are the same instance.
    def test_extract_path(self) -> None:
        pass


# Program entry point.
if __name__ == "__main__":
    suite = unittest.TestLoader().loadTestsFromTestCase(TestClass)
    unittest.TextTestRunner(verbosity=2, failfast=True, stream=sys.stdout).run(suite)
