# Godot Doc 2 Yml

Convert godot xml docs exported via the `godot --doctool` for gdscript
to yml compatible with docfx.

## References

* [Godot -- CLI Reference](https://docs.godotengine.org/en/stable/tutorials/editor/command_line_tutorial.html#command-line-reference)
* [Godot -- make_rst.py](https://github.com/godotengine/godot/blob/master/doc/tools/make_rst.py)
* [DocFx -- Github](https://github.com/dotnet/docfx)
* [DocFx -- Introduction to Multiple Languages Support](https://xxred.gitee.io/docfx/tutorial/universalreference/intro_multiple_langs_support.html)

## Setup

Build package

```bash
# Install build if required
# python3 -m pip install build
python3 -m build

# Project will be created in dir dist
```

## Tests

```bash
python3 -m unittest
```

## Example

```bash
python3 src/gddoc2yml/gdxml2yml.py godot/doc/classes out
```
