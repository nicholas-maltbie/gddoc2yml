# Examples

Example docfx projects

* godot-docs-link - link to godot docs via xrefmap and docfx.
* project - example godot project with scripts.

## Creating Example Site

```PowerShell
# Load project in editor at least once
godot -v --path examples/project --headless --import

# Build xml based documentation
mkdir -p examples/project/doc/godot
godot --path examples/project --doctool doc/godot
godot --path examples/project --doctool doc/classes `
    --gdscript-docs res://scripts --quit

# Convert docs to yml
gdxml2yml --filter examples/project/doc/classes `
    examples/project/doc/classes examples/project/doc/godot `
    examples/godot-docs-link/api

# Create site with docfx, to run add the --serve flag at the end
dotnet tool run docfx examples/godot-docs-link/docfx.json
```
