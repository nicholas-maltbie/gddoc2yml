# Godot Documentation Built via DocFx

Building entire godot documentation via [docfx](https://github.com/dotnet/docfx)
and [gddoc2yml](https://github.com/nicholas-maltbie/gddoc2yml)

See the [Class Reference](api/index.md) for details.

```bash
# Install gddoc2yml
python3 -m pip install gddoc2yml

# Generate docs using gdxml2yml
gdxml2yml godot/doc/classes godot/modules godot/platform/android/doc_classes doc/godot/api

# Startup docfx website
dotnet tool run docfx --serve doc/docfx.json
```

See original godot docs here - [Godot Docs](https://docs.godotengine.org/en/stable/)
