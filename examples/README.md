# Examples

Example docfx projects

* godot-docs-link - link to godot docs via xrefmap and docfx.
* project - example godot project with scripts.

## Creating Example Site

```bash
#  Load project in editor at least once
godot -v -e --path project --headless --quit-after 100

# Build xml based documentation
mkdir -p project/doc/godot
godot --path project --doctool doc/godot
godot --path project --doctool doc/classes --gdscript-docs res://scripts

# Convert docs to yml
gdxml2yml --filter project/doc/classes project/doc/classes project/doc/godot godot-docs-link/api

# Create site with docfx, to run add the --serve flag at the end
dotnet tool run docfx godot-docs-link/docfx.json
```
