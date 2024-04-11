import os
import unittest
import xml.etree.ElementTree as ET

from src.gddoc2yml import gdxml2yml
from src.gddoc2yml.make_rst import State

class MyTestCase1(unittest.TestCase):
    def test_class_yml_from_state(self):
        test_classes_dir = "tests/classes"
        state:State = gdxml2yml._get_class_state_from_docs([test_classes_dir])
        files = os.listdir(test_classes_dir)

        assert len(files) > 0
        assert len(state.classes) == len(files)

if __name__ == '__main__':
    unittest.main()