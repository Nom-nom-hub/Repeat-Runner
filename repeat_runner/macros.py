"""
Module to load and parse macro definitions from runner.yaml
"""
import yaml
import os


def load_macros(file_path="runner.yaml"):
    """
    Load macros from the specified YAML file.
    
    Args:
        file_path (str): Path to the YAML file containing macro definitions
        
    Returns:
        dict: Dictionary of macro definitions
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Macro file {file_path} not found")
    
    with open(file_path, 'r') as file:
        try:
            data = yaml.safe_load(file)
            if data is None:
                return {}
            # If the root of the YAML is just a dict of macros, return it directly
            # Otherwise, look for a 'macros' key
            if isinstance(data, dict):
                if 'macros' in data:
                    return data['macros']
                else:
                    # Assume the entire file is the macros dictionary
                    return data
            else:
                raise ValueError("Invalid macro file format: root must be a dictionary")
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in macro file: {e}")


def validate_macro_definition(macro_name, macro_def):
    """
    Validate a macro definition for required fields and correct structure
    
    Args:
        macro_name (str): Name of the macro
        macro_def (dict): The macro definition
    
    Returns:
        bool: True if valid, raises ValueError if invalid
    """
    if not isinstance(macro_def, (dict, list)):
        raise ValueError(f"Macro '{macro_name}' must be a dictionary or list, got {type(macro_def).__name__}")
    
    if isinstance(macro_def, dict):
        if 'commands' not in macro_def:
            raise ValueError(f"Macro '{macro_name}' must have 'commands' key. Valid keys are: 'commands', 'env'")
        if not isinstance(macro_def['commands'], list):
            raise ValueError(f"Macro '{macro_name}' commands must be a list, got {type(macro_def['commands']).__name__}")
        
        # Validate environment variables if present
        if 'env' in macro_def:
            if not isinstance(macro_def['env'], dict):
                raise ValueError(f"Macro '{macro_name}' environment variables must be a dictionary, got {type(macro_def['env']).__name__}")
            # Check that environment variable values are strings
            for key, value in macro_def['env'].items():
                if not isinstance(value, str):
                    raise ValueError(f"Environment variable '{key}' in macro '{macro_name}' must be a string, got {type(value).__name__}")
    
    return True