# Godot Doc 2 Yml

Convert godot xml docs exported via the `godot --doctool` for gdscript
to yml compatible with docfx.

## Install

Install gddoc2yml via pip

```bash
python3 -m pip install gddoc2yml
```

Then you will have the gdxml2yml and gdxml2xrefmap command available:

<!-- markdownlint-disable MD013 -->

```bash
gdxml2yml -h
    usage: gdxml2yml [-h] --path PATH [PATH ...] [--filter FILTER [FILTER ...]] --output OUTPUT [--verbose VERBOSE]

    Convert godot documentation xml file to yml for docfx.

    options:
      -h, --help            show this help message and exit
      --path PATH [PATH ...]
                            A path to an XML file or a directory containing XML files to parse.
      --filter FILTER [FILTER ...]
                            The filepath patterns for XML files to filter.
      --output OUTPUT       Output folder to store all generated yml files.
      --verbose VERBOSE     Verbose output as part of project

gdxml2xrefmap -h
    usage: gdxml2xrefmap [-h] [--path PATH [PATH ...]] [--filter FILTER [FILTER ...]] [--output OUTPUT]

    Convert godot documentation xml files into a xrefmap compatible with DoxFx.

    options:
      -h, --help            show this help message and exit
      --path PATH [PATH ...]
                            A path to an XML file or a directory containing XML files to parse.
      --filter FILTER [FILTER ...]
                            The filepath patterns for XML files to filter.
      --output OUTPUT       output path to store xrefmap.
```

<!-- markdownlint-enable MD013 -->

## Using gddoc2yml

Export xml docs for your project with godot, us gdxml2yml to generate yml api,
then use the gd

1. Generate xml docs for your project.

    Install godot command line tool (see
    [Godot's Command Line Tutorial](https://docs.godotengine.org/en/stable/tutorials/editor/command_line_tutorial.html#path)
    for details).

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

3. Use your generated yml in docfx. see the [doc/docfx.json](doc/docfx.json) for
    an example. Make sure to include your api folder in the doc content

    ```json
    {
        "files": ["*.yml"],
        "src": "api",
        "dest": "api"
    },
    ```

### Generating xrefmap for Godot Docs

Included is an additional command, `gdxml2xrefmap` to generate
an xrefmap for the godot docs.

```bash
gdxml2xrefmap --path godot/doc/classes godot/modules --output out/godot_xrefmap.yml
```

**Note** the build for this repo contains an xrefmap that points to godot's
documentation. You can reference this in your `docfx.json` file as a `xref`
like so:

```json
{
  "build": {
    "xref": [
      "https://gddoc2yml.nickmaltbie.com/xrefmap/godot_xrefmap.yml"
    ]
  }
}
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

#### Markdown Linting

Markdown linting via [markdownlint](https://github.com/DavidAnson/markdownlint)
can be installed via npm.

```PowerShell
# Install cli version via npm
npm install -g markdownlint-cli

# Run on local repo
markdownlint .
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
# Download submodules
git submodule update --init godot

# Install from repo
python3 -m pip install .

# Generate docs using gdxml2yml
gdxml2yml --path godot --output doc/godot/api

# Generate xrefmap using gdxml2xrefmap
gdxml2xrefmap --path godot/doc/classes godot/modules doc/xrefmap/godot_xrefmap.yml

# Startup docfx website
dotnet tool run docfx --serve doc/docfx.json
```
