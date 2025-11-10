"""
Module to execute macro commands sequentially
"""
import subprocess
import sys
import os
import importlib.util

# Handle imports differently to work both when run as module and when installed
try:
    # Try relative import when used as a package
    from .logger import Logger
    from .macros import validate_macro_definition, load_macros
except ImportError:
    # Try absolute import when run directly
    from repeat_runner.logger import Logger
    from repeat_runner.macros import validate_macro_definition, load_macros


def execute_macro(macro_name, macro_definition, logger, continue_on_error=False, executed_macros=None):
    """
    Execute a macro by running its commands sequentially.

    Args:
        macro_name (str): Name of the macro being executed
        macro_definition (dict or list): The macro definition containing commands
        logger (Logger): Logger instance for output
        continue_on_error (bool): Whether to continue on command failure
        executed_macros (set): Set of already executed macros to prevent circular calls
    """
    if executed_macros is None:
        executed_macros = set()
    
    if macro_name in executed_macros:
        logger.error(f"Circular macro call detected in macro '{macro_name}'. Call stack: {' -> '.join(executed_macros)} -> {macro_name}")
        sys.exit(1)
    
    executed_macros.add(macro_name)
    
    logger.info(f"Executing macro: {macro_name}")

    # Validate the macro definition
    try:
        validate_macro_definition(macro_name, macro_definition)
    except ValueError as e:
        logger.error(f"Invalid macro definition: {e}")
        sys.exit(1)

    # Handle both list of commands and dict with additional properties
    if isinstance(macro_definition, dict):
        commands = macro_definition.get('commands', [])
        # Get environment variables for this macro
        macro_env = macro_definition.get('env', {})
        
        # Create environment with macro-specific variables
        env = os.environ.copy()
        env.update(macro_env)
    elif isinstance(macro_definition, list):
        commands = macro_definition
        # No environment variables for simple list macros
        env = os.environ.copy()
    else:
        logger.error(f"Invalid macro definition format for {macro_name}")
        sys.exit(1)

    for i, command in enumerate(commands):
        # Check if this command is a macro call
        if isinstance(command, dict) and 'call' in command:
            called_macro_name = command['call']
            logger.info(f"Calling macro: {called_macro_name}")
            
            all_macros = load_macros()
            
            if all_macros is None or called_macro_name not in all_macros:
                logger.error(f"Macro '{called_macro_name}' not found")
                if not continue_on_error:
                    sys.exit(1)
                else:
                    logger.warn(f"Skipping missing macro call: {called_macro_name}")
                    continue
            
            called_macro_def = all_macros[called_macro_name]
            execute_macro(called_macro_name, called_macro_def, logger, continue_on_error, executed_macros)
        else:
            # Count only actual commands (not macro calls) for the progress indicator
            actual_commands = [c for c in commands if not (isinstance(c, dict) and 'call' in c)]
            command_index = actual_commands.index(command) + 1 if command in actual_commands else i+1
            total_commands = len(actual_commands)
            
            logger.info(f"Running command [{command_index}/{total_commands}]: {command}")

            if logger.dry_run:
                logger.info(f"[DRY RUN] Would execute: {command}")
                continue

            try:
                result = subprocess.run(
                    command,
                    shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    env=env  # Pass the environment with macro-specific variables
                )

                # Log the command execution
                logger.log_command(command, result.stdout.strip() if result.stdout.strip() else "(no output)", 
                                  result.stderr.strip() if result.stderr.strip() else "")

                if logger.verbose:
                    logger.info(f"Command output:\n{result.stdout}")
                    if result.stderr:
                        logger.error(f"Command errors:\n{result.stderr}")

                if result.returncode != 0:
                    logger.error(f"Command failed with return code {result.returncode}: {command}")
                    if result.stderr:
                        logger.error(f"Command errors:\n{result.stderr}")
                    if not continue_on_error:
                        logger.error("Stopping execution due to command failure.")
                        sys.exit(result.returncode)
                    else:
                        logger.warn(f"Continuing after command failure: {command}")
                else:
                    logger.info(f"Command completed successfully: {command}")

            except Exception as e:
                logger.log_command(command, "", str(e))
                logger.error(f"Error executing command '{command}': {e}")
                if not continue_on_error:
                    sys.exit(1)
                else:
                    logger.warn(f"Continuing after exception for command: {command}")

    executed_macros.remove(macro_name)
    logger.info(f"Macro '{macro_name}' completed successfully")