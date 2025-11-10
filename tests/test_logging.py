import unittest
import tempfile
import os
from unittest.mock import patch, MagicMock
from repeat_runner.executor import execute_macro
from repeat_runner.logger import Logger


class TestCommandExecutionLogging(unittest.TestCase):

    def setUp(self):
        """Set up test fixtures before each test method."""
        pass  # No specific setup needed

    def test_command_execution_logs_to_file_with_correct_format(self):
        """Test that command execution is properly logged to file with correct format."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as log_file:
            log_file_path = log_file.name

        try:
            logger = Logger(log_file=log_file_path)
            
            # Simulate logging a command execution
            logger.log_command("echo 'hello'", "hello", "")
            logger.close()

            with open(log_file_path, 'r') as f:
                content = f.read()
                
                # Check for timestamp format
                self.assertRegex(content, r'\[\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\]')
                
                # Check for EXECUTED tag
                self.assertIn("EXECUTED: echo 'hello'", content)
                
                # Check for OUTPUT tag (should be present since we provided output)
                self.assertIn("OUTPUT: hello", content)
                
                # Should not contain ERROR section since no error was provided
                self.assertNotIn("ERROR:", content.split("OUTPUT: hello")[1] if "OUTPUT: hello" in content else "")
        finally:
            if os.path.exists(log_file_path):
                os.unlink(log_file_path)

    def test_command_execution_logs_with_error_to_file(self):
        """Test that command execution with errors is properly logged to file."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as log_file:
            log_file_path = log_file.name

        try:
            logger = Logger(log_file=log_file_path)
            
            # Simulate logging a command execution with error
            logger.log_command("failing_command", "", "Command not found")
            logger.close()

            with open(log_file_path, 'r') as f:
                content = f.read()
                
                # Check for EXECUTED tag
                self.assertIn("EXECUTED: failing_command", content)
                
                # Check for ERROR tag
                self.assertIn("ERROR: Command not found", content)
                
                # Should not contain OUTPUT section since no output was provided
                self.assertNotIn("OUTPUT:", content.split("ERROR: Command not found")[0] if "ERROR: Command not found" in content else "")
        finally:
            if os.path.exists(log_file_path):
                os.unlink(log_file_path)

    def test_command_execution_logs_with_both_output_and_error(self):
        """Test that command execution with both output and error is properly logged."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as log_file:
            log_file_path = log_file.name

        try:
            logger = Logger(log_file=log_file_path)
            
            # Simulate logging a command execution with both output and error
            logger.log_command("mixed_command", "partial output", "some error occurred")
            logger.close()

            with open(log_file_path, 'r') as f:
                content = f.read()
                
                # Check for all components
                self.assertIn("EXECUTED: mixed_command", content)
                self.assertIn("OUTPUT: partial output", content)
                self.assertIn("ERROR: some error occurred", content)
                
                # Verify proper ordering
                exec_idx = content.find("EXECUTED: mixed_command")
                output_idx = content.find("OUTPUT: partial output")
                error_idx = content.find("ERROR: some error occurred")
                
                self.assertLess(exec_idx, output_idx)
                self.assertLess(output_idx, error_idx)
        finally:
            if os.path.exists(log_file_path):
                os.unlink(log_file_path)

    def test_multiple_command_executions_logged_to_same_file(self):
        """Test that multiple command executions are all logged to the same file."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as log_file:
            log_file_path = log_file.name

        try:
            logger = Logger(log_file=log_file_path)
            
            # Log multiple commands
            logger.log_command("command1", "output1", "")
            logger.log_command("command2", "", "error2")
            logger.log_command("command3", "output3", "error3")
            logger.close()

            with open(log_file_path, 'r') as f:
                content = f.read()
                
                # Should contain all commands
                self.assertIn("EXECUTED: command1", content)
                self.assertIn("EXECUTED: command2", content)
                self.assertIn("EXECUTED: command3", content)
                
                # Should contain all outputs and errors appropriately
                self.assertIn("OUTPUT: output1", content)
                self.assertIn("ERROR: error2", content)
                self.assertIn("OUTPUT: output3", content)
                self.assertIn("ERROR: error3", content)
        finally:
            if os.path.exists(log_file_path):
                os.unlink(log_file_path)

    def test_logging_with_existing_file_appends_content(self):
        """Test that logging to an existing file appends to it."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as log_file:
            log_file_path = log_file.name
            log_file.write("Existing content\n")

        try:
            logger = Logger(log_file=log_file_path)
            logger.log_command("new_command", "new_output", "")
            logger.close()

            with open(log_file_path, 'r') as f:
                content = f.read()
                
                # Should contain both existing content and new log entry
                self.assertIn("Existing content", content)
                self.assertIn("EXECUTED: new_command", content)
                self.assertIn("OUTPUT: new_output", content)
        finally:
            if os.path.exists(log_file_path):
                os.unlink(log_file_path)

    def test_log_file_creation_in_new_directory(self):
        """Test that log file is created in a new directory if needed."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file_path = os.path.join(temp_dir, 'subdir', 'log.txt')
            
            logger = Logger(log_file=log_file_path)
            logger.log_command("test_command", "test_output", "")
            logger.close()
            
            # Verify the directory was created and file exists
            self.assertTrue(os.path.exists(log_file_path))
            
            with open(log_file_path, 'r') as f:
                content = f.read()
                self.assertIn("EXECUTED: test_command", content)

    @patch('subprocess.run')
    def test_command_execution_with_logging_in_executor(self, mock_subprocess):
        """Test that command execution in executor properly logs to file."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as log_file:
            log_file_path = log_file.name

        try:
            # Mock subprocess to simulate command execution
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = "Command executed successfully"
            mock_result.stderr = ""
            mock_subprocess.return_value = mock_result

            macro_def = ['echo "test command"']
            logger = Logger(log_file=log_file_path)
            
            execute_macro('test_macro', macro_def, logger)
            logger.close()

            with open(log_file_path, 'r') as f:
                content = f.read()
                
                # Should contain the executed command
                self.assertIn("EXECUTED: echo \"test command\"", content)
                
                # Should contain the output
                self.assertIn("OUTPUT: Command executed successfully", content)
                
                # Should contain macro execution info
                self.assertIn("Executing macro: test_macro", content)
        finally:
            if os.path.exists(log_file_path):
                os.unlink(log_file_path)

    @patch('subprocess.run')
    def test_command_execution_with_error_logging_in_executor(self, mock_subprocess):
        """Test that command execution with errors is properly logged in executor."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as log_file:
            log_file_path = log_file.name

        try:
            # Mock subprocess to simulate command failure
            mock_result = MagicMock()
            mock_result.returncode = 1
            mock_result.stdout = ""
            mock_result.stderr = "Command failed"
            mock_subprocess.return_value = mock_result

            macro_def = ['failing_command']
            logger = Logger(log_file=log_file_path)  # Continue to see logging
            
            try:
                execute_macro('failing_macro', macro_def, logger)
            except SystemExit:
                pass  # Expected due to command failure
            finally:
                logger.close()

            with open(log_file_path, 'r') as f:
                content = f.read()
                
                # Should contain the executed command
                self.assertIn("EXECUTED: failing_command", content)
                
                # Should contain the error
                self.assertIn("ERROR: Command failed", content)
                
                # Should contain error message about command failure
                self.assertIn("Command failed with return code 1", content)
        finally:
            if os.path.exists(log_file_path):
                os.unlink(log_file_path)

    def test_log_file_contains_proper_timestamps(self):
        """Test that log entries contain properly formatted timestamps."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as log_file:
            log_file_path = log_file.name

        try:
            logger = Logger(log_file=log_file_path)
            
            # Log a command
            logger.log_command("timestamp_test", "output", "")
            logger.close()

            with open(log_file_path, 'r') as f:
                content = f.read()
                
                # Should match timestamp format: [YYYY-MM-DD HH:MM:SS]
                import re
                timestamp_pattern = r'\[\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\]'
                matches = re.findall(timestamp_pattern, content)
                
                # Should have at least one timestamp
                self.assertGreater(len(matches), 0)
                
                # All timestamps should match the pattern
                for match in matches:
                    self.assertRegex(match, timestamp_pattern)
        finally:
            if os.path.exists(log_file_path):
                os.unlink(log_file_path)

    @patch('subprocess.run')
    def test_macro_execution_with_logging_and_env_vars(self, mock_subprocess):
        """Test that macro execution with environment variables is properly logged."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as log_file:
            log_file_path = log_file.name

        try:
            # Mock subprocess
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = "Environment variable value: test_value"
            mock_result.stderr = ""
            mock_subprocess.return_value = mock_result

            macro_def = {
                'commands': ['echo "Environment variable value: $TEST_VAR"'],
                'env': {'TEST_VAR': 'test_value'}
            }
            logger = Logger(log_file=log_file_path)
            
            execute_macro('env_macro', macro_def, logger)
            logger.close()

            with open(log_file_path, 'r') as f:
                content = f.read()
                
                # Should contain macro execution info
                self.assertIn("Executing macro: env_macro", content)
                
                # Should contain command execution
                self.assertIn("EXECUTED: echo \"Environment variable value: $TEST_VAR\"", content)
                
                # Should contain command output
                self.assertIn("Environment variable value: test_value", content)
        finally:
            if os.path.exists(log_file_path):
                os.unlink(log_file_path)

    def test_log_file_header_with_timestamp(self):
        """Test that log file contains a header with timestamp when opened."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as log_file:
            log_file_path = log_file.name

        try:
            logger = Logger(log_file=log_file_path)
            logger.close()

            with open(log_file_path, 'r') as f:
                content = f.read()
                
                # Should contain logging started header
                self.assertIn("--- Logging started at", content)
                
                # Should contain properly formatted timestamp
                import re
                timestamp_pattern = r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}'
                self.assertRegex(content, timestamp_pattern)
        finally:
            if os.path.exists(log_file_path):
                os.unlink(log_file_path)

    @patch('subprocess.run')
    def test_chained_macro_execution_logging(self, mock_subprocess):
        """Test that chained macro execution is properly logged to file."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as log_file:
            log_file_path = log_file.name

        try:
            # Mock subprocess
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = "Success"
            mock_result.stderr = ""
            mock_subprocess.return_value = mock_result

            # Mock the called macro
            with patch('repeat_runner.executor.load_macros') as mock_load:
                mock_load.return_value = {
                    'inner_macro': {
                        'commands': ['echo "inner command"']
                    }
                }
                
                macro_def = {
                    'commands': [
                        'echo "outer command"',
                        {'call': 'inner_macro'}
                    ]
                }
                
                logger = Logger(log_file=log_file_path)
                execute_macro('outer_macro', macro_def, logger)
                logger.close()

            with open(log_file_path, 'r') as f:
                content = f.read()
                
                # Should contain outer macro execution
                self.assertIn("Executing macro: outer_macro", content)
                
                # Should contain inner macro execution
                self.assertIn("Executing macro: inner_macro", content)
                
                # Should contain both command executions
                self.assertIn("EXECUTED: echo \"outer command\"", content)
                self.assertIn("EXECUTED: echo \"inner command\"", content)
        finally:
            if os.path.exists(log_file_path):
                os.unlink(log_file_path)


if __name__ == '__main__':
    unittest.main()