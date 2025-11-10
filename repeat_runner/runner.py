#!/usr/bin/env python3
"""
Repeat-Runner: Run your repetitive dev workflows with a single command.
CLI entry point for the Repeat-Runner tool.
"""
import argparse
import sys
import os
import importlib.util

# Handle imports differently to work both when run as module and when installed
try:
    # Try relative import when used as a package
    from .macros import load_macros
    from .executor import execute_macro
    from .logger import Logger
except ImportError:
    # Try absolute import when run directly
    from repeat_runner.macros import load_macros
    from repeat_runner.executor import execute_macro
    from repeat_runner.logger import Logger


def main():
    parser = argparse.ArgumentParser(description="Repeat-Runner: Run your repetitive dev workflows with a single command.")
    parser.add_argument('command', choices=['run', 'list'], help='Command to execute')
    parser.add_argument('macro_name', nargs='?', help='Name of the macro to run (required for run command)')
    parser.add_argument('--dry-run', action='store_true', help='Print commands without execution')
    parser.add_argument('--verbose', action='store_true', help='Show real-time command output')
    parser.add_argument('--continue', dest='continue_on_error', action='store_true', help='Continue on command failure')
    parser.add_argument('--log-file', help='Path to log file for command execution')

    args = parser.parse_args()

    logger = Logger(dry_run=args.dry_run, verbose=args.verbose, log_file=args.log_file)

    try:
        macros = load_macros()
        if not macros:
            logger.warn("No macros found in runner.yaml file.")
    except FileNotFoundError:
        logger.error("runner.yaml not found. Please create a runner.yaml file in the current directory.")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Invalid macro definition in runner.yaml: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error loading macros: {type(e).__name__}: {e}")
        sys.exit(1)

    if args.command == 'list':
        logger.info("Available macros:")
        if macros is not None:
            for name in macros.keys():
                logger.info(f"  - {name}")
        else:
            logger.warn("Could not load macros - no macros available")
        if logger.file_handle:
            logger.close()
        return

    if args.command == 'run':
        if not args.macro_name:
            logger.error("Macro name is required for run command")
            parser.print_help()
            sys.exit(2)

        if macros is None or args.macro_name not in macros:
            logger.error(f"Macro '{args.macro_name}' not found")
            sys.exit(1)

        macro = macros[args.macro_name]
        execute_macro(args.macro_name, macro, logger, args.continue_on_error)
        
        if logger.file_handle:
            logger.close()


# Don't execute main when imported as a module
# if __name__ == "__main__":
#     main()