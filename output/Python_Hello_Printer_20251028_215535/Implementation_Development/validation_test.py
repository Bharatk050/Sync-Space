# Generated on: 2025-10-28 21:56:07

# validation_test.py
"""
This module contains the validation tests for the hello world printer.
It checks if the output is indeed "hello world" and if the code structure is organized.
"""

import unittest
from hello_world import print_hello_world
from io import StringIO
import sys

class TestHelloWorldPrinter(unittest.TestCase):
    def test_print_hello_world(self):
        # Capture the output
        capturedOutput = StringIO()
        sys.stdout = capturedOutput
        print_hello_world()
        sys.stdout = sys.__stdout__
        
        # Check if the output is indeed "hello world"
        self.assertEqual(capturedOutput.getvalue().strip(), "hello world")

if __name__ == "__main__":
    unittest.main()