import unittest
import tempfile
import os
import sys
from io import StringIO
from unittest.mock import patch, MagicMock
from repeat_runner.runner import main
from repeat_runner.executor import execute_macro
from repeat_runner.logger import Logger
from repeat_runner.macros import load_macros, validate_macro_definition


class TestIntegration(unittest.TestCase):

    def setUp(self):
        """Set up test fixtures before each test method."""
        self.original_cwd = os.getcwd()
        self.temp_dir = tempfile.mkdtemp()
        os.chdir(self.temp_dir)

    def tearDown(self):
        """Clean up after each test method."""
        os.chdir(self.original_cwd)
        # Clean up temp directory
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def create_runner_yaml(self, content):
        """Helper to create a runner.yaml file."""
        with open('runner.yaml', 'w') as f:
            f.write(content)

    def test_complete_workflow_with_env_vars(self):
        """Test complete workflow with environment variables."""
        yaml_content = """
macros:
  env_test:
    commands:
      - echo "ENV_VAR is $TEST_ENV_VAR"
    env:
      TEST_ENV_VAR: "integration_test_value"
"""
        self.create_runner_yaml(yaml_content)
        
        # Load and validate macros
        macros = load_macros('runner.yaml')
        self.assertIn('env_test', macros)
        
        # Validate the macro definition
        validate_macro_definition('env_test', macros['env_test'])
        
        # Execute the macro
        logger = Logger(dry_run=True)  # Use dry run to avoid actual command execution
        execute_macro('env_test', macros['env_test'], logger)
        
        # The macro should execute without errors

    def test_complete_workflow_with_macro_chaining(self):
        """Test complete workflow with macro chaining."""
        yaml_content = """
macros:
  setup:
    commands:
      - echo "Setting up..."
  build:
    commands:
      - call: setup
      - echo "Building..."
  test:
    commands:
      - call: build
      - echo "Testing..."
"""
        self.create_runner_yaml(yaml_content)
        
        # Load and validate macros
        macros = load_macros('runner.yaml')
        self.assertIn('setup', macros)
        self.assertIn('build', macros)
        self.assertIn('test', macros)
        
        # Execute the top-level macro that chains others
        logger = Logger(dry_run=True)  # Use dry run to avoid actual command execution
        execute_macro('test', macros['test'], logger)
        
        # The macro should execute without errors

    def test_complete_workflow_with_logging(self):
        """Test complete workflow with logging to file."""
        yaml_content = """
macros:
  log_test:
    commands:
      - echo "Logging test"
"""
        self.create_runner_yaml(yaml_content)
        
        # Create a temporary log file
        with tempfile.NamedTemporaryFile(delete=False) as log_file:
            log_file_path = log_file.name

        try:
            # Load and execute with logging
            macros = load_macros('runner.yaml')
            logger = Logger(log_file=log_file_path)
            execute_macro('log_test', macros['log_test'], logger)
            logger.close()
            
            # Verify log file was created with content
            self.assertTrue(os.path.exists(log_file_path))
            with open(log_file_path, 'r') as f:
                content = f.read()
                self.assertIn("Logging started", content)
                self.assertIn("EXECUTED: echo \"Logging test\"", content)
        finally:
            # Clean up log file
            if os.path.exists(log_file_path):
                os.unlink(log_file_path)

    @patch('sys.argv', ['repeat-runner', 'list'])
    @patch('sys.stdout', new_callable=StringIO)
    def test_cli_list_command_integration(self, mock_stdout):
        """Test CLI list command integration."""
        yaml_content = """
macros:
  cli_test1:
    commands:
      - echo "test"
  cli_test2:
    commands:
      - echo "test2"
"""
        self.create_runner_yaml(yaml_content)
        
        # Run the main function with list command
        try:
            main()
        except SystemExit:
            pass  # Expected after listing macros
        
        output = mock_stdout.getvalue()
        self.assertIn("Available macros:", output)
        self.assertIn("cli_test1", output)
        self.assertIn("cli_test2", output)

    @patch('sys.argv', ['repeat-runner', 'run', 'integration_test'])
    @patch('subprocess.run')
    def test_cli_run_command_integration(self, mock_subprocess):
        """Test CLI run command integration."""
        # Mock subprocess to avoid actual command execution
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "Command output"
        mock_result.stderr = ""
        mock_subprocess.return_value = mock_result
        
        yaml_content = """
macros:
  integration_test:
    commands:
      - echo "Integration test command"
    env:
      TEST_VAR: "test_value"
"""
        self.create_runner_yaml(yaml_content)
        
        # Run the main function with run command
        try:
            main()
        except SystemExit:
            pass  # Expected after successful execution
        
        # Verify subprocess was called
        mock_subprocess.assert_called_once()

    def test_circular_macro_detection_integration(self):
        """Test that circular macro calls are detected in full workflow."""
        yaml_content = """
macros:
  circular_a:
    commands:
      - call: circular_b
  circular_b:
    commands:
      - call: circular_a
"""
        self.create_runner_yaml(yaml_content)
        
        # Load macros
        macros = load_macros('runner.yaml')
        
        # Attempt to execute circular macro - should cause SystemExit
        logger = Logger()
        with self.assertRaises(SystemExit):
            execute_macro('circular_a', macros['circular_a'], logger)

    def test_invalid_macro_definition_integration(self):
        """Test that invalid macro definitions are caught in full workflow."""
        yaml_content = """
macros:
  invalid_macro:
    env:
      SOME_VAR: "missing commands"
"""
        self.create_runner_yaml(yaml_content)
        
        # Load macros
        macros = load_macros('runner.yaml')
        
        # Attempt to execute invalid macro - should cause SystemExit
        logger = Logger()
        with self.assertRaises(SystemExit):
            execute_macro('invalid_macro', macros['invalid_macro'], logger)

    def test_macro_with_invalid_env_vars(self):
        """Test that invalid environment variable definitions are caught."""
        yaml_content = """
macros:
  invalid_env_macro:
    commands:
      - echo "test"
    env:
      INVALID_VAR: 123  # Should be string, not int
"""
        self.create_runner_yaml(yaml_content)
        
        # Load macros
        macros = load_macros('runner.yaml')
        
        # Attempt to execute macro with invalid env var - should cause SystemExit
        logger = Logger()
        with self.assertRaises(SystemExit):
            execute_macro('invalid_env_macro', macros['invalid_env_macro'], logger)

    @patch('sys.argv', ['repeat-runner', 'run', 'env_macro_test', '--log-file', 'integration_test.log'])
    @patch('subprocess.run')
    def test_complete_workflow_with_env_vars_and_logging(self, mock_subprocess):
        """Test complete workflow with both environment variables and logging."""
        # Mock subprocess to avoid actual command execution
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "Environment value: test_value"
        mock_result.stderr = ""
        mock_subprocess.return_value = mock_result
        
        yaml_content = """
macros:
  env_macro_test:
    commands:
      - echo "Environment value: $TEST_ENV"
    env:
      TEST_ENV: "test_value"
"""
        self.create_runner_yaml(yaml_content)
        
        # Run the main function with run command and log file
        try:
            main()
        except SystemExit:
            pass  # Expected after successful execution
        
        # Verify log file was created
        self.assertTrue(os.path.exists('integration_test.log'))
        
        # Check log file content
        with open('integration_test.log', 'r') as f:
            content = f.read()
            self.assertIn("EXECUTED: echo \"Environment value: $TEST_ENV\"", content)
            self.assertIn("Environment value: test_value", content)

    def test_macro_chaining_with_env_vars(self):
        """Test macro chaining where each macro has environment variables."""
        yaml_content = """
macros:
  parent_macro:
    commands:
      - call: child_macro
      - echo "Parent done with $PARENT_VAR"
    env:
      PARENT_VAR: "parent_value"
  child_macro:
    commands:
      - echo "Child executing with $CHILD_VAR"
    env:
      CHILD_VAR: "child_value"
"""
        self.create_runner_yaml(yaml_content)
        
        # Load and execute macros
        macros = load_macros('runner.yaml')
        logger = Logger(dry_run=True)  # Use dry run to avoid actual command execution
        execute_macro('parent_macro', macros['parent_macro'], logger)
        
        # The macro should execute without errors despite multiple env vars in chain

    @patch('sys.argv', ['repeat-runner', 'run', 'chained_macro_test'])
    @patch('subprocess.run')
    def test_cli_macro_chaining_integration(self, mock_subprocess):
        """Test CLI integration with macro chaining."""
        # Mock subprocess
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "Success"
        mock_result.stderr = ""
        mock_subprocess.return_value = mock_result
        
        yaml_content = """
macros:
  first_macro:
    commands:
      - echo "First macro"
  chained_macro_test:
    commands:
      - call: first_macro
      - echo "Second command"
"""
        self.create_runner_yaml(yaml_content)
        
        # Run the main function
        try:
            main()
        except SystemExit:
            pass  # Expected after successful execution
        
        # Should have been called twice: once for first_macro, once for second command
        self.assertEqual(mock_subprocess.call_count, 2)


if __name__ == '__main__':
    unittest.main()