import os
import tempfile
import shutil
import unittest

from importlib.resources import files
from src.gddoc2yml import gdxml_helpers
from src.gddoc2yml.make_rst import State


class MyTestCase1(unittest.TestCase):
    def test_class_yml_from_state(self):
        # Program expects files to be read from path location, not package
        # Setup temporary directory with xml docs
        xml_docs = [f for f in files("tests").joinpath("classes").iterdir() if f.is_file() and f.name.endswith(".xml")]
        with tempfile.TemporaryDirectory() as tmpdirname:
            for xml_doc in xml_docs:
                shutil.copyfile(xml_doc, os.path.join(tmpdirname, xml_doc.name))

            state: State = gdxml_helpers.get_class_state_from_docs([tmpdirname])
            xml_files = [f for f in os.listdir(tmpdirname) if f.endswith(".xml")]

            assert len(xml_files) > 0
            assert len(state.classes) == len(xml_files)


if __name__ == '__main__':
    unittest.main()
