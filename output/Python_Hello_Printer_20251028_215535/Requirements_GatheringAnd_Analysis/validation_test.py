# Generated on: 2025-10-28 21:55:46

# validation_test.py
import unittest

class TestHelloWorldProgram(unittest.TestCase):
    def test_print_hello_world(self):
        # Arrange
        import io
        import sys
        captured_output = io.StringIO()
        sys.stdout = captured_output

        # Act
        print_hello_world()

        # Assert
        sys.stdout = sys.__stdout__
        self.assertEqual(captured_output.getvalue().strip(), "hello world")

if __name__ == "__main__":
    unittest.main()