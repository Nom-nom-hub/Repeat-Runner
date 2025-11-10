# Repeat-Runner CLI Reference

## Command Syntax
```
runner <command> [options] [macro_name]
```

## Commands
- `list` - List all available macros
- `run` - Run a specific macro

## Options

### Basic Options
- `--dry-run` - Print commands without executing them
- `--verbose` - Show real-time command output
- `--continue` - Continue executing commands even if one fails

### New in v2
- `--log-file <path>` - Log command execution to the specified file

## Examples

### Basic Usage
```bash
# List all macros
runner list

# Run a macro
runner run myMacro

# Dry run (show commands without executing)
runner run myMacro --dry-run

# Run with verbose output
runner run myMacro --verbose

# Continue on error
runner run myMacro --continue
```

### v2 Features Examples
```bash
# Run with logging to file
runner run myMacro --log-file execution.log

# Run with verbose output and logging
runner run myMacro --verbose --log-file execution.log

# Run with continue on error and logging
runner run myMacro --continue --log-file execution.log

# Combine all options
runner run myMacro --verbose --continue --log-file execution.log
```

## Environment Variables in Commands
When using macros with environment variables, the variables will be available in your commands:

```bash
# If your macro has env variables like:
# myMacro:
#   commands:
#     - echo "Hello $USER_NAME"
#   env:
#     USER_NAME: "John"

# The command will expand to "echo Hello John" when executed
```

## Macro Chaining
When using macro chaining (the `call` syntax in your YAML), the called macros will be executed as part of the workflow:

```yaml
# This macro will call other macros in sequence
workflow:
  commands:
    - call: setup
    - call: build
    - call: test
```

## Exit Codes
- `0` - Success
- `1` - General error
- Other codes - Command-specific error codes from failed subprocesses