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

from .make_rst import State, DefinitionBase, TagState, MethodDef, \
    SignalDef, AnnotationDef, ParameterDef, ClassDef, PropertyDef, TypeName, \
    RESERVED_CODEBLOCK_TAGS, RESERVED_CROSSLINK_TAGS, GODOT_DOCS_PATTERN, \
    MARKUP_ALLOWED_PRECEDENT, MARKUP_ALLOWED_SUBSEQUENT
from typing import List, Dict, TextIO, Tuple, Optional, Union

GODOT_DOC_URL = "https://docs.godotengine.org/en/stable/"

STYLES: Dict[str, str] = {}
STYLES["red"] = "\x1b[91m"
STYLES["green"] = "\x1b[92m"
STYLES["yellow"] = "\x1b[93m"
STYLES["bold"] = "\x1b[1m"
STYLES["regular"] = "\x1b[22m"
STYLES["reset"] = "\x1b[0m"

operator_lookup = {
    "!=": "neq",
    "==": "eq",
    "<": "lt",
    "<=": "lte",
    ">": "gt",
    ">=": "gte",
    "+": "sum",
    "-": "dif",
    "*": "mul",
    "/": "div",
    "%": "mod",
    "**": "pow",
    "unary+": "unplus",
    "unary-": "unminus",
    "<<": "bwsl",
    ">>": "bwsr",
    "&": "bwand",
    "|": "bwor",
    "^": "bwxor",
    "~": "bwnot",
    "[]": "idx",
}


def print_error(error: str, state: State) -> None:
    print(f'{STYLES["red"]}{STYLES["bold"]}ERROR:{STYLES["regular"]} {error}{STYLES["reset"]}')
    state.num_errors += 1


def print_warning(warning: str, state: State) -> None:
    print(f'{STYLES["yellow"]}{STYLES["bold"]}WARNING:{STYLES["regular"]} {warning}{STYLES["reset"]}')
    state.num_warnings += 1


def make_link(url: str, title: str) -> str:
    match = GODOT_DOCS_PATTERN.search(url)
    if match:
        groups = match.groups()
        if match.lastindex == 2:
            # Doc reference with fragment identifier: emit direct link to section with reference to page, for example:
            # `#calling-javascript-from-script in Exporting For Web`
            # Or use the title if provided.
            if title != "":
                return f"[{title}]({GODOT_DOC_URL}/{groups[0]}.html{groups[1]})"
            return f"{GODOT_DOC_URL}/{groups[0]}.html{groups[1]}"
        elif match.lastindex == 1:
            # Doc reference, for example:
            # `Math`
            if title != "":
                return f"[{title}]({GODOT_DOC_URL}/{groups[0]}.html)"
            return f"{GODOT_DOC_URL}/{groups[0]}.html{groups[1]}"

    # External link, for example:
    # `http://enet.bespin.org/usergroup0.html`
    if title != "":
        return f"[{title}]({url})"
    return f"{url}"


def make_enum(t: str, is_bitfield: bool, state: State) -> str:
    p = t.find(".")
    if p >= 0:
        c = t[0:p]
        e = t[p + 1:]
        # Variant enums live in GlobalScope but still use periods.
        if c == "Variant":
            c = "@GlobalScope"
            e = "Variant." + e
    else:
        c = state.current_class
        e = t
        if c in state.classes and e not in state.classes[c].enums:
            c = "@GlobalScope"

    if c in state.classes and e in state.classes[c].enums:
        if is_bitfield:
            if not state.classes[c].enums[e].is_bitfield:
                print_error(f'{state.current_class}.xml: Enum "{t}" is not bitfield.', state)
            return f"<xref href=\"{c}.{e}\"></xref>"
        else:
            return f"<xref href=\"{e}\"></xref>"

    # Don't fail for `Vector3.Axis`, as this enum is a special case which is expected not to be resolved.
    if f"{c}.{e}" != "Vector3.Axis":
        print_error(f'{state.current_class}.xml: Unresolved enum "{t}".', state)

    return t


def make_type(klass: str, state: State) -> str:
    if klass.find("*") != -1:  # Pointer, ignore
        return f"``{klass}``"

    link_type = klass
    is_array = False
    if link_type.endswith("[]"):  # Typed array, strip [] to link to contained type.
        link_type = link_type[:-2]
        is_array = True

    if link_type in state.classes:
        if is_array:
            return f"<xref href=\"{link_type}\" data-throw-if-not-resolved=\"false\">{link_type}[]</xref>"
        return f"<xref href=\"{link_type}\" data-throw-if-not-resolved=\"false\"></xref>"

    if klass == "void":
        return "void"

    print_error(f'{state.current_class}.xml: Unresolved type "{link_type}".', state)
    if is_array:
        return f"``{link_type}[]``"
    return f"``{link_type}``"


def full_type_name(type_name: str, state: State) -> str:
    if type_name in state.classes:
        return type_name

    for enum_name, _ in state.classes[state.current_class].enums.items():
        if enum_name == type_name:
            return f"{state.current_class}.{enum_name}"

    for class_name, class_def in state.classes.items():
        for enum_name, _ in class_def.enums.items():
            if enum_name == type_name:
                return f"{class_name}.{enum_name}"

    return type_name


def is_in_tagset(tag_text: str, tagset: List[str]) -> bool:
    for tag in tagset:
        # Complete match.
        if tag_text == tag:
            return True
        # Tag with arguments.
        if tag_text.startswith(tag + " "):
            return True
        # Tag with arguments, special case for [url], [color], and [font].
        if tag_text.startswith(tag + "="):
            return True

    return False


def get_tag_and_args(tag_text: str) -> TagState:
    tag_name = tag_text
    arguments: str = ""

    delim_pos = -1

    space_pos = tag_text.find(" ")
    if space_pos >= 0:
        delim_pos = space_pos

    # Special case for [url], [color], and [font].
    assign_pos = tag_text.find("=")
    if assign_pos >= 0 and (delim_pos < 0 or assign_pos < delim_pos):
        delim_pos = assign_pos

    if delim_pos >= 0:
        tag_name = tag_text[:delim_pos]
        arguments = tag_text[delim_pos + 1:].strip()

    closing = False
    if tag_name.startswith("/"):
        tag_name = tag_name[1:]
        closing = True

    return TagState(tag_text, tag_name, arguments, closing)


def parse_link_target(link_target: str, state: State, context_name: str) -> List[str]:
    if link_target.find(".") != -1:
        return link_target.split(".")
    else:
        return [state.current_class, link_target]


def format_context_name(context: Union[DefinitionBase, None]) -> str:
    context_name: str = "unknown context"
    if context is not None:
        context_name = f'{context.definition_name} "{context.name}" description'

    return context_name


def escape_rst(text: str, until_pos: int = -1) -> str:
    # Escape \ character, otherwise it ends up as an escape character in rst
    pos = 0
    while True:
        pos = text.find("\\", pos, until_pos)
        if pos == -1:
            break
        text = f"{text[:pos]}\\\\{text[pos + 1:]}"
        pos += 2

    # Escape * character to avoid interpreting it as emphasis
    pos = 0
    while True:
        pos = text.find("*", pos, until_pos)
        if pos == -1:
            break
        text = f"{text[:pos]}\\*{text[pos + 1:]}"
        pos += 2

    # Escape _ character at the end of a word to avoid interpreting it as an inline hyperlink
    pos = 0
    while True:
        pos = text.find("_", pos, until_pos)
        if pos == -1:
            break
        if not text[pos + 1].isalnum():  # don't escape within a snake_case word
            text = f"{text[:pos]}\\_{text[pos + 1:]}"
            pos += 2
        else:
            pos += 1

    return text


def format_codeblock(
    tag_state: TagState, post_text: str, indent_level: int, state: State
) -> Union[Tuple[str, int], None]:
    end_pos = post_text.find("[/" + tag_state.name + "]")
    if end_pos == -1:
        print_error(
            f"{state.current_class}.xml: Tag depth mismatch for [{tag_state.name}]: no closing [/{tag_state.name}].",
            state,
        )
        return None

    opening_formatted = tag_state.name
    if len(tag_state.arguments) > 0:
        opening_formatted += " " + tag_state.arguments

    code_text = post_text[len(f"[{opening_formatted}]"):end_pos]
    post_text = post_text[end_pos:]

    # Remove extraneous tabs
    code_pos = 0
    while True:
        code_pos = code_text.find("\n", code_pos)
        if code_pos == -1:
            break

        to_skip = 0
        while code_pos + to_skip + 1 < len(code_text) and code_text[code_pos + to_skip + 1] == "\t":
            to_skip += 1

        if to_skip > indent_level:
            print_error(
                f"{state.current_class}.xml: Four spaces should be used for indentation within [{tag_state.name}].",
                state,
            )

        if len(code_text[code_pos + to_skip + 1:]) == 0:
            code_text = f"{code_text[:code_pos]}\n"
            code_pos += 1
        else:
            code_text = f"{code_text[:code_pos]}\n    {code_text[code_pos + to_skip + 1:]}"
            code_pos += 5 - to_skip

    # Remove extra indentation
    code_text = code_text.replace("\n    ", "\n")

    # Get language name for syntax highlighting
    lang_name = tag_state.name

    # Assume default language of gdscript unless otherwise specified
    if lang_name == "codeblock":
        lang_name = "gdscript"

    return (
        f"\n[{opening_formatted}]```{lang_name}{code_text}```{post_text}",
        len(f"\n[{opening_formatted}]{code_text}"))


def format_table(f: TextIO, data: List[Tuple[Optional[str], ...]], remove_empty_columns: bool = False) -> None:
    if len(data) == 0:
        return

    f.write(".. table::\n")
    f.write("   :widths: auto\n\n")

    # Calculate the width of each column first, we will use this information
    # to properly format RST-style tables.
    column_sizes = [0] * len(data[0])
    for row in data:
        for i, text in enumerate(row):
            text_length = len(text or "")
            if text_length > column_sizes[i]:
                column_sizes[i] = text_length

    # Each table row is wrapped in two separators, consecutive rows share the same separator.
    # All separators, or rather borders, have the same shape and content. We compose it once,
    # then reuse it.

    sep = ""
    for size in column_sizes:
        if size == 0 and remove_empty_columns:
            continue
        sep += "+" + "-" * (size + 2)  # Content of each cell is padded by 1 on each side.
    sep += "+\n"

    # Draw the first separator.
    f.write(f"   {sep}")

    # Draw each row and close it with a separator.
    for row in data:
        row_text = "|"
        for i, text in enumerate(row):
            if column_sizes[i] == 0 and remove_empty_columns:
                continue
            row_text += f' {(text or "").ljust(column_sizes[i])} |'
        row_text += "\n"

        f.write(f"   {row_text}")
        f.write(f"   {sep}")

    f.write("\n")


def sanitize_operator_name(dirty_name: str, state: State) -> str:
    clear_name = dirty_name.replace("operator ", "")
    if clear_name in operator_lookup:
        clear_name = operator_lookup[clear_name]
    else:
        clear_name = "xxx"
        print_error(f'Unsupported operator type "{dirty_name}", please add the missing rule.', state)

    return clear_name


def format_text_block(  # noqa: C901 # TODO: Unwrap and fix this function!
    text: str,
    context: DefinitionBase,
    state: State,
) -> str:
    # Linebreak + tabs in the XML should become two line breaks unless in a "codeblock"
    pos = 0
    while True:
        pos = text.find("\n", pos)
        if pos == -1:
            break

        pre_text = text[:pos]
        indent_level = 0
        while pos + 1 < len(text) and text[pos + 1] == "\t":
            pos += 1
            indent_level += 1
        post_text = text[pos + 1:]

        # Handle codeblocks
        if (
            post_text.startswith("[codeblock]")
            or post_text.startswith("[codeblock ")
            or post_text.startswith("[gdscript]")
            or post_text.startswith("[gdscript ")
            or post_text.startswith("[csharp]")
            or post_text.startswith("[csharp ")
        ):
            tag_text = post_text[1:].split("]", 1)[0]
            tag_state = get_tag_and_args(tag_text)
            result = format_codeblock(tag_state, post_text, indent_level, state)
            if result is None:
                return ""
            text = f"{pre_text}{result[0]}"
            pos += result[1] - indent_level

        # Handle normal text
        else:
            text = f"{pre_text}\n\n{post_text}"
            pos += 2 - indent_level

    next_brac_pos = text.find("[")
    text = escape_rst(text, next_brac_pos)

    context_name = format_context_name(context)

    # Handle [tags]
    inside_code = False
    inside_code_tag = ""
    inside_code_tabs = False
    ignore_code_warnings = False
    code_warning_if_intended_string = "If this is intended, use [code skip-lint]...[/code]."

    has_codeblocks_gdscript = False
    has_codeblocks_csharp = False

    pos = 0
    tag_depth = 0
    while True:
        pos = text.find("[", pos)
        if pos == -1:
            break

        endq_pos = text.find("]", pos + 1)
        if endq_pos == -1:
            break

        pre_text = text[:pos]
        post_text = text[endq_pos + 1:]
        tag_text = text[pos + 1:endq_pos]

        # Tag is a reference to a class.
        if tag_text in state.classes and not inside_code:
            if tag_text == state.current_class:
                # Don't create a link to the same class, format it as strong emphasis.
                tag_text = f"**{tag_text}**"
            else:
                tag_text = make_type(tag_text, state)

        # Tag is a cross-reference or a formatting directive.
        else:
            tag_state = get_tag_and_args(tag_text)

            # Anything identified as a tag inside of a code block is valid,
            # unless it's a matching closing tag.
            if inside_code:
                # Exiting codeblocks and inline code tags.

                if tag_state.closing and tag_state.name == inside_code_tag:
                    if is_in_tagset(tag_state.name, RESERVED_CODEBLOCK_TAGS):
                        tag_text = ""
                        tag_depth -= 1
                        inside_code = False
                        ignore_code_warnings = False
                        # Strip newline if the tag was alone on one
                        if pre_text[-1] == "\n":
                            pre_text = pre_text[:-1]

                    elif is_in_tagset(tag_state.name, ["code"]):
                        tag_text = "``"
                        tag_depth -= 1
                        inside_code = False
                        ignore_code_warnings = False

                else:
                    if not ignore_code_warnings and tag_state.closing:
                        print_warning(
                            f'{state.current_class}.xml: Found a code string ' +
                            f'that looks like a closing tag "[{tag_state.raw}]" ' +
                            f'in {context_name}. {code_warning_if_intended_string}',
                            state,
                        )

                    tag_text = f"[{tag_text}]"

            # Entering codeblocks and inline code tags.

            elif tag_state.name == "codeblocks":
                if tag_state.closing:
                    if not has_codeblocks_gdscript or not has_codeblocks_csharp:
                        state.script_language_parity_check.add_hit(
                            state.current_class,
                            context,
                            "Only one script language sample found in [codeblocks]",
                            state,
                        )

                    has_codeblocks_gdscript = False
                    has_codeblocks_csharp = False

                    tag_depth -= 1
                    tag_text = "---"
                    inside_code_tabs = False
                else:
                    tag_depth += 1
                    tag_text = ""
                    inside_code_tabs = True

            elif is_in_tagset(tag_state.name, RESERVED_CODEBLOCK_TAGS):
                tag_depth += 1

                if tag_state.name == "gdscript":
                    if not inside_code_tabs:
                        print_error(
                            f"{state.current_class}.xml: GDScript code block is " +
                            f"used outside of [codeblocks] in {context_name}.",
                            state,
                        )
                    else:
                        has_codeblocks_gdscript = True
                    tag_text = "\n# [gdscript](#tab/gdscript)\n"
                elif tag_state.name == "csharp":
                    if not inside_code_tabs:
                        print_error(
                            f"{state.current_class}.xml: C# code block is " +
                            f"used outside of [codeblocks] in {context_name}.",
                            state,
                        )
                    else:
                        has_codeblocks_csharp = True
                    tag_text = "\n# [C#](#tab/csharp)\n"
                else:
                    state.script_language_parity_check.add_hit(
                        state.current_class,
                        context,
                        "Code sample is formatted with [codeblock] where [codeblocks] should be used",
                        state,
                    )

                    if "lang=text" in tag_state.arguments.split(" "):
                        tag_text = "\n# [text](#tab/text)\n"
                    else:
                        tag_text = ""

                inside_code = True
                inside_code_tag = tag_state.name
                ignore_code_warnings = "skip-lint" in tag_state.arguments.split(" ")

            elif is_in_tagset(tag_state.name, ["code"]):
                tag_text = "``"
                tag_depth += 1

                inside_code = True
                inside_code_tag = "code"
                ignore_code_warnings = "skip-lint" in tag_state.arguments.split(" ")

                if not ignore_code_warnings:
                    endcode_pos = text.find("[/code]", endq_pos + 1)
                    if endcode_pos == -1:
                        print_error(
                            f"{state.current_class}.xml: Tag depth mismatch for " +
                            f"[code]: no closing [/code] in {context_name}.",
                            state,
                        )
                        break

                    inside_code_text = text[endq_pos + 1:endcode_pos]
                    if inside_code_text.endswith("()"):
                        # It's formatted like a call for some reason, may still be a mistake.
                        inside_code_text = inside_code_text[:-2]

                    if inside_code_text in state.classes:
                        print_warning(
                            f'{state.current_class}.xml: Found a code string ' +
                            f'"{inside_code_text}" that matches one of the known ' +
                            f'classes in {context_name}. {code_warning_if_intended_string}',
                            state,
                        )

                    target_class_name, target_name, *rest = parse_link_target(inside_code_text, state, context_name)
                    if len(rest) == 0 and target_class_name in state.classes:
                        class_def = state.classes[target_class_name]

                        if target_name in class_def.methods:
                            print_warning(
                                f'{state.current_class}.xml: Found a code string ' +
                                f'"{inside_code_text}" that matches the ' +
                                f'{target_class_name}.{target_name} method in ' +
                                f'{context_name}. {code_warning_if_intended_string}',
                                state,
                            )

                        elif target_name in class_def.constructors:
                            print_warning(
                                f'{state.current_class}.xml: Found a code string ' +
                                f'"{inside_code_text}" that matches the ' +
                                f'{target_class_name}.{target_name} constructor ' +
                                f'in {context_name}. {code_warning_if_intended_string}',
                                state,
                            )

                        elif target_name in class_def.operators:
                            print_warning(
                                f'{state.current_class}.xml: Found a code string ' +
                                f'"{inside_code_text}" that matches the ' +
                                f'{target_class_name}.{target_name} operator in ' +
                                f'{context_name}. {code_warning_if_intended_string}',
                                state,
                            )

                        elif target_name in class_def.properties:
                            print_warning(
                                f'{state.current_class}.xml: Found a code string ' +
                                f'"{inside_code_text}" that matches the ' +
                                f'{target_class_name}.{target_name} member in ' +
                                f'{context_name}. {code_warning_if_intended_string}',
                                state,
                            )

                        elif target_name in class_def.signals:
                            print_warning(
                                f'{state.current_class}.xml: Found a code string ' +
                                f'"{inside_code_text}" that matches the ' +
                                f'{target_class_name}.{target_name} signal in ' +
                                f'{context_name}. {code_warning_if_intended_string}',
                                state,
                            )

                        elif target_name in class_def.annotations:
                            print_warning(
                                f'{state.current_class}.xml: Found a code string ' +
                                f'"{inside_code_text}" that matches the ' +
                                f'{target_class_name}.{target_name} annotation ' +
                                f'in {context_name}. {code_warning_if_intended_string}',
                                state,
                            )

                        elif target_name in class_def.theme_items:
                            print_warning(
                                f'{state.current_class}.xml: Found a code string ' +
                                f'"{inside_code_text}" that matches the ' +
                                f'{target_class_name}.{target_name} theme property ' +
                                f'in {context_name}. {code_warning_if_intended_string}',
                                state,
                            )

                        elif target_name in class_def.constants:
                            print_warning(
                                f'{state.current_class}.xml: Found a code string ' +
                                f'"{inside_code_text}" that matches the ' +
                                f'{target_class_name}.{target_name} constant in ' +
                                f'{context_name}. {code_warning_if_intended_string}',
                                state,
                            )

                        else:
                            for enum in class_def.enums.values():
                                if target_name in enum.values:
                                    print_warning(
                                        f'{state.current_class}.xml: Found a code ' +
                                        f'string "{inside_code_text}" that matches ' +
                                        f'the {target_class_name}.{target_name} enum ' +
                                        f'value in {context_name}. {code_warning_if_intended_string}',
                                        state,
                                    )
                                    break

                    valid_param_context = isinstance(context, (MethodDef, SignalDef, AnnotationDef))
                    if valid_param_context:
                        context_params: List[ParameterDef] = context.parameters  # type: ignore
                        for param_def in context_params:
                            if param_def.name == inside_code_text:
                                print_warning(
                                    f'{state.current_class}.xml: Found a code string ' +
                                    f'"{inside_code_text}" that matches one of the parameters ' +
                                    f'in {context_name}. {code_warning_if_intended_string}',
                                    state,
                                )
                                break

            # Cross-references to items in this or other class documentation pages.
            elif is_in_tagset(tag_state.name, RESERVED_CROSSLINK_TAGS):
                link_target: str = tag_state.arguments

                if link_target == "":
                    print_error(
                        f'{state.current_class}.xml: Empty cross-reference link "[{tag_state.raw}]" in {context_name}.',
                        state,
                    )
                    tag_text = ""
                else:
                    if (
                        tag_state.name == "method"
                        or tag_state.name == "constructor"
                        or tag_state.name == "operator"
                        or tag_state.name == "member"
                        or tag_state.name == "signal"
                        or tag_state.name == "annotation"
                        or tag_state.name == "theme_item"
                        or tag_state.name == "constant"
                    ):
                        target_class_name, target_name, *rest = parse_link_target(link_target, state, context_name)
                        if len(rest) > 0:
                            print_error(
                                f'{state.current_class}.xml: Bad reference "{link_target}" in {context_name}.',
                                state,
                            )

                        # Default to the tag command name. This works by default for most tags,
                        # but method, member, and theme_item have special cases.
                        if target_class_name in state.classes:
                            class_def = state.classes[target_class_name]

                            if tag_state.name == "method":
                                if target_name not in class_def.methods:
                                    print_error(
                                        f'{state.current_class}.xml: Unresolved method ' +
                                        f'reference "{link_target}" in {context_name}.',
                                        state,
                                    )

                            elif tag_state.name == "constructor" and target_name not in class_def.constructors:
                                print_error(
                                    f'{state.current_class}.xml: Unresolved constructor ' +
                                    f'reference "{link_target}" in {context_name}.',
                                    state,
                                )

                            elif tag_state.name == "operator" and target_name not in class_def.operators:
                                print_error(
                                    f'{state.current_class}.xml: Unresolved operator reference ' +
                                    f'"{link_target}" in {context_name}.',
                                    state,
                                )

                            elif tag_state.name == "member":
                                if target_name not in class_def.properties:
                                    print_error(
                                        f'{state.current_class}.xml: Unresolved member ' +
                                        f'reference "{link_target}" in {context_name}.',
                                        state,
                                    )

                            elif tag_state.name == "signal" and target_name not in class_def.signals:
                                print_error(
                                    f'{state.current_class}.xml: Unresolved signal reference ' +
                                    f'"{link_target}" in {context_name}.',
                                    state,
                                )

                            elif tag_state.name == "annotation" and target_name not in class_def.annotations:
                                print_error(
                                    f'{state.current_class}.xml: Unresolved annotation ' +
                                    f'reference "{link_target}" in {context_name}.',
                                    state,
                                )

                            elif tag_state.name == "theme_item":
                                if target_name not in class_def.theme_items:
                                    print_error(
                                        f'{state.current_class}.xml: Unresolved theme '
                                        f'property reference "{link_target}" in {context_name}.',
                                        state,
                                    )

                            elif tag_state.name == "constant":
                                found = False

                                # Search in the current class
                                search_class_defs = [class_def]

                                if link_target.find(".") == -1:
                                    # Also search in @GlobalScope as a last resort if no class was specified
                                    search_class_defs.append(state.classes["@GlobalScope"])

                                for search_class_def in search_class_defs:
                                    if target_name in search_class_def.constants:
                                        target_class_name = search_class_def.name
                                        found = True

                                    else:
                                        for enum in search_class_def.enums.values():
                                            if target_name in enum.values:
                                                target_class_name = search_class_def.name
                                                found = True
                                                break

                                if not found:
                                    print_error(
                                        f'{state.current_class}.xml: Unresolved constant reference ' +
                                        f'"{link_target}" in {context_name}.',
                                        state,
                                    )

                        else:
                            print_error(
                                f'{state.current_class}.xml: Unresolved type reference ' +
                                f'"{target_class_name}" in method reference "{link_target}" in {context_name}.',
                                state,
                            )

                        tag_text = f"<xref href=\"{target_class_name}.{target_name}\"></xref>"

                    elif tag_state.name == "enum":
                        tag_text = make_enum(link_target, False, state)

                    elif tag_state.name == "param":
                        valid_param_context = isinstance(context, (MethodDef, SignalDef, AnnotationDef))
                        if not valid_param_context:
                            print_error(
                                f'{state.current_class}.xml: Argument reference ' +
                                f'"{link_target}" used outside of method, signal, or ' +
                                f'annotation context in {context_name}.',
                                state,
                            )
                        else:
                            context_params: List[ParameterDef] = context.parameters  # type: ignore
                            found = False
                            for param_def in context_params:
                                if param_def.name == link_target:
                                    found = True
                                    break
                            if not found:
                                print_error(
                                    f'{state.current_class}.xml: Unresolved argument reference ' +
                                    f'"{link_target}" in {context_name}.',
                                    state,
                                )

                        tag_text = f"``{link_target}``"

            # Formatting directives.

            elif is_in_tagset(tag_state.name, ["url"]):
                url_target = tag_state.arguments

                if url_target == "":
                    print_error(
                        f'{state.current_class}.xml: Misformatted [url] tag "[{tag_state.raw}]" in {context_name}.',
                        state,
                    )
                else:
                    # Unlike other tags, URLs are handled in full here, as we need to extract
                    # the optional link title to use `make_link`.
                    endurl_pos = text.find("[/url]", endq_pos + 1)
                    if endurl_pos == -1:
                        print_error(
                            f"{state.current_class}.xml: Tag depth mismatch for " +
                            f"[url]: no closing [/url] in {context_name}.",
                            state,
                        )
                        break
                    link_title = text[endq_pos + 1:endurl_pos]
                    tag_text = make_link(url_target, link_title)

                    pre_text = text[:pos]
                    post_text = text[endurl_pos + 6:]

                    if pre_text and pre_text[-1] not in MARKUP_ALLOWED_PRECEDENT:
                        pre_text += "\\ "
                    if post_text and post_text[0] not in MARKUP_ALLOWED_SUBSEQUENT:
                        post_text = "\\ " + post_text

                    text = pre_text + tag_text + post_text
                    pos = len(pre_text) + len(tag_text)
                    continue

            elif tag_state.name == "br":
                # Make a new paragraph instead of a linebreak, rst is not so linebreak friendly
                tag_text = "\n\n"
                # Strip potential leading spaces
                while post_text[0] == " ":
                    post_text = post_text[1:]

            elif tag_state.name == "center":
                if tag_state.closing:
                    tag_depth -= 1
                else:
                    tag_depth += 1
                tag_text = ""

            elif tag_state.name == "i":
                if tag_state.closing:
                    tag_depth -= 1
                else:
                    tag_depth += 1
                tag_text = "*"

            elif tag_state.name == "b":
                if tag_state.closing:
                    tag_depth -= 1
                else:
                    tag_depth += 1
                tag_text = "**"

            elif tag_state.name == "u":
                if tag_state.closing:
                    tag_depth -= 1
                else:
                    tag_depth += 1
                tag_text = ""

            elif tag_state.name == "lb":
                tag_text = "["

            elif tag_state.name == "rb":
                tag_text = "]"

            elif tag_state.name == "kbd":
                tag_text = "`"
                if tag_state.closing:
                    tag_text = tag_text + "</kbd>"
                    tag_depth -= 1
                else:
                    tag_text = "<kbd>" + tag_text
                    tag_depth += 1

            # Invalid syntax.
            else:
                if tag_state.closing:
                    print_error(
                        f'{state.current_class}.xml: Unrecognized closing tag "[{tag_state.raw}]" in {context_name}.',
                        state,
                    )

                    tag_text = f"[{tag_text}]"
                else:
                    print_error(
                        f'{state.current_class}.xml: Unrecognized opening tag "[{tag_state.raw}]" in {context_name}.',
                        state,
                    )

                    tag_text = f"``{tag_text}``"

        next_brac_pos = post_text.find("[", 0)
        iter_pos = 0
        while not inside_code:
            iter_pos = post_text.find("*", iter_pos, next_brac_pos)
            if iter_pos == -1:
                break
            post_text = f"{post_text[:iter_pos]}\\*{post_text[iter_pos + 1:]}"
            iter_pos += 2

        iter_pos = 0
        while not inside_code:
            iter_pos = post_text.find("_", iter_pos, next_brac_pos)
            if iter_pos == -1:
                break
            if not post_text[iter_pos + 1].isalnum():  # don't escape within a snake_case word
                post_text = f"{post_text[:iter_pos]}\\_{post_text[iter_pos + 1:]}"
                iter_pos += 2
            else:
                iter_pos += 1

        text = pre_text + tag_text + post_text
        pos = len(pre_text) + len(tag_text)

    if tag_depth > 0:
        print_error(
            f"{state.current_class}.xml: Tag depth mismatch: too many (or too few) open/close tags in {context_name}.",
            state,
        )

    return text


def get_method_return_type(definition: Union[AnnotationDef, MethodDef, SignalDef]) -> str:
    ret_type = ""

    if isinstance(definition, MethodDef):
        ret_type = definition.return_type.type_name

    return ret_type


def make_method_signature(
    definition: Union[AnnotationDef, MethodDef, SignalDef],
    spaces: bool,
    named_params: bool,
    xref_param_types: bool,
    state: State,
    sanitize: bool,
    always_include_parenthesis: bool
) -> str:
    qualifiers = None
    if isinstance(definition, (MethodDef, AnnotationDef)):
        qualifiers = definition.qualifiers

    varargs = qualifiers is not None and "vararg" in qualifiers
    params = []
    for parameter in definition.parameters:
        type_name = parameter.type_name.type_name
        if xref_param_types:
            type_name = make_type(parameter.type_name.type_name, state)

        if named_params:
            params.append(f"{type_name} {parameter.name}")
        else:
            params.append(type_name)

    out = definition.name.replace("operator ", "")
    if definition.name.startswith("operator ") and sanitize:
        out = sanitize_operator_name(definition.name, state)

    sep = ", " if spaces else ","
    if varargs:
        params += ["..."]

    if len(params):
        if definition.name.startswith("operator ") and spaces:
            out += " "
        out += f"({sep.join(params)})"
    elif always_include_parenthesis:
        out += "()"

    return out


def get_method_qualifiers(definition: Union[AnnotationDef, MethodDef]):
    out = ""
    for qualifier in definition.qualifiers.split():
        out += f"<abbr title=\"{get_qualifier_tooltip(qualifier)}\">{qualifier}</abbr>"
    return out


def get_qualifier_tooltip(qualifier: str):
    virtual_msg = "This method should typically be overridden by the user to have any effect."
    const_msg = "This method has no side effects. It doesn't modify any of the instance's member variables."
    vararg_msg = "This method accepts any number of arguments after the ones described here."
    constructor_msg = "This method is used to construct a type."
    static_msg = "This method doesn't need an instance to be called, so it can be called directly using the class name."
    operator_msg = "This method describes a valid operator to use with this type as left-hand operand."
    bitfield_msg = "This value is an integer composed as a bitmask of the following flags."
    void_msg = "No return value."

    if qualifier == "virtual":
        return virtual_msg
    elif qualifier == "const":
        return const_msg
    elif qualifier == "vararg":
        return vararg_msg
    elif qualifier == "constructor":
        return constructor_msg
    elif qualifier == "static":
        return static_msg
    elif qualifier == "operator":
        return operator_msg
    elif qualifier == "bitfield":
        return bitfield_msg
    elif qualifier == "void":
        return void_msg


def make_setter_signature(class_def: ClassDef, property_def: PropertyDef, state: State) -> str:
    if property_def.setter is None:
        return ""

    # If setter is a method available as a method definition, we use that.
    if property_def.setter in class_def.methods:
        setter = class_def.methods[property_def.setter][0]
    # Otherwise we fake it with the information we have available.
    else:
        setter_params: List[ParameterDef] = []
        setter_params.append(ParameterDef("value", property_def.type_name, None))
        setter = MethodDef(property_def.setter, TypeName("void"), setter_params, None, None)

    ret_type = make_type(get_method_return_type(setter), state)
    signature = make_method_signature(setter, True, True, True, state, False, False)
    return f"{ret_type} {signature}"


def make_getter_signature(class_def: ClassDef, property_def: PropertyDef, state: State) -> str:
    if property_def.getter is None:
        return ""

    # If getter is a method available as a method definition, we use that.
    if property_def.getter in class_def.methods:
        getter = class_def.methods[property_def.getter][0]
    # Otherwise we fake it with the information we have available.
    else:
        getter_params: List[ParameterDef] = []
        getter = MethodDef(property_def.getter, property_def.type_name, getter_params, None, None)

    ret_type = make_type(get_method_return_type(getter), state)
    signature = make_method_signature(getter, True, True, True, state, False, False)
    return f"{ret_type} {signature}"
