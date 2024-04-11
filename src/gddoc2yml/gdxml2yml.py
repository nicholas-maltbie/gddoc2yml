#!/usr/bin/env python3
#
# Copyright (C) 2024 Nicholas Maltbie
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and
# associated documentation files (the "Software"), to deal in the Software without restriction,
# including without limitation the rights to use, copy, modify, merge, publish, distribute,
# sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all copies or
# substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING
# BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
# CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
# ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import argparse
import os
import pathvalidate
import re
import xml.etree.ElementTree as ET
import yaml

from .make_rst import State, ClassDef, print_error
from typing import Dict, List, Tuple


yml_mime_managed_reference_prefix = "### YamlMime:ManagedReference"
yml_mime_toc_prefix = "### YamlMime:TableOfContent"


def dir_path(string):
    if os.path.isdir(string):
        return string
    else:
        raise NotADirectoryError(string)


def make_yml_toc(classes: Dict[str, str], output: str) -> None:
    with open(
        os.path.join(output, "toc.yml"),
        "w",
        encoding="utf-8",
        newline="\n"
    ) as file:
        file.write(yml_mime_toc_prefix)
        file.write("\n")
        file.write(yaml.dump(
            [
                {
                    'uid': class_name,
                    'name': class_name
                }
                for class_name in classes
            ],
            default_flow_style=False,
            sort_keys=True))


def make_yml_class(class_def: ClassDef, state: State, output: str) -> str:
    class_name = class_def.name
    output_file = class_name.lower().replace("/", "--")
    with open(
        pathvalidate.sanitize_filepath(os.path.join(output, f"class_{output_file}.yml")),
        "w",
        encoding="utf-8",
        newline="\n"
    ) as file:
        file.write(yml_mime_managed_reference_prefix)
        file.write("\n")
        file.write(_get_class_yml(class_name, class_def, state))

    return output_file


def _get_class_yml(class_name: str, class_def: ClassDef, state: State) -> str:
    class_yml = {
        "uid": class_name,
        "commentId": "T:" + class_name,
        "id": class_name,
        "langs": ["gdscript"],
        "name": class_name,
        "nameWithType": class_name,
        "type": "Class",
    }

    if class_def.inherits:
        inherits = class_def.inherits.strip()
        all_inherits = [inherits]
        while inherits in state.classes:
            inode = state.classes[inherits].inherits
            if inode:
                inherits = inode.strip()
                all_inherits.append(inode)
            else:
                break
        class_yml["inheritance"] = all_inherits

    items = [class_yml]
    return yaml.dump({"items": items}, default_flow_style=False, sort_keys=False)


def _get_file_list(paths: List[str]) -> List[str]:
    file_list: List[str] = []

    for path in paths:
        if os.path.isdir(path):
            for root, subdirs, files in os.walk(path):
                file_list += (os.path.join(root, filename) for filename in files if filename.endswith(".xml"))
        elif os.path.isfile(path):
            if not path.endswith(".xml"):
                print(f'Got non-.xml file "{path}" in input, skipping.')
                continue
            file_list.append(path)

    return file_list


def _read_xml_data(files: List[str]) -> Dict[str, Tuple[ET.Element, str]]:
    classes: Dict[str, Tuple[ET.Element, str]] = {}
    for cur_file in _get_file_list(files):
        tree = ET.parse(cur_file)
        doc = tree.getroot()
        name = doc.attrib["name"]
        classes[name] = (doc, cur_file)

    return classes


def _get_class_state_from_docs(paths: List[str]) -> State:
    files: List[str] = _get_file_list(paths)
    classes: Dict[str, Tuple[ET.Element, str]] = _read_xml_data(files)
    state = State()
    for name, data in classes.items():
        try:
            state.parse_class(data[0], data[1])
        except Exception as e:
            print_error(f"{name}.xml: Exception while parsing class: {e}", state)
    return state


def _get_parser():
    parser = argparse.ArgumentParser(description='Convert godot documentation xml file to yml for docfx.')
    parser.add_argument("path", nargs="+", help="A path to an XML file or a directory containing XML files to parse.")
    parser.add_argument("--filter", default="", help="The filepath pattern for XML files to filter.")
    parser.add_argument('output', help='output folder to store all generated yml files.')
    return parser


def main() -> None:
    args = _get_parser().parse_args()

    state: State = _get_class_state_from_docs(args.path)

    # Create the output folder recursively if it doesn't already exist.
    os.makedirs(args.output, exist_ok=True)
    pattern = re.compile(args.filter)

    class_files: Dict[str, str] = {}
    state.sort_classes()
    for class_name, class_def in state.classes.items():
        if args.filter and not pattern.search(class_def.filepath):
            continue

        state.current_class = class_name
        class_def.update_class_group(state)
        class_files[class_name] = make_yml_class(class_def, state, args.output)

    make_yml_toc(class_files, args.output)


if __name__ == "__main__":
    main()
