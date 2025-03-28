# Changelog

## In Progress

## v1.0.0 : 03-27-2025

* Added new --filter and --path parameters to gdxml2yml and gdxml2xrefmap
    * This is a breaking change, please see help for details.
* Updated godot version for test to 4.4
* Updated github actions associated with automation.

## v0.2.0 : 05-15-2024

* Added more fixes and support to gdxml2yml.
* Added extra command to generate xrefmap that points to godot docs.
* Added example docfx and godot project into the repo to show
    how to generate documentation site and automated with a github
    action workflow.

## v0.1.1 : 05-02-2024

* Added fix to how id is formatted for operators, signals, and annotation.
    * Made parenthesis optional and only included if arguments require.
* Small fixes to typos in code and docs.
* Added basic markdown linting to the project.

## v0.1.0 : 05-01-2024

Added main features to project. Converting godot doctool to docfx compatible
yml. Added support for the following types of attributes:

* Class description
* Online tutorials
* Signal descriptions
* Constant descriptions
* Annotation descriptions
* Property descriptions
* Constructor, Method, and Operator descriptions
* Theme property descriptions

In addition, I added a basic godot-template for docfx to support highlighting
gdscript code based off of [highlightjs-gdscript](https://github.com/highlightjs/highlightjs-gdscript)

## v0.0.1 : 04-12-2024

Initial project setup
