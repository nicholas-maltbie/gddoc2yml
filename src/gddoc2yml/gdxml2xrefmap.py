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
import re
import yaml
from pathlib import Path

from .make_rst import State
from .gdxml_helpers import *
from typing import Dict


def _get_parser():
    parser = argparse.ArgumentParser(description='Convert godot documentation xml files into a xrefmap compatibile with DoxFx.')
    parser.add_argument("path", nargs="+", help="A path to an XML file or a directory containing XML files to parse.")
    parser.add_argument("--filter", default="", help="The filepath pattern for XML files to filter.")
    parser.add_argument('output', help='output path to store xrefmap.')
    return parser


def main() -> None:
    args = _get_parser().parse_args()

    state: State = get_class_state_from_docs(args.path)

    # Create the output folder recursively if it doesn't already exist.
    os.makedirs(Path(args.output).parent, exist_ok=True)
    pattern = re.compile(args.filter)

    base_url = "https://docs.godotengine.org/en/stable"
    references = []
    state.sort_classes()
    for class_name, class_def in state.classes.items():
        if args.filter and not pattern.search(class_def.filepath):
            continue

        state.current_class = class_name
        class_def.update_class_group(state)
        references.append(get_class_reference(class_def))

        for signal_def in class_def.signals.values():
            references.append(get_signal_reference(signal_def, class_def, state))
        for constant_def in class_def.constants.values():
            references.append(get_constant_reference(constant_def, class_def, state))
        for property_def in class_def.properties.values():
            references.append(get_property_reference(property_def, class_def, state))
        for method_list in class_def.annotations.values():
            for _, annotation_def in enumerate(method_list):
                references.append(get_method_reference(annotation_def, class_def, state))
        for method_list in class_def.constructors.values():
            for _, constructor_def in enumerate(method_list):
                references.append(get_method_reference(constructor_def, class_def, state))
        for method_list in class_def.operators.values():
            for _, operator_def in enumerate(method_list):
                references.append(get_method_reference(operator_def, class_def, state, True))
        for method_list in class_def.methods.values():
            for _, method_def in enumerate(method_list):
                references.append(get_method_reference(method_def, class_def, state))
        for theme_item_def in class_def.theme_items.values():
            references.append(get_theme_item_reference(theme_item_def, class_def, state))

        for enum_name, enum_def in class_def.enums.items():
            pass
        

    xrefmap_yml = {
        "baseUrl": base_url,
        "references": references
    }

    with open(args.output, "w", encoding="utf-8", newline="\n") as file:\
        file.write("### YamlMime:XRefMap")
        file.write("\n")
        file.write(yaml.dump(xrefmap_yml, default_flow_style=False, sort_keys=True))


def get_class_reference(class_def: ClassDef) -> Dict:
    class_name = class_def.name
    class_uid = get_class_uid(class_def)
    return {
        "uid": class_uid,
        "name": class_def.name,
        "href": f"classes/class_{class_name}.html#{class_name}",
        "commentId": f"T:{class_uid}",
        "nameWithType": class_uid,
    }


def get_signal_reference(signal_def: SignalDef, class_def: ClassDef, state: State) -> Dict:
    class_name = class_def.name
    signal_uid = get_signal_uid(signal_def, class_def, state)
    signal_name = make_method_signature(signal_def, True, False, False, state, False)
    signal_href = clean_href(signal_def.name)
    return {
        "uid": signal_uid,
        "name": signal_name,
        "href": f"classes/class_{class_name.lower()}.html#class-{class_name.lower()}-signal-{signal_href}",
        "commentId": f"E:{signal_uid}",
        "nameWithType": f"{class_name}.{signal_name}",
    }


def get_constant_reference(constant_def: ConstantDef, class_def: ClassDef, state: State) -> Dict:
    class_name = class_def.name
    constant_uid = get_constant_uid(constant_def, class_def)
    constant_href_id = clean_href(f"class-{class_name.lower()}-constant-{constant_def.name}")
    return {
        "uid": constant_uid,
        "name": constant_def.name,
        "href": f"classes/class_{class_name.lower()}.html#{constant_href_id}",
        "commentId": f"E:{constant_uid}",
        "nameWithType": f"{class_name}.{constant_def.name}",
    }


def get_method_reference(method_def: AnnotationDef, class_def: ClassDef, state: State, include_params: bool = False) -> Dict:
    class_name = class_def.name
    method_uid = get_method_uid(method_def, class_def, state)
    method_name = make_method_signature(method_def, True, False, False, state, False)
    method_href_id = clean_href(f"class-{class_name.lower()}-{method_def.definition_name}-{make_method_href(method_def, state, include_params)}")
    return {
        "uid": method_uid,
        "name": method_name,
        "href": f"classes/class_{class_name.lower()}.html#{method_href_id}",
        "commentId": f"M:{method_uid}",
        "nameWithType": f"{class_name}.{method_def.name}",
    }


def get_property_reference(property_def: PropertyDef, class_def: ClassDef, state: State) -> Dict:
    class_name = class_def.name
    property_uid = f"{class_name}.{property_def.name}"
    property_href_id = clean_href(f"class-{class_name.lower()}-property-{property_def.name}")
    return {
        "uid": property_uid,
        "name": property_def.name,
        "href": f"classes/class_{class_name.lower()}.html#{property_href_id}",
        "commentId": f"P:{property_uid}",
        "nameWithType": f"{class_name}.{property_def.name}",
    }


def make_method_href(definition: Union[AnnotationDef, MethodDef, SignalDef], state: State, include_params: bool = False) -> str:
    qualifiers = None
    if isinstance(definition, (MethodDef, AnnotationDef)):
        qualifiers = definition.qualifiers

    varargs = qualifiers is not None and "vararg" in qualifiers
    params = []
    for parameter in definition.parameters:
        params.append(parameter.type_name.type_name)

    out = definition.name.replace("operator ", "")
    if definition.name.startswith("operator "):
        out = sanitize_operator_name(definition.name, state)

    if varargs:
        params += ["..."]

    if len(params) and include_params:
        out += f"-{"-".join(params)}"

    return out


def get_theme_item_reference(theme_item_def: ThemeItemDef, class_def: ClassDef, state: State) -> Dict:
    class_name = class_def.name
    theme_item_id = get_theme_uid(theme_item_def, class_def)
    theme_item_href_id = clean_href(f"class-{class_name.lower()}-theme-{theme_item_def.data_name}-{theme_item_def.name}")
    return {
        "uid": theme_item_id,
        "name": theme_item_def.name,
        "href": f"classes/class_{class_name.lower()}.html#{theme_item_href_id}",
        "commentId": f"M:{theme_item_id}",
        "nameWithType": f"{class_name}.{theme_item_def.name}",
    }


def clean_href(name: str) -> str:
    return re.sub(r'[^a-zA-Z\d\s:]', '-', name.replace("@", "")).lower()

if __name__ == "__main__":
    main()
