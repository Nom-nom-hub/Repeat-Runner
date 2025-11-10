import unittest
import tempfile
import os
from io import StringIO
from unittest.mock import patch, mock_open
from repeat_runner.logger import Logger


class TestLogger(unittest.TestCase):

    def test_logger_init_without_log_file(self):
        """Test logger initialization without log file."""
        logger = Logger()
        self.assertFalse(logger.dry_run)
        self.assertFalse(logger.verbose)
        self.assertIsNone(logger.log_file)
        self.assertIsNone(logger.file_handle)

    def test_logger_init_with_dry_run(self):
        """Test logger initialization with dry_run flag."""
        logger = Logger(dry_run=True)
        self.assertTrue(logger.dry_run)
        self.assertFalse(logger.verbose)

    def test_logger_init_with_verbose(self):
        """Test logger initialization with verbose flag."""
        logger = Logger(verbose=True)
        self.assertFalse(logger.dry_run)
        self.assertTrue(logger.verbose)

    def test_logger_init_with_log_file(self):
        """Test logger initialization with log file."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            log_file_path = tmp_file.name

        try:
            logger = Logger(log_file=log_file_path)
            self.assertEqual(logger.log_file, log_file_path)
            self.assertIsNotNone(logger.file_handle)
        finally:
            # Clean up
            if os.path.exists(log_file_path):
                os.unlink(log_file_path)

    def test_logger_init_with_log_file_directory_creation(self):
        """Test logger initialization creates directories if they don't exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file_path = os.path.join(temp_dir, 'subdir', 'log.txt')
            
            logger = Logger(log_file=log_file_path)
            self.assertEqual(logger.log_file, log_file_path)
            self.assertIsNotNone(logger.file_handle)
            
            # Verify directory was created
            self.assertTrue(os.path.exists(os.path.dirname(log_file_path)))

    @patch('sys.stdout', new_callable=StringIO)
    def test_info_message_console_output(self, mock_stdout):
        """Test that info messages are printed to console."""
        logger = Logger()
        logger.info("Test info message")
        
        output = mock_stdout.getvalue()
        self.assertIn("[INFO] Test info message", output)

    @patch('sys.stdout', new_callable=StringIO)
    def test_warn_message_console_output(self, mock_stdout):
        """Test that warn messages are printed to console."""
        logger = Logger()
        logger.warn("Test warning message")
        
        output = mock_stdout.getvalue()
        self.assertIn("[WARNING] Test warning message", output)

    @patch('sys.stderr', new_callable=StringIO)
    def test_error_message_console_output(self, mock_stderr):
        """Test that error messages are printed to stderr."""
        logger = Logger()
        logger.error("Test error message")
        
        output = mock_stderr.getvalue()
        self.assertIn("[ERROR] Test error message", output)

    def test_info_message_file_logging(self):
        """Test that info messages are logged to file."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as tmp_file:
            log_file_path = tmp_file.name

        try:
            logger = Logger(log_file=log_file_path)
            logger.info("Test info message")
            logger.close()

            with open(log_file_path, 'r') as f:
                content = f.read()
                self.assertIn("[INFO] Test info message", content)
        finally:
            # Clean up
            if os.path.exists(log_file_path):
                os.unlink(log_file_path)

    def test_warn_message_file_logging(self):
        """Test that warn messages are logged to file."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as tmp_file:
            log_file_path = tmp_file.name

        try:
            logger = Logger(log_file=log_file_path)
            logger.warn("Test warning message")
            logger.close()

            with open(log_file_path, 'r') as f:
                content = f.read()
                self.assertIn("[WARNING] Test warning message", content)
        finally:
            # Clean up
            if os.path.exists(log_file_path):
                os.unlink(log_file_path)

    def test_error_message_file_logging(self):
        """Test that error messages are logged to file."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as tmp_file:
            log_file_path = tmp_file.name

        try:
            logger = Logger(log_file=log_file_path)
            logger.error("Test error message")
            logger.close()

            with open(log_file_path, 'r') as f:
                content = f.read()
                self.assertIn("[ERROR] Test error message", content)
        finally:
            # Clean up
            if os.path.exists(log_file_path):
                os.unlink(log_file_path)

    def test_log_command_with_output_and_error(self):
        """Test logging command execution with output and error."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as tmp_file:
            log_file_path = tmp_file.name

        try:
            logger = Logger(log_file=log_file_path, verbose=True)
            logger.log_command("echo 'hello'", "hello", "error occurred")
            logger.close()

            with open(log_file_path, 'r') as f:
                content = f.read()
                self.assertIn("EXECUTED: echo 'hello'", content)
                self.assertIn("OUTPUT: hello", content)
                self.assertIn("ERROR: error occurred", content)
        finally:
            # Clean up
            if os.path.exists(log_file_path):
                os.unlink(log_file_path)

    def test_log_command_with_only_output(self):
        """Test logging command execution with only output."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as tmp_file:
            log_file_path = tmp_file.name

        try:
            logger = Logger(log_file=log_file_path)
            logger.log_command("echo 'hello'", "hello", "")
            logger.close()

            with open(log_file_path, 'r') as f:
                content = f.read()
                self.assertIn("EXECUTED: echo 'hello'", content)
                self.assertIn("OUTPUT: hello", content)
                # Should not contain error section
                self.assertNotIn("ERROR:", content.split("OUTPUT: hello")[1])
        finally:
            # Clean up
            if os.path.exists(log_file_path):
                os.unlink(log_file_path)

    def test_log_command_with_only_error(self):
        """Test logging command execution with only error."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as tmp_file:
            log_file_path = tmp_file.name

        try:
            logger = Logger(log_file=log_file_path)
            logger.log_command("echo 'hello'", "", "error occurred")
            logger.close()

            with open(log_file_path, 'r') as f:
                content = f.read()
                self.assertIn("EXECUTED: echo 'hello'", content)
                self.assertIn("ERROR: error occurred", content)
                # Should not contain output section
                self.assertNotIn("OUTPUT:", content.split("ERROR: error occurred")[0])
        finally:
            # Clean up
            if os.path.exists(log_file_path):
                os.unlink(log_file_path)

    def test_log_command_with_verbose_console_output(self):
        """Test that verbose mode prints command details to console."""
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            logger = Logger(verbose=True)
            logger.log_command("echo 'hello'", "hello", "error occurred")
            
            output = mock_stdout.getvalue()
            self.assertIn("[COMMAND] echo 'hello'", output)
            self.assertIn("[OUTPUT] hello", output)
            self.assertIn("[ERROR] error occurred", output)

    def test_file_handle_closed_properly(self):
        """Test that file handle is properly closed."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as tmp_file:
            log_file_path = tmp_file.name

        try:
            logger = Logger(log_file=log_file_path)
            # Verify file handle is open
            self.assertIsNotNone(logger.file_handle)
            self.assertFalse(logger.file_handle.closed)
            
            logger.close()
            # After closing, file_handle is set to None in the close method
            self.assertIsNone(logger.file_handle)
        finally:
            # Clean up
            if os.path.exists(log_file_path):
                os.unlink(log_file_path)

    def test_file_handle_closed_idempotently(self):
        """Test that close() can be called multiple times without error."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as tmp_file:
            log_file_path = tmp_file.name

        try:
            logger = Logger(log_file=log_file_path)
            logger.close()
            # Should not raise an exception
            logger.close()
        finally:
            # Clean up
            if os.path.exists(log_file_path):
                os.unlink(log_file_path)

    @patch('os.makedirs')
    @patch('builtins.open', side_effect=PermissionError("Permission denied"))
    def test_file_permission_error(self, mock_open, mock_makedirs):
        """Test handling of file permission errors."""
        # This should not raise an exception, but should log to stderr
        with patch('sys.stderr', new_callable=StringIO) as mock_stderr:
            logger = Logger(log_file="test.log")  # Use a simple filename to avoid path issues
            # Verify that the file handle is None when permission is denied
            self.assertIsNone(logger.file_handle)

    def test_write_to_file_with_exception(self):
        """Test handling of exceptions when writing to file."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as tmp_file:
            log_file_path = tmp_file.name

        try:
            logger = Logger(log_file=log_file_path)
            # Close the file handle to simulate an error condition
            logger.file_handle.close()
            
            # This should handle the exception gracefully
            logger._write_to_file("test message")
        finally:
            # Clean up
            if os.path.exists(log_file_path):
                os.unlink(log_file_path)

    def test_dry_run_info_message(self):
        """Test that dry run doesn't affect info messages."""
        with patch('sys.stdout', new_callable=StringIO):
            logger = Logger(dry_run=True)
            logger.info("Test info message")
            # Should still output to console even in dry run mode

    def test_log_command_timestamp_format(self):
        """Test that log command includes proper timestamp format."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as tmp_file:
            log_file_path = tmp_file.name

        try:
            logger = Logger(log_file=log_file_path)
            logger.log_command("echo 'test'", "output", "")
            logger.close()

            with open(log_file_path, 'r') as f:
                content = f.read()
                # Should contain timestamp in the format [YYYY-MM-DD HH:MM:SS]
                self.assertRegex(content, r'\[\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\]')
        finally:
            # Clean up
            if os.path.exists(log_file_path):
                os.unlink(log_file_path)


if __name__ == '__main__':
    unittest.main()