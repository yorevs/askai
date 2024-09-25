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
import base64
import os
import sys
import tempfile
import unittest
from pathlib import Path
from textwrap import dedent

from askai.core.support.utilities import extract_codeblock, media_type_of, extract_path, encode_image


class TestClass(unittest.TestCase):

    # Setup tests
    def setUp(self):
        Path("/tmp/newdir/with spaces").mkdir(parents=True, exist_ok=True)
        Path("/tmp/newdir").mkdir(parents=True, exist_ok=True)

    # Teardown tests
    def tearDown(self):
        os.rmdir("/tmp/newdir/with spaces")
        os.rmdir("/tmp/newdir")

    # TEST CASES ----------

    def test_extract_codeblock(self):
        # Test case 1: Code block with language specified
        text1 = dedent(
            """
        Some text before.

        ```python
        def hello_world():
            print("Hello, World!")
        ```

        Some text after.
        """
        ).strip()
        expected_language1 = "python"
        expected_code1 = 'def hello_world():\n    print("Hello, World!")'

        language1, code1 = extract_codeblock(text1)
        self.assertEqual(language1, expected_language1)
        self.assertEqual(code1, expected_code1)

        # Test case 2: Code block without language specified
        text2 = dedent(
            """
        Some text before.

        ```
        print("No language specified.")
        ```

        Some text after.
        """
        ).strip()
        expected_language2 = None
        expected_code2 = 'print("No language specified.")'

        language2, code2 = extract_codeblock(text2)
        self.assertEqual(language2, expected_language2)
        self.assertEqual(code2, expected_code2)

        # Test case 3: No code block present
        text3 = "This text has no code block."
        expected_code3 = ""

        language3, code3 = extract_codeblock(text3)
        self.assertIsNone(language3)
        self.assertEqual(code3, expected_code3)

    def test_media_type_of(self):
        # Test known file types
        self.assertEqual(media_type_of("example.txt"), ("text", "plain"))
        self.assertEqual(media_type_of("example.html"), ("text", "html"))
        self.assertEqual(media_type_of("image.png"), ("image", "png"))

        # Test unknown file type
        self.assertIsNone(media_type_of("file.unknownextension"))

        # Test no extension
        self.assertIsNone(media_type_of("file"))

        # Test with full path
        self.assertEqual(media_type_of("/path/to/example.css"), ("text", "css"))

        # Test uppercase extension
        self.assertEqual(media_type_of("IMAGE.JPG"), ("image", "jpeg"))

        # Test filename with multiple dots
        self.assertEqual(media_type_of("archive.tar.gz"), ("application", "x-tar"))

    def test_extract_path(self):
        test_cases = [
            ("ls -l /usr/bin", "/usr/bin"),
            ("cat /etc/passwd", "/etc"),
            ("ls -l /nonexistent/path", None),
            ("grep 'pattern' /var/log/syslog", "/var/log"),
            ("cp /etc/hosts /tmp", "/etc"),
            ("echo 'Hello World' > /tmp/hello.txt", "/tmp"),
            ("cat /etc/passwd | grep root", "/etc"),
            ("ls /tmp/newdir/with\\ spaces", "/tmp/newdir/with spaces"),
            ("ls '/tmp/newdir/with spaces'", "/tmp/newdir/with spaces"),
            ("ls $HOME", str(Path.home())),
            ("ls ~/Documents", None),
            ("find /usr -name 'python*'", "/usr"),
            ("grep 'error' /var/log/syslog > /tmp/errors.txt", "/var/log"),
            ("cd /tmp; ls", "/tmp"),
            ("echo $(pwd)", None),
            ("sudo cat /etc/ssh", "/etc/ssh"),
            ("ls ../", "../"),
            ("mkdir /tmp/newdir && cd /tmp/newdir", "/tmp/newdir"),
            ("ls", None),
            ("ls -la", None),
        ]

        for command_line, expected in test_cases:
            with self.subTest(command_line=command_line):
                result = extract_path(command_line)
                self.assertEqual(result, expected)

    def test_encode_image(self):
        test_image_content = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR"  # Sample PNG header bytes
        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            tmp_file.write(test_image_content)
            tmp_file_name = tmp_file.name
        try:
            expected_base64 = base64.b64encode(test_image_content).decode("utf-8")
            actual_base64 = encode_image(tmp_file_name)
            self.assertEqual(actual_base64, expected_base64)
        finally:
            os.unlink(tmp_file_name)


# Program entry point.
if __name__ == "__main__":
    suite = unittest.TestLoader().loadTestsFromTestCase(TestClass)
    unittest.TextTestRunner(verbosity=2, failfast=True, stream=sys.stdout).run(suite)
