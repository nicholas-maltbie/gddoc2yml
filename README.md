# Godot Doc 2 Yml

Convert godot xml docs exported via the `godot --doctool` for gdscript
to yml compatible with docfx.

## Install

Install gddoc2yml via pip

```bash
python3 -m pip install gddoc2yml
```

Then you will have the gdxml2yml command available:

```bash
gdxml2yml
    usage: gdxml2yml [-h] [--filter FILTER] path [path ...] output
    gdxml2yml: error: the following arguments are required: path, output

gdxml2yml -h
    usage: gdxml2yml [-h] [--filter FILTER] path [path ...] output

    Convert godot documentation xml file to yml for docfx.

    positional arguments:
    path             A path to an XML file or a directory containing XML files to parse.
    output           output folder to store all generated yml files.

    options:
    -h, --help       show this help message and exit
    --filter FILTER  The filepath pattern for XML files to filter
```

## Using gddoc2yml

Export xml docs for your project with godot, us gdxml2yml to generate yml api,
then use the gd

1. Generate xml docs for your project.

    Install godot command line tool (see [Godot's Command Line Tutorial](https://docs.godotengine.org/en/stable/tutorials/editor/command_line_tutorial.html#path) for details).

    Export docs for your gdscript to xml via the `--doctool` flag.

    ```bash
    # Example command to generate docs from scripts in project/scripts to dir doc/my-classes
    godot --path project --doctool doc/my-classes --gdscript-docs res://scripts
    ```

2. Use gdxml2yml to generate yml docs for your project.
    See references section for details on yml schema.

    ```bash
    # You will also need the original xml docs from
    # the godot repo, generate via godot --doctool <path>
    # to generate godot docs at a given path
    #   $ mkdir ref
    #   $ godot --doctool ref

    # Generate yml api for docfx.
    # Generates output at folder out/my-classes/api
    # Use the '--filter' flag to only generate docs for your files
    gdxml2yml --filter doc/my-classes doc/my-classes ref out/my-classes/api
    ```

3. Use your generated yml in docfx. see the [doc/docfx.json](doc/docfx.json) for an example.

    Make sure to include your api folder in the doc content

    ```json
    {
        "files": ["*.yml"],
        "src": "api",
        "dest": "api"
    },
    ```

## References

* [Godot -- CLI Reference](https://docs.godotengine.org/en/stable/tutorials/editor/command_line_tutorial.html#command-line-reference)
* [Godot -- make_rst.py](https://github.com/godotengine/godot/blob/master/doc/tools/make_rst.py)
* [DocFx -- Github](https://github.com/dotnet/docfx)
* [DocFx -- Introduction to Multiple Languages Support](https://xxred.gitee.io/docfx/tutorial/universalreference/intro_multiple_langs_support.html)
* [DocFx -- Custom Template](https://dotnet.github.io/docfx/docs/template.html?tabs=modern#custom-template)
* [DocFx -- .NET API Docs YAML Format](https://github.com/dotnet/docfx/blob/fe0bd0bfcbfecb655cc1cda2185df601fac1df23/docs/docs/dotnet-yaml-format.md)
* [DocFx -- PageViewModel.cs](https://github.com/dotnet/docfx/blob/main/src/Docfx.DataContracts.UniversalReference/PageViewModel.cs)
* [DocFx -- ItemViewModel.cs](https://github.com/dotnet/docfx/blob/main/src/Docfx.DataContracts.UniversalReference/ItemViewModel.cs)
* [DocFx -- Recommended XML tags for C#](https://learn.microsoft.com/en-us/dotnet/csharp/language-reference/xmldoc/recommended-tags)

## Development

This section consists of how to build and test the gddoc2yml project.

### Setup

Build package

```bash
# Install dependencies
python3 -m pip install -r requirements.txt

# Install build if required
# python3 -m pip install build
# Project will be created in dir dist
python3 -m build
```

### Linting

Lint using [flake8](https://github.com/pycqa/flake8/) tool.

```bash
# Run flake8 from .flake8 config file
# Install via python3 -m pip install flake8
python3 -m flake8 .
```

### Tests

Run tests for project via Python's unittest module -- [Unit testing framework](https://docs.python.org/3/library/unittest.html)

```bash
python3 -m unittest
```

#### Code Coverage

Compute code coverage using [coveragepy](https://github.com/nedbat/coveragepy)

```bash
# Get code coverage using coverage
# Install via python -m pip install coverage
coverage run -m unittest discover

# Get results
coverage report -m
```

### Build and Use Latest Version

Build godot docs using latest gddoc2yml.

```bash
# Install from repo
python3 -m pip install .

# Generate docs using gdxml2yml
gdxml2yml godot/doc/classes godot/modules godot/platform/android/doc_classes doc/api

# Startup docfx website
dotnet tool run docfx --serve doc/docfx.json
```
