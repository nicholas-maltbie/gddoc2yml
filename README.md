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

Run tests for project via Python's unittest module -- [Unit testing framework](https://docs.python.org/3/library/unittest.html)

```bash
python3 -m unittest
```

### Code Coverage

Compute code coverage using [coveragepy](https://github.com/nedbat/coveragepy)

```bash
# Get code coverage using coverage
# Install via python -m pip install coverage
coverage run -m unittest discover

# Get results
coverage report -m
```

## Example

```bash
# Build latest version of package
python3 -m build

# Install from dist dir
python3 -m pip install dist/gddoc2yml-0.0.1-py3-none-any.whl

# Generate docs using gdxml2yml
gdxml2yml godot/doc/classes doc/api

# Startup docfx website
dotnet tool run docfx --serve doc/docfx.json
```
