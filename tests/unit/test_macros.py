import unittest
import tempfile
import os
from unittest.mock import patch, mock_open
from repeat_runner.macros import load_macros, validate_macro_definition


class TestMacros(unittest.TestCase):

    def setUp(self):
        """Set up test fixtures before each test method."""
        self.valid_yaml_content = """
macros:
  test_macro:
    commands:
      - echo "Hello World"
    env:
      TEST_VAR: "test_value"
  simple_macro:
    commands:
      - ls -la
"""
        self.simple_yaml_content = """
simple_macro:
  commands:
    - echo "Simple command"
test_macro:
  commands:
    - echo "Test command"
  env:
    TEST_VAR: "test_value"
"""

    def test_load_macros_from_existing_file(self):
        """Test loading macros from a valid YAML file."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.yaml') as tmp_file:
            tmp_file.write(self.valid_yaml_content)
            tmp_file_path = tmp_file.name

        try:
            macros = load_macros(tmp_file_path)
            self.assertIn('test_macro', macros)
            self.assertIn('simple_macro', macros)
            self.assertEqual(macros['test_macro']['env']['TEST_VAR'], 'test_value')
        finally:
            os.unlink(tmp_file_path)

    def test_load_macros_file_not_found(self):
        """Test that FileNotFoundError is raised when file doesn't exist."""
        with self.assertRaises(FileNotFoundError):
            load_macros("nonexistent_file.yaml")

    def test_load_macros_invalid_yaml(self):
        """Test that ValueError is raised for invalid YAML."""
        invalid_yaml = "invalid: [ yaml: content"
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.yaml') as tmp_file:
            tmp_file.write(invalid_yaml)
            tmp_file_path = tmp_file.name

        try:
            with self.assertRaises(ValueError):
                load_macros(tmp_file_path)
        finally:
            os.unlink(tmp_file_path)

    def test_load_macros_no_macros_key(self):
        """Test loading macros when there's no 'macros' key in the YAML."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.yaml') as tmp_file:
            tmp_file.write(self.simple_yaml_content)
            tmp_file_path = tmp_file.name

        try:
            macros = load_macros(tmp_file_path)
            self.assertIn('simple_macro', macros)
            self.assertIn('test_macro', macros)
            self.assertEqual(macros['test_macro']['env']['TEST_VAR'], 'test_value')
        finally:
            os.unlink(tmp_file_path)

    def test_validate_macro_definition_valid_dict(self):
        """Test validation of a valid macro definition (dict format)."""
        macro_def = {
            'commands': ['echo "test"'],
            'env': {'TEST_VAR': 'value'}
        }
        result = validate_macro_definition('test_macro', macro_def)
        self.assertTrue(result)

    def test_validate_macro_definition_valid_list(self):
        """Test validation of a valid macro definition (list format)."""
        macro_def = ['echo "test"']
        result = validate_macro_definition('test_macro', macro_def)
        self.assertTrue(result)

    def test_validate_macro_definition_missing_commands(self):
        """Test validation fails when 'commands' key is missing."""
        macro_def = {
            'env': {'TEST_VAR': 'value'}
        }
        with self.assertRaises(ValueError) as context:
            validate_macro_definition('test_macro', macro_def)
        self.assertIn("must have 'commands' key", str(context.exception))

    def test_validate_macro_definition_commands_not_list(self):
        """Test validation fails when 'commands' is not a list."""
        macro_def = {
            'commands': 'echo "test"'
        }
        with self.assertRaises(ValueError) as context:
            validate_macro_definition('test_macro', macro_def)
        self.assertIn("commands must be a list", str(context.exception))

    def test_validate_macro_definition_env_not_dict(self):
        """Test validation fails when 'env' is not a dictionary."""
        macro_def = {
            'commands': ['echo "test"'],
            'env': ['TEST_VAR=value']
        }
        with self.assertRaises(ValueError) as context:
            validate_macro_definition('test_macro', macro_def)
        self.assertIn("environment variables must be a dictionary", str(context.exception))

    def test_validate_macro_definition_env_values_not_string(self):
        """Test validation fails when environment variable values are not strings."""
        macro_def = {
            'commands': ['echo "test"'],
            'env': {'TEST_VAR': 123}
        }
        with self.assertRaises(ValueError) as context:
            validate_macro_definition('test_macro', macro_def)
        self.assertIn("must be a string", str(context.exception))

    def test_validate_macro_definition_invalid_type(self):
        """Test validation fails when macro definition is not dict or list."""
        macro_def = "invalid"
        with self.assertRaises(ValueError) as context:
            validate_macro_definition('test_macro', macro_def)
        self.assertIn("must be a dictionary or list", str(context.exception))

    def test_load_macros_empty_file(self):
        """Test loading macros from an empty file."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.yaml') as tmp_file:
            tmp_file.write("")
            tmp_file_path = tmp_file.name

        try:
            macros = load_macros(tmp_file_path)
            self.assertEqual(macros, {})
        finally:
            os.unlink(tmp_file_path)

    def test_load_macros_only_macros_key(self):
        """Test loading macros when content is under 'macros' key."""
        yaml_content = """
macros:
  build:
    commands:
      - npm run build
  test:
    commands:
      - npm test
    env:
      NODE_ENV: test
"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.yaml') as tmp_file:
            tmp_file.write(yaml_content)
            tmp_file_path = tmp_file.name

        try:
            macros = load_macros(tmp_file_path)
            self.assertIn('build', macros)
            self.assertIn('test', macros)
            self.assertEqual(macros['test']['env']['NODE_ENV'], 'test')
        finally:
            os.unlink(tmp_file_path)


if __name__ == '__main__':
    unittest.main()