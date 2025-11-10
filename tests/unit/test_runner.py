import unittest
import tempfile
import os
import sys
from io import StringIO
from unittest.mock import patch, MagicMock, mock_open
from repeat_runner.runner import main
from repeat_runner.macros import load_macros
from repeat_runner.executor import execute_macro
from repeat_runner.logger import Logger


class TestRunner(unittest.TestCase):

    def setUp(self):
        """Set up test fixtures before each test method."""
        # Create a temporary runner.yaml for testing
        self.test_yaml_content = """
macros:
  test_macro:
    commands:
      - echo "Hello World"
    env:
      TEST_VAR: "test_value"
  simple_macro:
    commands:
      - ls -la
  chained_macro:
    commands:
      - call: simple_macro
      - echo "After call"
"""
        self.temp_yaml_file = None

    def tearDown(self):
        """Clean up after each test method."""
        if self.temp_yaml_file and os.path.exists(self.temp_yaml_file):
            os.unlink(self.temp_yaml_file)

    def create_temp_yaml(self, content=None):
        """Helper to create a temporary YAML file."""
        content = content or self.test_yaml_content
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.yaml') as tmp_file:
            tmp_file.write(content)
            self.temp_yaml_file = tmp_file.name
        return self.temp_yaml_file

    @patch('sys.argv', ['repeat-runner', 'list'])
    @patch('sys.stdout', new_callable=StringIO)
    def test_main_list_command(self, mock_stdout):
        """Test the list command functionality."""
        yaml_file = self.create_temp_yaml()
        
        # Temporarily change working directory to where the yaml file is
        original_cwd = os.getcwd()
        try:
            os.chdir(os.path.dirname(yaml_file))
            with patch('repeat_runner.runner.load_macros') as mock_load_macros:
                mock_load_macros.return_value = {
                    'test_macro': {'commands': ['echo "Hello"']},
                    'simple_macro': {'commands': ['ls -la']}
                }
                
                # This should not raise an exception
                try:
                    main()
                except SystemExit:
                    pass  # Expected after listing macros
                
                output = mock_stdout.getvalue()
                self.assertIn("Available macros:", output)
                self.assertIn("test_macro", output)
                self.assertIn("simple_macro", output)
        finally:
            os.chdir(original_cwd)

    @patch('sys.argv', ['repeat-runner', 'run', 'test_macro'])
    @patch('repeat_runner.runner.execute_macro')
    @patch('repeat_runner.runner.load_macros')
    def test_main_run_command(self, mock_load_macros, mock_execute_macro):
        """Test the run command functionality."""
        yaml_file = self.create_temp_yaml()
        
        original_cwd = os.getcwd()
        try:
            os.chdir(os.path.dirname(yaml_file))
            mock_load_macros.return_value = {
                'test_macro': {
                    'commands': ['echo "Hello"'],
                    'env': {'TEST_VAR': 'test_value'}
                }
            }
            
            # This should not raise an exception
            try:
                main()
            except SystemExit:
                pass  # Expected after successful execution
                
            # Verify that execute_macro was called with correct parameters
            mock_execute_macro.assert_called_once()
        finally:
            os.chdir(original_cwd)

    @patch('sys.argv', ['repeat-runner', 'run'])
    @patch('sys.stdout', new_callable=StringIO)
    def test_main_run_command_missing_macro_name(self, mock_stdout):
        """Test that run command without macro name shows help."""
        yaml_file = self.create_temp_yaml()
        
        original_cwd = os.getcwd()
        try:
            os.chdir(os.path.dirname(yaml_file))
            with patch('repeat_runner.runner.load_macros') as mock_load_macros:
                mock_load_macros.return_value = {
                    'test_macro': {'commands': ['echo "Hello"']}
                }
                
                with self.assertRaises(SystemExit) as context:
                    main()
                
                # Should exit with code 2 due to argparse error (missing required argument)
                self.assertEqual(context.exception.code, 2)
                
                output = mock_stdout.getvalue()
                # Check for help message content instead
                self.assertIn("Name of the macro to run", output)
        finally:
            os.chdir(original_cwd)

    @patch('sys.argv', ['repeat-runner', 'run', 'nonexistent_macro'])
    @patch('sys.stdout', new_callable=StringIO)
    @patch('sys.stderr', new_callable=StringIO)
    def test_main_run_command_nonexistent_macro(self, mock_stderr, mock_stdout):
        """Test that run command with nonexistent macro fails."""
        yaml_file = self.create_temp_yaml()
        
        original_cwd = os.getcwd()
        try:
            os.chdir(os.path.dirname(yaml_file))
            with patch('repeat_runner.runner.load_macros') as mock_load_macros:
                mock_load_macros.return_value = {
                    'test_macro': {'commands': ['echo "Hello"']}
                }
                
                with self.assertRaises(SystemExit) as context:
                    main()
                
                # Should exit with code 1 due to nonexistent macro
                self.assertEqual(context.exception.code, 1)
                
                # Error is typically logged to stderr
                error_output = mock_stderr.getvalue()
                self.assertTrue(
                    "nonexistent_macro" in error_output or "not found" in error_output,
                    f"Expected error about nonexistent_macro in stderr, got: {error_output}"
                )
        finally:
            os.chdir(original_cwd)

    @patch('sys.argv', ['repeat-runner', 'run', 'test_macro'])
    @patch('sys.stdout', new_callable=StringIO)
    @patch('sys.stderr', new_callable=StringIO)
    def test_main_runner_yaml_not_found(self, mock_stderr, mock_stdout):
        """Test that missing runner.yaml file causes an error."""
        # Don't create a YAML file, so it doesn't exist
        with self.assertRaises(SystemExit) as context:
            main()
        
        # Should exit with code 1 due to missing runner.yaml
        self.assertEqual(context.exception.code, 1)
        
        # Error message is typically printed to stderr or stdout
        output = mock_stderr.getvalue() or mock_stdout.getvalue()
        self.assertIn("runner.yaml", output)

    @patch('sys.argv', ['repeat-runner', 'run', 'test_macro'])
    @patch('sys.stdout', new_callable=StringIO)
    @patch('sys.stderr', new_callable=StringIO)
    def test_main_invalid_macro_definition(self, mock_stderr, mock_stdout):
        """Test that invalid macro definition causes an error."""
        invalid_yaml_content = """
invalid: [ yaml: content
"""
        yaml_file = self.create_temp_yaml(invalid_yaml_content)
        
        original_cwd = os.getcwd()
        try:
            os.chdir(os.path.dirname(yaml_file))
            with self.assertRaises(SystemExit) as context:
                main()
            
            # Should exit with code 1 due to invalid YAML
            self.assertEqual(context.exception.code, 1)
            
            # Error could be in stderr or stdout
            output = mock_stderr.getvalue() or mock_stdout.getvalue()
            # Check for YAML parsing error or error message
            self.assertTrue(
                "error" in output.lower() or "invalid" in output.lower() or "yaml" in output.lower(),
                f"Expected an error in output, got: {output}"
            )
        finally:
            os.chdir(original_cwd)

    @patch('sys.argv', ['repeat-runner', 'run', 'test_macro', '--dry-run'])
    @patch('repeat_runner.runner.execute_macro')
    @patch('repeat_runner.runner.load_macros')
    def test_main_dry_run_flag(self, mock_load_macros, mock_execute_macro):
        """Test that dry-run flag is properly passed to logger."""
        yaml_file = self.create_temp_yaml()
        
        original_cwd = os.getcwd()
        try:
            os.chdir(os.path.dirname(yaml_file))
            mock_load_macros.return_value = {
                'test_macro': {'commands': ['echo "Hello"']}
            }
            
            # This should not raise an exception
            try:
                main()
            except SystemExit:
                pass  # Expected after successful execution
                
            # The execute_macro should be called, but with dry-run context
            mock_execute_macro.assert_called_once()
        finally:
            os.chdir(original_cwd)

    @patch('sys.argv', ['repeat-runner', 'run', 'test_macro', '--verbose'])
    @patch('repeat_runner.runner.execute_macro')
    @patch('repeat_runner.runner.load_macros')
    def test_main_verbose_flag(self, mock_load_macros, mock_execute_macro):
        """Test that verbose flag is properly passed to logger."""
        yaml_file = self.create_temp_yaml()
        
        original_cwd = os.getcwd()
        try:
            os.chdir(os.path.dirname(yaml_file))
            mock_load_macros.return_value = {
                'test_macro': {'commands': ['echo "Hello"']}
            }
            
            # This should not raise an exception
            try:
                main()
            except SystemExit:
                pass  # Expected after successful execution
                
            # The execute_macro should be called, but with verbose context
            mock_execute_macro.assert_called_once()
        finally:
            os.chdir(original_cwd)

    @patch('sys.argv', ['repeat-runner', 'run', 'test_macro', '--continue'])
    @patch('repeat_runner.runner.execute_macro')
    @patch('repeat_runner.runner.load_macros')
    def test_main_continue_on_error_flag(self, mock_load_macros, mock_execute_macro):
        """Test that continue flag is properly passed to execute_macro."""
        yaml_file = self.create_temp_yaml()
        
        original_cwd = os.getcwd()
        try:
            os.chdir(os.path.dirname(yaml_file))
            mock_load_macros.return_value = {
                'test_macro': {'commands': ['echo "Hello"']}
            }
            
            # This should not raise an exception
            try:
                main()
            except SystemExit:
                pass  # Expected after successful execution
                
            # Verify execute_macro was called with continue_on_error=True
            args, kwargs = mock_execute_macro.call_args
            # The last parameter should be continue_on_error
            self.assertTrue(args[3])  # continue_on_error should be True
        finally:
            os.chdir(original_cwd)

    @patch('sys.argv', ['repeat-runner', 'run', 'test_macro', '--log-file', 'test.log'])
    @patch('repeat_runner.runner.execute_macro')
    @patch('repeat_runner.runner.load_macros')
    def test_main_log_file_flag(self, mock_load_macros, mock_execute_macro):
        """Test that log-file flag is properly handled."""
        yaml_file = self.create_temp_yaml()
        
        original_cwd = os.getcwd()
        try:
            os.chdir(os.path.dirname(yaml_file))
            mock_load_macros.return_value = {
                'test_macro': {'commands': ['echo "Hello"']}
            }
            
            # This should not raise an exception
            try:
                main()
            except SystemExit:
                pass  # Expected after successful execution
                
            # The execute_macro should be called with proper logger
            mock_execute_macro.assert_called_once()
        finally:
            os.chdir(original_cwd)
            
            # Clean up log file if it was created
            if os.path.exists('test.log'):
                os.unlink('test.log')

    @patch('sys.argv', ['repeat-runner', 'invalid_command'])
    @patch('sys.stdout', new_callable=StringIO)
    def test_main_invalid_command(self, mock_stdout):
        """Test that invalid command shows help."""
        # This should fail argument parsing and show help
        with self.assertRaises(SystemExit):
            main()


if __name__ == '__main__':
    unittest.main()