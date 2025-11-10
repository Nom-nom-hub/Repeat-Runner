import unittest
import tempfile
import os
from unittest.mock import patch, MagicMock, mock_open
from repeat_runner.executor import execute_macro
from repeat_runner.logger import Logger


class TestExecutor(unittest.TestCase):

    def setUp(self):
        """Set up test fixtures before each test method."""
        self.logger = Logger()
        self.simple_macro = ['echo "Hello"']
        self.dict_macro = {
            'commands': ['echo "Hello"'],
            'env': {'TEST_VAR': 'test_value'}
        }
        self.macro_with_calls = {
            'commands': [
                'echo "Before call"',
                {'call': 'inner_macro'},
                'echo "After call"'
            ]
        }

    @patch('subprocess.run')
    def test_execute_simple_macro(self, mock_subprocess):
        """Test executing a simple macro with a list of commands."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "Hello"
        mock_result.stderr = ""
        mock_subprocess.return_value = mock_result

        execute_macro('test_macro', self.simple_macro, self.logger)

        # Verify subprocess was called with the right parameters
        mock_subprocess.assert_called_once()
        args, kwargs = mock_subprocess.call_args
        self.assertEqual(args[0], 'echo "Hello"')
        self.assertTrue('env' in kwargs)

    @patch('subprocess.run')
    def test_execute_macro_with_env_vars(self, mock_subprocess):
        """Test executing a macro with environment variables."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "Hello"
        mock_result.stderr = ""
        mock_subprocess.return_value = mock_result

        execute_macro('test_macro', self.dict_macro, self.logger)

        # Verify subprocess was called with environment variables
        mock_subprocess.assert_called_once()
        args, kwargs = mock_subprocess.call_args
        self.assertEqual(args[0], 'echo "Hello"')
        self.assertTrue('env' in kwargs)
        self.assertIn('TEST_VAR', kwargs['env'])
        self.assertEqual(kwargs['env']['TEST_VAR'], 'test_value')

    @patch('repeat_runner.executor.load_macros')
    @patch('subprocess.run')
    def test_execute_macro_with_macro_call(self, mock_subprocess, mock_load_macros):
        """Test executing a macro that calls another macro."""
        # Mock the called macro
        mock_load_macros.return_value = {
            'inner_macro': {
                'commands': ['echo "Inner"']
            }
        }

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "Inner"
        mock_result.stderr = ""
        mock_subprocess.return_value = mock_result

        execute_macro('outer_macro', self.macro_with_calls, self.logger)

        # Verify that the inner macro was loaded and executed
        mock_load_macros.assert_called()
        # subprocess should be called for the inner macro's command
        self.assertTrue(mock_subprocess.called)

    @patch('repeat_runner.executor.load_macros')
    def test_execute_macro_missing_called_macro(self, mock_load_macros):
        """Test executing a macro that calls a non-existent macro."""
        # Mock to return empty dict (no macros found)
        mock_load_macros.return_value = {}

        with self.assertRaises(SystemExit):
            execute_macro('outer_macro', self.macro_with_calls, self.logger, continue_on_error=False)

    @patch('repeat_runner.executor.load_macros')
    @patch('subprocess.run')
    def test_execute_macro_missing_called_macro_continue_on_error(self, mock_subprocess, mock_load_macros):
        """Test executing a macro that calls a non-existent macro with continue_on_error=True."""
        # Mock to return empty dict (no macros found)
        mock_load_macros.return_value = {}

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "Before call\nAfter call"
        mock_result.stderr = ""
        mock_subprocess.return_value = mock_result

        # Should not raise SystemExit when continue_on_error=True
        try:
            execute_macro('outer_macro', self.macro_with_calls, self.logger, continue_on_error=True)
        except SystemExit:
            self.fail("execute_macro raised SystemExit when continue_on_error=True")

    def test_execute_macro_circular_call_detection(self):
        """Test that circular macro calls are detected and cause an exit."""
        executed_macros = {'macro_a'}
        
        with self.assertRaises(SystemExit):
            execute_macro('macro_a', self.simple_macro, self.logger, executed_macros=executed_macros)

    def test_execute_macro_invalid_definition(self):
        """Test that invalid macro definitions cause an exit."""
        invalid_macro = "invalid_macro_definition"

        with self.assertRaises(SystemExit):
            execute_macro('invalid_macro', invalid_macro, self.logger)

    @patch('subprocess.run')
    def test_execute_macro_command_failure_continue_on_error(self, mock_subprocess):
        """Test that command failures are handled when continue_on_error=True."""
        mock_result = MagicMock()
        mock_result.returncode = 1  # Simulate failure
        mock_result.stdout = ""
        mock_result.stderr = "Command failed"
        mock_subprocess.return_value = mock_result

        # Should not raise SystemExit when continue_on_error=True
        try:
            execute_macro('test_macro', self.simple_macro, self.logger, continue_on_error=True)
        except SystemExit:
            self.fail("execute_macro raised SystemExit when continue_on_error=True")

    @patch('subprocess.run')
    def test_execute_macro_command_failure_stop_on_error(self, mock_subprocess):
        """Test that command failures cause an exit when continue_on_error=False."""
        mock_result = MagicMock()
        mock_result.returncode = 1  # Simulate failure
        mock_result.stdout = ""
        mock_result.stderr = "Command failed"
        mock_subprocess.return_value = mock_result

        with self.assertRaises(SystemExit):
            execute_macro('test_macro', self.simple_macro, self.logger, continue_on_error=False)

    @patch('subprocess.run')
    def test_execute_macro_command_exception(self, mock_subprocess):
        """Test that exceptions during command execution are handled."""
        mock_subprocess.side_effect = Exception("Test exception")

        with self.assertRaises(SystemExit):
            execute_macro('test_macro', self.simple_macro, self.logger, continue_on_error=False)

    @patch('subprocess.run')
    def test_execute_macro_command_exception_continue_on_error(self, mock_subprocess):
        """Test that exceptions during command execution are handled with continue_on_error."""
        mock_subprocess.side_effect = Exception("Test exception")

        # Should not raise SystemExit when continue_on_error=True
        try:
            execute_macro('test_macro', self.simple_macro, self.logger, continue_on_error=True)
        except SystemExit:
            self.fail("execute_macro raised SystemExit when continue_on_error=True")

    def test_execute_macro_dry_run(self):
        """Test that dry run mode doesn't execute commands."""
        dry_run_logger = Logger(dry_run=True)
        
        # Should not raise any exceptions in dry run mode
        execute_macro('test_macro', self.simple_macro, dry_run_logger)


if __name__ == '__main__':
    unittest.main()