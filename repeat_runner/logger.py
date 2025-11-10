"""
Module for handling logging and output formatting
"""
import sys
import os
from datetime import datetime


class Logger:
    """
    A logger class that handles output, dry-run mode, verbose output, and file logging
    """
    def __init__(self, dry_run=False, verbose=False, log_file=None):
        self.dry_run = dry_run
        self.verbose = verbose
        self.log_file = log_file
        self.file_handle = None
        
        # Open log file if specified
        if self.log_file:
            # Create directory if it doesn't exist
            log_dir = os.path.dirname(self.log_file)
            if log_dir:
                try:
                    os.makedirs(log_dir, exist_ok=True)
                except (OSError, PermissionError):
                    # If we can't create the directory, set file_handle to None
                    self.file_handle = None
                    print(f"[ERROR] Could not create log directory: {log_dir}", file=sys.stderr)
                    return
            
            try:
                self.file_handle = open(self.log_file, 'a', encoding='utf-8')
                # Write a header with timestamp
                self._write_to_file(f"\n--- Logging started at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ---\n")
            except (OSError, PermissionError) as e:
                # If we can't open the file, set file_handle to None
                self.file_handle = None
                print(f"[ERROR] Could not open log file: {e}", file=sys.stderr)
        else:
            self.file_handle = None

    def _write_to_file(self, message):
        """
        Write a message to the log file if file logging is enabled
        """
        if self.file_handle:
            try:
                self.file_handle.write(message + '\n')
                self.file_handle.flush()  # Ensure it's written immediately
            except Exception as e:
                print(f"[ERROR] Could not write to log file: {e}", file=sys.stderr)

    def info(self, message):
        """
        Log an informational message
        """
        formatted_message = f"[INFO] {message}"
        print(formatted_message)
        
        # Log to file if enabled
        if self.file_handle:
            self._write_to_file(formatted_message)

    def error(self, message):
        """
        Log an error message to stderr
        """
        formatted_message = f"[ERROR] {message}"
        print(formatted_message, file=sys.stderr)
        
        # Log to file if enabled
        if self.file_handle:
            self._write_to_file(formatted_message)

    def warn(self, message):
        """
        Log a warning message
        """
        formatted_message = f"[WARNING] {message}"
        print(formatted_message)
        
        # Log to file if enabled
        if self.file_handle:
            self._write_to_file(formatted_message)

    def log_command(self, command, output="", error=""):
        """
        Log command execution details
        """
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_entry = f"[{timestamp}] EXECUTED: {command}"
        if output:
            log_entry += f"\n[{timestamp}] OUTPUT: {output}"
        if error:
            log_entry += f"\n[{timestamp}] ERROR: {error}"
        
        # Log to console if verbose
        if self.verbose:
            print(f"[COMMAND] {command}")
            if output:
                print(f"[OUTPUT] {output}")
            if error:
                print(f"[ERROR] {error}")
        
        # Log to file if enabled
        if self.file_handle:
            self._write_to_file(log_entry)

    def close(self):
        """
        Close the log file if it was opened
        """
        if self.file_handle:
            self.file_handle.close()
            self.file_handle = None