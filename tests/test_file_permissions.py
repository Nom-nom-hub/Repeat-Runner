import unittest
import tempfile
import os
import stat
from io import StringIO
from unittest.mock import patch, MagicMock, mock_open
from repeat_runner.executor import execute_macro
from repeat_runner.logger import Logger


class TestFilePermissionIssues(unittest.TestCase):

    def setUp(self):
        """Set up test fixtures before each test method."""
        self.logger = Logger(dry_run=True)

    @patch('builtins.open', side_effect=PermissionError("Permission denied"))
    def test_logger_creation_with_no_write_permission(self, mock_open):
        """Test logger creation when log file has no write permission."""
        # This should not raise an exception, but should handle the error gracefully
        logger = Logger(log_file="/nonexistent/path/log.txt")
        
        # The file handle should be None when permission is denied
        self.assertIsNone(logger.file_handle)
        
        # The log file path should still be set
        self.assertEqual(logger.log_file, "/nonexistent/path/log.txt")

    @patch('os.makedirs', side_effect=PermissionError("Permission denied"))
    def test_logger_creation_with_no_directory_permission(self, mock_makedirs):
        """Test logger creation when directory creation has no permission."""
        logger = Logger(log_file="/root-protected/test/log.txt")
        
        # The file handle should be None when permission is denied
        self.assertIsNone(logger.file_handle)

    def test_logger_with_readonly_directory(self):
        """Test logger behavior with read-only directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Make directory read-only (remove write permissions)
            os.chmod(temp_dir, stat.S_IREAD | stat.S_IEXEC)
            
            try:
                log_file_path = os.path.join(temp_dir, "test.log")
                logger = Logger(log_file=log_file_path)
                
                # The file handle should be None when permission is denied
                self.assertIsNone(logger.file_handle)
            finally:
                # Restore permissions to allow cleanup
                os.chmod(temp_dir, stat.S_IREAD | stat.S_IWRITE | stat.S_IEXEC)

    @patch('builtins.open', side_effect=IsADirectoryError("Is a directory"))
    def test_logger_creation_with_directory_instead_of_file(self, mock_open):
        """Test logger creation when trying to open a directory as a file."""
        logger = Logger(log_file="/some/directory/")
        
        # The file handle should be None when trying to open a directory
        self.assertIsNone(logger.file_handle)

    @patch('builtins.open', side_effect=FileNotFoundError("No such file or directory"))
    def test_logger_creation_with_nonexistent_directory(self, mock_open):
        """Test logger creation when the directory doesn't exist."""
        logger = Logger(log_file="/nonexistent/directory/log.txt")
        
        # The file handle should be None when directory doesn't exist
        self.assertIsNone(logger.file_handle)

    @patch('os.makedirs', side_effect=OSError("Too many levels of symbolic links"))
    def test_logger_creation_with_circular_symlinks(self, mock_makedirs):
        """Test logger creation when there are circular symbolic links."""
        logger = Logger(log_file="/circular/symlink/path/log.txt")
        
        # The file handle should be None when there are circular symlinks
        self.assertIsNone(logger.file_handle)

    def test_write_to_closed_file_handle(self):
        """Test writing to logger after file handle has been closed."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as tmp_file:
            log_file_path = tmp_file.name

        try:
            logger = Logger(log_file=log_file_path)
            logger.close()  # Close the file handle
            
            # Try to write after closing - should handle gracefully
            logger.info("This should not cause an error")
            logger.log_command("test_command", "output", "error")
        finally:
            if os.path.exists(log_file_path):
                os.unlink(log_file_path)

    def test_write_to_readonly_file(self):
        """Test writing to a read-only log file."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as tmp_file:
            log_file_path = tmp_file.name

        try:
            # Make the file read-only
            os.chmod(log_file_path, stat.S_IREAD)
            
            logger = Logger(log_file=log_file_path)
            
            # The file handle should be None due to permission error
            self.assertIsNone(logger.file_handle)
            
            # Try to write - should not crash
            logger.info("Test message")
            logger.log_command("test_command", "output", "")
        finally:
            # Restore permissions to allow cleanup
            os.chmod(log_file_path, stat.S_IREAD | stat.S_IWRITE)
            if os.path.exists(log_file_path):
                os.unlink(log_file_path)

    @patch('builtins.open')
    def test_file_write_permission_error_handling(self, mock_open):
        """Test that file write permission errors are handled gracefully."""
        # Mock open to succeed but file write to fail with permission error
        mock_file_handle = MagicMock()
        mock_file_handle.write.side_effect = PermissionError("Permission denied")
        mock_file_handle.flush.side_effect = PermissionError("Permission denied")
        mock_open.return_value = mock_file_handle
        
        with patch('sys.stderr', new_callable=StringIO) as mock_stderr:
            logger = Logger(log_file="test.log")
            
            # Try to write - should handle the error gracefully
            logger.info("Test message")
            
            # Verify error was logged to stderr
            error_output = mock_stderr.getvalue()
            self.assertIn("Could not write to log file", error_output)

    @patch('builtins.open')
    def test_file_flush_permission_error_handling(self, mock_open):
        """Test that file flush permission errors are handled gracefully."""
        # Mock open to succeed but flush to fail with permission error
        mock_file_handle = MagicMock()
        mock_file_handle.flush.side_effect = PermissionError("Permission denied")
        mock_open.return_value = mock_file_handle
        
        with patch('sys.stderr', new_callable=StringIO) as mock_stderr:
            logger = Logger(log_file="test.log")
            
            # Try to write - should handle the flush error gracefully
            logger.info("Test message")
            
            # Verify error was logged to stderr
            error_output = mock_stderr.getvalue()
            self.assertIn("Could not write to log file", error_output)

    @patch('os.makedirs', side_effect=PermissionError("Permission denied"))
    def test_executor_with_log_file_permission_error(self, mock_makedirs):
        """Test executor behavior when log file has permission issues."""
        macro_def = ['echo "test"']
        
        with patch('subprocess.run') as mock_subprocess:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = "test"
            mock_result.stderr = ""
            mock_subprocess.return_value = mock_result

            # Create logger with problematic log file
            logger = Logger(log_file="/protected/path/log.txt", dry_run=True)
            
            # Should execute without crashing despite log file issues
            execute_macro('test_macro', macro_def, logger)

    @patch('builtins.open', side_effect=PermissionError("Permission denied"))
    def test_logger_info_with_file_permission_error(self, mock_open):
        """Test that Logger.info handles file permission errors gracefully."""
        with patch('sys.stderr', new_callable=StringIO) as mock_stderr:
            logger = Logger(log_file="no_permission.log")
            
            # Should not crash when trying to write to file with no permission
            logger.info("Test info message")
            logger.error("Test error message")
            logger.warn("Test warning message")
            logger.log_command("test_cmd", "output", "error")
            
            # Verify permission errors were logged to stderr
            error_output = mock_stderr.getvalue()
            self.assertIn("Could not open log file", error_output)

    def test_logger_close_on_permission_error_file(self):
        """Test that Logger.close handles files with permission errors."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as tmp_file:
            log_file_path = tmp_file.name

        try:
            # Make the file read-only
            os.chmod(log_file_path, stat.S_IREAD)
            
            logger = Logger(log_file=log_file_path)
            
            # The file handle should be None due to permission error
            # But close should still work without crashing
            logger.close()  # Should not raise an exception
            
        finally:
            # Restore permissions to allow cleanup
            os.chmod(log_file_path, stat.S_IREAD | stat.S_IWRITE)
            if os.path.exists(log_file_path):
                os.unlink(log_file_path)

    @patch('builtins.open', side_effect=[PermissionError("Permission denied"), None])
    def test_logger_retry_behavior(self, mock_open):
        """Test logger behavior when first open fails but later operations might succeed."""
        # This tests the scenario where file creation fails but the logger continues to work
        logger = Logger(log_file="problematic.log")
        
        # Should continue to work for console output even if file logging fails
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            logger.info("Test message")
            output = mock_stdout.getvalue()
            # Should still output to console
            self.assertIn("[INFO] Test message", output)

    def test_logger_with_full_disk_simulation(self):
        """Test logger behavior when disk is full (simulated with exception)."""
        with patch('builtins.open') as mock_open:
            mock_file_handle = MagicMock()
            mock_file_handle.write.side_effect = OSError(28, "No space left on device")
            mock_file_handle.flush.side_effect = OSError(28, "No space left on device")
            mock_open.return_value = mock_file_handle
            
            with patch('sys.stderr', new_callable=StringIO) as mock_stderr:
                logger = Logger(log_file="full_disk.log")
                
                # Should handle disk full error gracefully
                logger.info("Test message")
                logger.log_command("cmd", "output", "")
                
                # Verify error was logged to stderr
                error_output = mock_stderr.getvalue()
                self.assertIn("Could not write to log file", error_output)

    @patch('os.makedirs', side_effect=OSError("Read-only file system"))
    def test_logger_on_readonly_filesystem(self, mock_makedirs):
        """Test logger behavior on a read-only filesystem."""
        logger = Logger(log_file="/readonly/system/log.txt")
        
        # The file handle should be None due to filesystem being read-only
        self.assertIsNone(logger.file_handle)
        
        # But console logging should still work
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            logger.info("Test message")
            output = mock_stdout.getvalue()
            self.assertIn("[INFO] Test message", output)


if __name__ == '__main__':
    unittest.main()