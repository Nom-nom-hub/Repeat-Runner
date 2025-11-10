import unittest
import tempfile
import os
import sys
from io import StringIO
from unittest.mock import patch, MagicMock
from repeat_runner.executor import execute_macro
from repeat_runner.logger import Logger
from repeat_runner.macros import load_macros, validate_macro_definition


class TestErrorHandling(unittest.TestCase):

    def setUp(self):
        """Set up test fixtures before each test method."""
        self.logger = Logger(dry_run=True)

    def test_invalid_macro_definition_error_handling(self):
        """Test that invalid macro definitions produce descriptive error messages."""
        invalid_macro = {
            'env': {'TEST_VAR': 'value'}  # Missing 'commands' key
        }

        with patch('sys.stderr', new_callable=StringIO) as mock_stderr:
            with self.assertRaises(SystemExit):
                execute_macro('invalid_macro', invalid_macro, self.logger)
            
            error_output = mock_stderr.getvalue()
            self.assertIn("Invalid macro definition", error_output)
            self.assertIn("must have 'commands' key", error_output)

    def test_invalid_macro_type_error_handling(self):
        """Test that invalid macro types produce descriptive error messages."""
        invalid_macro = "not_a_dict_or_list"

        with patch('sys.stderr', new_callable=StringIO) as mock_stderr:
            with self.assertRaises(SystemExit):
                execute_macro('invalid_macro', invalid_macro, self.logger)
            
            error_output = mock_stderr.getvalue()
            self.assertIn("Invalid macro definition", error_output)
            self.assertIn("must be a dictionary or list", error_output)

    def test_command_execution_failure_error_handling(self):
        """Test that command execution failures produce descriptive error messages."""
        macro_def = ['nonexistent_command_that_does_not_exist']

        with patch('subprocess.run') as mock_subprocess, \
             patch('sys.stderr', new_callable=StringIO) as mock_stderr:
            mock_result = MagicMock()
            mock_result.returncode = 1
            mock_result.stdout = ""
            mock_result.stderr = "Command not found"
            mock_subprocess.return_value = mock_result

            with self.assertRaises(SystemExit):
                execute_macro('failing_macro', macro_def, self.logger, continue_on_error=False)
            
            error_output = mock_stderr.getvalue()
            self.assertIn("Command failed with return code 1", error_output)
            self.assertIn("nonexistent_command_that_does_not_exist", error_output)
            self.assertIn("Command not found", error_output)
            self.assertIn("Stopping execution due to command failure", error_output)

    def test_command_execution_exception_error_handling(self):
        """Test that exceptions during command execution produce descriptive error messages."""
        macro_def = ['problematic_command']

        with patch('subprocess.run', side_effect=Exception("Subprocess failed completely")), \
             patch('sys.stderr', new_callable=StringIO) as mock_stderr:
            with self.assertRaises(SystemExit):
                execute_macro('exception_macro', macro_def, self.logger, continue_on_error=False)
            
            error_output = mock_stderr.getvalue()
            self.assertIn("Error executing command", error_output)
            self.assertIn("problematic_command", error_output)
            self.assertIn("Subprocess failed completely", error_output)

    def test_missing_runner_yaml_error_handling(self):
        """Test that missing runner.yaml produces descriptive error message."""
        with self.assertRaises(FileNotFoundError) as context:
            load_macros("nonexistent_file.yaml")
        
        self.assertIn("Macro file nonexistent_file.yaml not found", str(context.exception))

    def test_invalid_yaml_format_error_handling(self):
        """Test that invalid YAML format produces descriptive error message."""
        invalid_yaml_content = "invalid: [ yaml: content"
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.yaml') as tmp_file:
            tmp_file.write(invalid_yaml_content)
            tmp_file_path = tmp_file.name

        try:
            with self.assertRaises(ValueError) as context:
                load_macros(tmp_file_path)
            
            self.assertIn("Invalid YAML in macro file", str(context.exception))
        finally:
            os.unlink(tmp_file_path)

    def test_invalid_yaml_structure_error_handling(self):
        """Test that invalid YAML structure produces descriptive error message."""
        invalid_yaml_content = "42"  # Not a dictionary
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.yaml') as tmp_file:
            tmp_file.write(invalid_yaml_content)
            tmp_file_path = tmp_file.name

        try:
            with self.assertRaises(ValueError) as context:
                load_macros(tmp_file_path)
            
            self.assertIn("Invalid macro file format", str(context.exception))
        finally:
            os.unlink(tmp_file_path)

    def test_invalid_env_var_type_error_handling(self):
        """Test that invalid environment variable types produce descriptive error messages."""
        invalid_macro = {
            'commands': ['echo "test"'],
            'env': {
                'INVALID_VAR': 123  # Should be string, not int
            }
        }

        with patch('sys.stderr', new_callable=StringIO) as mock_stderr:
            with self.assertRaises(SystemExit):
                execute_macro('invalid_env_macro', invalid_macro, self.logger)
            
            error_output = mock_stderr.getvalue()
            self.assertIn("Invalid macro definition", error_output)
            self.assertIn("must be a string", error_output)
            self.assertIn("INVALID_VAR", error_output)

    def test_invalid_env_var_not_dict_error_handling(self):
        """Test that non-dict environment variables produce descriptive error messages."""
        invalid_macro = {
            'commands': ['echo "test"'],
            'env': ['TEST_VAR=value']  # Should be dict, not list
        }

        with patch('sys.stderr', new_callable=StringIO) as mock_stderr:
            with self.assertRaises(SystemExit):
                execute_macro('invalid_env_macro', invalid_macro, self.logger)
            
            error_output = mock_stderr.getvalue()
            self.assertIn("Invalid macro definition", error_output)
            self.assertIn("environment variables must be a dictionary", error_output)

    def test_invalid_commands_type_error_handling(self):
        """Test that non-list commands produce descriptive error messages."""
        invalid_macro = {
            'commands': 'echo "test"',  # Should be list, not string
        }

        with patch('sys.stderr', new_callable=StringIO) as mock_stderr:
            with self.assertRaises(SystemExit):
                execute_macro('invalid_commands_macro', invalid_macro, self.logger)
            
            error_output = mock_stderr.getvalue()
            self.assertIn("Invalid macro definition", error_output)
            self.assertIn("commands must be a list", error_output)

    def test_macro_call_nonexistent_error_handling(self):
        """Test that calling non-existent macros produces descriptive error messages."""
        macro_def = [{'call': 'nonexistent_macro'}]

        with patch('repeat_runner.executor.load_macros', return_value={}), \
             patch('sys.stderr', new_callable=StringIO) as mock_stderr:
            with self.assertRaises(SystemExit):
                execute_macro('calling_macro', macro_def, self.logger, continue_on_error=False)
            
            error_output = mock_stderr.getvalue()
            self.assertIn("Called macro 'nonexistent_macro' not found", error_output)

    def test_macro_call_nonexistent_with_continue_error_handling(self):
        """Test that calling non-existent macros with continue_on_error shows warning."""
        macro_def = [{'call': 'nonexistent_macro'}, 'echo "continue"']

        with patch('repeat_runner.executor.load_macros', return_value={}), \
             patch('sys.stderr', new_callable=StringIO) as mock_stderr, \
             patch('subprocess.run') as mock_subprocess:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = "continue"
            mock_result.stderr = ""
            mock_subprocess.return_value = mock_result

            # Should not raise SystemExit when continue_on_error=True
            try:
                execute_macro('calling_macro', macro_def, self.logger, continue_on_error=True)
            except SystemExit:
                self.fail("execute_macro raised SystemExit when continue_on_error=True")
            
            error_output = mock_stderr.getvalue()
            self.assertIn("Skipping missing macro call: nonexistent_macro", error_output)

    def test_subprocess_exception_error_handling(self):
        """Test that subprocess exceptions are properly handled with descriptive messages."""
        macro_def = ['problematic_command']

        with patch('subprocess.run', side_effect=OSError("No such file or directory")), \
             patch('sys.stderr', new_callable=StringIO) as mock_stderr:
            with self.assertRaises(SystemExit):
                execute_macro('os_error_macro', macro_def, self.logger, continue_on_error=False)
            
            error_output = mock_stderr.getvalue()
            self.assertIn("Error executing command", error_output)
            self.assertIn("problematic_command", error_output)
            self.assertIn("No such file or directory", error_output)

    def test_command_execution_failure_with_continue_on_error(self):
        """Test error handling when continue_on_error=True."""
        macro_def = ['failing_command', 'should_still_run']

        with patch('subprocess.run') as mock_subprocess, \
             patch('sys.stderr', new_callable=StringIO) as mock_stderr:
            # First call fails, second succeeds
            results = [
                MagicMock(returncode=1, stdout="", stderr="Command failed"),
                MagicMock(returncode=0, stdout="Success", stderr="")
            ]
            mock_subprocess.side_effect = results

            # Should not raise SystemExit when continue_on_error=True
            try:
                execute_macro('continue_macro', macro_def, self.logger, continue_on_error=True)
            except SystemExit:
                self.fail("execute_macro raised SystemExit when continue_on_error=True")
            
            error_output = mock_stderr.getvalue()
            self.assertIn("Continuing after command failure", error_output)

    def test_exception_handling_in_command_with_continue_on_error(self):
        """Test exception handling in command execution with continue_on_error=True."""
        macro_def = ['problematic_command', 'should_still_run']

        with patch('subprocess.run', side_effect=[Exception("Subprocess error"), 
                                                 MagicMock(returncode=0, stdout="Success", stderr="")]), \
             patch('sys.stderr', new_callable=StringIO) as mock_stderr:
            # Should not raise SystemExit when continue_on_error=True
            try:
                execute_macro('continue_exception_macro', macro_def, self.logger, continue_on_error=True)
            except SystemExit:
                self.fail("execute_macro raised SystemExit when continue_on_error=True")
            
            error_output = mock_stderr.getvalue()
            self.assertIn("Continuing after exception for command", error_output)

    def test_invalid_macro_file_format_error_handling(self):
        """Test error handling for invalid macro file formats."""
        invalid_yaml_content = "- just a list at root level"
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.yaml') as tmp_file:
            tmp_file.write(invalid_yaml_content)
            tmp_file_path = tmp_file.name

        try:
            with self.assertRaises(ValueError) as context:
                load_macros(tmp_file_path)
            
            self.assertIn("Invalid macro file format", str(context.exception))
        finally:
            os.unlink(tmp_file_path)

    def test_detailed_error_message_for_complex_invalid_macro(self):
        """Test detailed error message for complex invalid macro."""
        complex_invalid_macro = {
            'commands': 'not a list',  # Wrong type
            'env': ['not', 'a', 'dict'],  # Wrong type
            'extra_field': 'unexpected'  # Extra field (not necessarily an error, but testing validation)
        }

        with patch('sys.stderr', new_callable=StringIO) as mock_stderr:
            with self.assertRaises(SystemExit):
                execute_macro('complex_invalid_macro', complex_invalid_macro, self.logger)
            
            error_output = mock_stderr.getvalue()
            # Should catch the commands issue first (as it's validated first)
            self.assertIn("commands must be a list", error_output)

    def test_error_handling_with_verbose_logging(self):
        """Test error handling when verbose logging is enabled."""
        macro_def = ['failing_command']

        verbose_logger = Logger(verbose=True, dry_run=True)

        with patch('subprocess.run') as mock_subprocess, \
             patch('sys.stderr', new_callable=StringIO) as mock_stderr:
            mock_result = MagicMock()
            mock_result.returncode = 1
            mock_result.stdout = "Some output"
            mock_result.stderr = "Detailed error message"
            mock_subprocess.return_value = mock_result

            with self.assertRaises(SystemExit):
                execute_macro('verbose_failing_macro', macro_def, verbose_logger, continue_on_error=False)
            
            error_output = mock_stderr.getvalue()
            self.assertIn("Command failed with return code 1", error_output)
            self.assertIn("Detailed error message", error_output)
            # With verbose, should also show command output
            self.assertIn("Command errors:", error_output)


if __name__ == '__main__':
    unittest.main()