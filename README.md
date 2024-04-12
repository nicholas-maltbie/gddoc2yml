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
# Install dependencies
python3 -m pip install -r requirements.txt

# Install build if required
# python3 -m pip install build
# Project will be created in dir dist
python3 -m build
```

## Linting

Lint using [flake8](https://github.com/pycqa/flake8/) tool.

```bash
# Run flake8 from .flake8 config file
# Install via python3 -m pip install flake8
flake8 .
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

Build godot docs using latest gddoc2yml.

```bash
# Install from repo
python3 -m pip install .

# Generate docs using gdxml2yml
gdxml2yml godot/doc/classes doc/api

# Startup docfx website
dotnet tool run docfx --serve doc/docfx.json
```
