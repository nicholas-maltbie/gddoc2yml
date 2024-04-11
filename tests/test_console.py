import unittest
import argparse
import tempfile

from unittest import TestCase, mock
from src.gddoc2yml.gdxml2yml import main

class TestConsole(TestCase):
    def test_empty(self):
        with tempfile.TemporaryDirectory() as input_dirname, \
            tempfile.TemporaryDirectory() as output_dirname, \
            mock.patch('argparse.ArgumentParser.parse_args',
                        return_value=argparse.Namespace(path = [input_dirname], filter="", output = output_dirname)):
            main()

if __name__ == '__main__':
    unittest.main()
