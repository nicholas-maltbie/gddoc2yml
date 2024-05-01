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

from .make_rst import AnnotationDef, MethodDef, SignalDef, State, ClassDef, EnumDef, TypeName, print_error
from .gdxml_helpers import format_text_block, make_link, make_method_signature, \
    full_type_name, make_setter_signature, make_getter_signature, get_method_qualifiers, get_method_return_type
from typing import Dict, List, Tuple, Union


yml_mime_managed_reference_prefix = "### YamlMime:ManagedReference"
yml_mime_toc_prefix = "### YamlMime:TableOfContent"


def dir_path(string):
    if os.path.isdir(string):
        return string
    else:
        raise NotADirectoryError(string)


def make_yml_toc(classes: List[Dict], output: str) -> None:
    with open(
        os.path.join(output, "toc.yml"),
        "w",
        encoding="utf-8",
        newline="\n"
    ) as file:
        file.write(yml_mime_toc_prefix)
        file.write("\n")
        file.write(yaml.dump(
            classes,
            default_flow_style=False,
            sort_keys=True))


def make_yml_enum(class_name: str, enum_def: EnumDef, state: State, output: str) -> str:
    enum_name = enum_def.name
    output_file = enum_name.lower().replace("/", "--")
    with open(
        pathvalidate.sanitize_filepath(os.path.join(output, f"enum_{class_name}_{output_file}.yml")),
        "w",
        encoding="utf-8",
        newline="\n"
    ) as file:
        file.write(yml_mime_managed_reference_prefix)
        file.write("\n")
        file.write(_get_enum_yml(class_name, enum_name, enum_def, state))

    return output_file


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


def _get_class_descendants(class_name: str, state: State) -> List[str]:
    """Gets the list of all classes that inherit a given class from a state."""
    inherited: List[str] = []
    for c in state.classes.values():
        if c.inherits and c.inherits.strip() == class_name:
            inherited.append(c.name)

    return inherited


def _get_class_inheritance(class_def: ClassDef, state: State) -> List[str]:
    """Get the class inheritance in order for a given class and state."""
    inherits = class_def.inherits.strip()
    all_inherits = [inherits]
    while inherits in state.classes:
        inode = state.classes[inherits].inherits
        if inode:
            inherits = inode.strip()
            all_inherits.append(inode)
        else:
            break
    return all_inherits


def _get_seealso_list(class_def: ClassDef) -> List[Dict]:
    seealso: List[Dict] = []
    for url, title in class_def.tutorials:
        # see LinkInfo definition
        # https://github.com/dotnet/docfx/blob/main/src/Docfx.DataContracts.UniversalReference/LinkInfo.cs
        seealso.append(
            {
                "linkType": "HRef",
                "linkId": make_link(url, ""),
                "commentId": title,
                "altText": title
            }
        )

    return seealso


def _get_enum_yml(class_name: str, enum_name: str, enum_def: EnumDef, state: State) -> str:
    enum_id = f"{class_name}.{enum_name}"
    enum_yml = {
        "uid": enum_id,
        "commentId": "T:" + enum_id,
        "id": enum_name,
        "langs": ["gdscript", "csharp"],
        "name": enum_name,
        "nameWithType": enum_id,
        "type": "Enum",
    }

    children = []
    for value_name, value_def in enum_def.values.items():
        value_id = f"{enum_id}.{value_name}"
        value_yml = {
            "uid": value_id,
            "commentId": f"F:{value_id}",
            "id": value_name,
            "langs": ["gdscript", "csharp"],
            "name": value_name,
            "nameWithType": value_id,
            "type": "Field",
            "summary": format_text_block(value_def.text, enum_def, state),
            "syntax":
            {
                "content": f"{value_name} = {value_def.value}",
                "return": {"type": full_type_name(value_id, state)}
            }
        }
        children.append(value_yml)

    enum_yml["children"] = [value["uid"] for value in children]
    items = [enum_yml] + children
    return yaml.dump({"items": items}, default_flow_style=False, sort_keys=False)


def _make_reference_yml(type_def: TypeName, state: State):
    full_name = full_type_name(type_def.type_name, state)
    return {
        "uid": full_name,
        "name": full_name,
    }


def _get_method_yml(
        class_name: str,
        method_def: Union[AnnotationDef, MethodDef, SignalDef],
        state: State, method_type: str
    ) -> Tuple[Dict[str, Dict], Dict]:
    references = {}
    signature_short = make_method_signature(method_def, False, False, False, state, True)
    signature_spaces = make_method_signature(method_def, True, False, False, state, False)
    signature_spaces_named = make_method_signature(method_def, True, True, False, state, False)
    full_name = f"{class_name}.{signature_short}"

    summary = ""
    if method_def.qualifiers:
        summary += f"Qualifiers: {get_method_qualifiers(method_def)}\n\n"
    summary += format_text_block(method_def.description.strip(), method_def, state)

    syntax = f"{signature_spaces_named}"
    ret_type = get_method_return_type(method_def)
    if ret_type:
        syntax = ret_type + " " + syntax

    method_yml = {
        "uid": full_name,
        "commentId": f"M:{full_name}",
        "id": signature_short,
        "langs": ["gdscript", "csharp"],
        "name": signature_spaces,
        "nameWithType": f"{class_name}.{signature_spaces}",
        "type": method_type,
        "syntax": {
            "content": syntax,
            "parameters": [
                {
                    "id": parameter.name,
                    "type": parameter.type_name.type_name,
                }
                for parameter in method_def.parameters
            ],
        },
        "summary": summary,
        "parent": class_name,
    }

    # add all types of parameter as references
    for parameter in method_def.parameters:
        references[parameter.type_name.type_name] = _make_reference_yml(parameter.type_name, state)

    return references, method_yml


def _get_class_yml(class_name: str, class_def: ClassDef, state: State) -> str:
    class_yml = {
        "uid": class_name,
        "commentId": "T:" + class_name,
        "id": class_name,
        "langs": ["gdscript", "csharp"],
        "name": class_name,
        "nameWithType": class_name,
        "type": "Class",
    }

    # Referenced data types, see ReferenceViewModel
    # https://github.com/dotnet/docfx/blob/main/src/Docfx.DataContracts.Common/ReferenceViewModel.cs
    references = dict()

    # INHERITANCE TREE
    # Ascendants
    if class_def.inherits:
        class_yml["inheritance"] = _get_class_inheritance(class_def, state)

    # Descendants
    inherited: List[str] = _get_class_descendants(class_name, state)
    if len(inherited):
        class_yml["derivedClasses"] = inherited

    # INTRODUCTION
    # Brief description
    # See Summary tag definition -
    #  https://learn.microsoft.com/en-us/dotnet/csharp/language-reference/xmldoc/recommended-tags#summary
    if class_def.brief_description is not None and class_def.brief_description.strip() != "":
        class_yml["summary"] = format_text_block(
            class_def.brief_description.strip(),
            class_def,
            state)

    # Class description
    # See Remarks tag definition -
    #  https://learn.microsoft.com/en-us/dotnet/csharp/language-reference/xmldoc/recommended-tags#remarks
    if class_def.description is not None and class_def.description.strip() != "":
        class_yml["remarks"] = format_text_block(
            class_def.description.strip(),
            class_def,
            state)

    # Online tutorials (implemented via seealso)
    #  https://learn.microsoft.com/en-us/dotnet/csharp/language-reference/xmldoc/recommended-tags#seealso
    if len(class_def.tutorials) > 0:
        class_yml["seealso"] = _get_seealso_list(class_def)

    # Signal descriptions
    signals = []
    for signal in class_def.signals.values():
        signature_short = make_method_signature(signal, False, False, False, state, False)
        signature_spaces = make_method_signature(signal, True, False, False, state, False)
        signature_spaces_named = make_method_signature(signal, True, True, False, state, False)
        full_name = f"{class_name}.{signature_short}"
        signal_yml = {
            "uid": full_name,
            "commentId": f"E:{full_name}",
            "id": signature_short,
            "langs": ["gdscript", "csharp"],
            "name": signature_spaces,
            "nameWithType": f"{class_name}.{signature_spaces}",
            "type": "Event",
            "syntax": {
                "content": f"signal {signature_spaces_named}",
                "parameters": [
                    {
                        "id": parameter.name,
                        "type": parameter.type_name.type_name,
                    }
                    for parameter in signal.parameters
                ],
            },
            "summary": format_text_block(signal.description.strip(), signal, state),
            "parent": class_name,
        }

        # add all types of parameter as references
        for parameter in signal.parameters:
            references[parameter.type_name.type_name] = _make_reference_yml(parameter.type_name, state)

        signals.append(signal_yml)

    # Constant descriptions
    constants = []
    for constant in class_def.constants.values():
        constant_id = f"{class_name}.{constant.name}"
        constant_yml = {
            "uid": constant_id,
            "commentId": f"F:{constant_id}",
            "id": constant.name,
            "langs": ["gdscript", "csharp"],
            "name": constant.name,
            "nameWithType": constant_id,
            "type": "Field",
            "summary": format_text_block(constant.text, class_def, state),
            "syntax":
            {
                "content": f"const {constant.name} = {constant.value}",
            },
            "parent": class_name,
        }
        constants.append(constant_yml)

    # Annotation descriptions
    annotations = []
    for method_list in class_def.annotations.values():
        for _, m in enumerate(method_list):
            signature_spaces_named = make_method_signature(m, True, True, False, state, False)
            annotation_ref, annotation_yml = _get_method_yml(class_name, m, state, "Property")
            annotation_yml["summary"] = "**Annotation**\n\n" + annotation_yml["summary"]
            references.update(annotation_ref)
            annotations.append(annotation_yml)


    # Property descriptions
    properties = []
    if any(not p.overrides for p in class_def.properties.values()) > 0:
        for property_def in class_def.properties.values():
            if property_def.overrides:
                continue

            property_id = f"{class_name}.{property_def.name}"
            syntax = f"var {property_def.name}"
            if len(property_def.type_name.type_name):
                syntax += f" : {property_def.type_name.type_name}"
            if property_def.default_value:
                syntax += f" = {property_def.default_value.replace("`", "")}"

            property_yml = {
                "uid": property_id,
                "commentId": f"P:{property_id}",
                "id": property_def.name,
                "langs": ["gdscript", "csharp"],
                "name": property_def.name,
                "nameWithType": property_id,
                "type": "Property",
                "summary": format_text_block(property_def.text.strip(), property_def, state),
                "syntax":
                {
                    "content": syntax,
                    "return": {"type": full_type_name(property_def.type_name.type_name, state)}
                },
                "parent": class_name,
            }

            # Create property setter and getter records.
            property_setget = ""

            if property_def.setter is not None and not property_def.setter.startswith("_"):
                property_setter = make_setter_signature(class_def, property_def, state)
                property_setget += f"- {property_setter}\n"

            if property_def.getter is not None and not property_def.getter.startswith("_"):
                property_getter = make_getter_signature(class_def, property_def, state)
                property_setget += f"- {property_getter}\n"

            if property_setget != "":
                property_yml["remarks"] = property_setget

            properties.append(property_yml)
            references[property_def.type_name.type_name] = _make_reference_yml(property_def.type_name, state)

    # Constructor, Method, Operator descriptions
    constructors = []
    for method_list in class_def.constructors.values():
        for _, m in enumerate(method_list):
            constructor_ref, constructor_yml = _get_method_yml(class_name, m, state, "Constructor")
            references.update(constructor_ref)
            constructors.append(constructor_yml)

    methods = []
    for method_list in class_def.methods.values():
        for _, m in enumerate(method_list):
            method_ref, method_yml = _get_method_yml(class_name, m, state, "Method")
            references.update(method_ref)
            constructors.append(method_yml)

    operators = []
    for method_list in class_def.operators.values():
        for _, m in enumerate(method_list):
            operator_ref, operator_yml = _get_method_yml(class_name, m, state, "Operator")
            references.update(operator_ref)
            operators.append(operator_yml)

    # Theme property descriptions
    theme_properties = []
    for theme_item_def in class_def.theme_items.values():
        theme_item_id = f"{class_name}.{theme_item_def.name}"
        syntax = f"{theme_item_def.type_name.type_name} {theme_item_def.name}"
        if theme_item_def.default_value is not None:
            syntax = f" = {theme_item_def.default_value}"
        theme_yml = {
            "uid": theme_item_id,
            "commentId": f"P:{theme_item_id}",
            "id": theme_item_def.name,
            "langs": ["gdscript", "csharp"],
            "name": theme_item_def.name,
            "nameWithType": theme_item_id,
            "type": "Property",
            "summary": "**Theme Property**\n\n" + format_text_block(theme_item_def.text.strip(), theme_item_def, state),
            "syntax":
            {
                "content": syntax,
                "return": {"type": full_type_name(theme_item_def.type_name.type_name, state)}
            },
            "parent": class_name,
        }

        references[theme_item_def.type_name.type_name] = _make_reference_yml(theme_item_def.type_name, state)
        theme_properties.append(theme_yml)

    children = signals + constants + annotations + properties + constructors + methods + operators + theme_properties
    if len(children):
        class_yml["children"] = [child["uid"] for child in children]

    items = [class_yml] + children
    return yaml.dump(
        {
            "items": items,
            "references": list(references.values())
        }, default_flow_style=False, sort_keys=False)


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

    class_files = []
    state.sort_classes()
    for class_name, class_def in state.classes.items():
        if args.filter and not pattern.search(class_def.filepath):
            continue

        state.current_class = class_name
        class_def.update_class_group(state)
        class_file_path = make_yml_class(class_def, state, args.output)
        toc_yml = {
            "uid": class_name,
            "name": class_file_path,
        }

        enum_toc_yml = []
        for enum_name, enum_def in class_def.enums.items():
            make_yml_enum(class_name, enum_def, state, args.output)
            ref_yml = {"uid": f"{class_name}.{enum_name}", "name": enum_name}
            enum_toc_yml.append(ref_yml)

        if len(enum_toc_yml):
            toc_yml["items"] = enum_toc_yml

        class_files.append(toc_yml)

    make_yml_toc(class_files, args.output)


if __name__ == "__main__":
    main()
