# Tests

Run tests, see [README/Tests](../README.md#tests) for details on running tests.

## Updating Test Files

Update xml files for test run.

```PowerShell
# Build xml based documentation
mkdir -p tests/tmp
godot --doctool tests/tmp

# Copy test files over to test classes folder
foreach ($file in $(ls tests/classes))
{
    $fileName = Split-Path $file -leaf
    Copy-Item tests/tmp/doc/classes/$fileName tests/classes/$fileName -Force
}
```
