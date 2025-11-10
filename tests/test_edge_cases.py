import unittest
import tempfile
import os
from io import StringIO
from unittest.mock import patch, MagicMock
from repeat_runner.executor import execute_macro
from repeat_runner.logger import Logger
from repeat_runner.macros import validate_macro_definition


class TestEdgeCases(unittest.TestCase):

    def setUp(self):
        """Set up test fixtures before each test method."""
        self.logger = Logger(dry_run=True)

    def test_env_var_with_special_characters(self):        """Test environment variables with special characters."""
        macro_def = {
            'commands': ['echo "Testing special chars: $SPECIAL_VAR"'],
            'env': {
                'SPECIAL_VAR': 'value with spaces!@#$%^&*()',
                'PATH_VAR': '/usr/local/bin:/usr/bin:/bin',
                'JSON_VAR': '{"key": "value", "nested": {"inner": "value"}}',
                'EMPTY_VAR': ''
            }
        }

        with patch('subprocess.run') as mock_subprocess:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = "Testing special chars: value with spaces!@#$%^&*()"
            mock_result.stderr = ""
            mock_subprocess.return_value = mock_result

            execute_macro('special_chars_macro', macro_def, logger)

            # Verify subprocess was called and environment was passed
            mock_subprocess.assert_called()
            args, kwargs = mock_subprocess.call_args
            env = kwargs['env']
            
            # Check that special character values are preserved
            self.assertEqual(env['SPECIAL_VAR'], 'value with spaces!@#$%^&*()')
            self.assertEqual(env['PATH_VAR'], '/usr/local/bin:/usr/bin:/bin')
            self.assertEqual(env['JSON_VAR'], '{"key": "value", "nested": {"inner": "value"}}')
            self.assertEqual(env['EMPTY_VAR'], '')

    def test_env_var_name_edge_cases(self):        """Test environment variable names with edge cases."""
        macro_def = {
            'commands': ['echo "Testing var names"'],
            'env': {
                'NORMAL_VAR': 'normal',
                '_UNDERSCORE_START': 'underscore_start',
                'VAR_WITH_123_NUMBERS': 'numbers',
                'VAR_WITH_DASH-CHARS': 'dashes',  # This might not be valid in all shells
                '': 'empty_key'  # Empty key should be caught by validation
            }
        }

        # This should fail validation due to empty key
        with patch('sys.stderr', new_callable=StringIO) as mock_stderr:
            with self.assertRaises(SystemExit):
                execute_macro('edge_case_names_macro', macro_def, logger)

    def test_env_var_non_string_values(self):        """Test environment variables with non-string values (should fail validation)."""
        # Test with integer value
        macro_def_int = {
            'commands': ['echo "test"'],
            'env': {'TEST_VAR': 123}
        }

        with patch('sys.stderr', new_callable=StringIO) as mock_stderr:
            with self.assertRaises(SystemExit):
                execute_macro('int_env_macro', macro_def_int, logger)
            
            error_output = mock_stderr.getvalue()
            self.assertIn("must be a string", error_output)

        # Test with float value
        macro_def_float = {
            'commands': ['echo "test"'],
            'env': {'TEST_VAR': 3.14}
        }

        with patch('sys.stderr', new_callable=StringIO) as mock_stderr:
            with self.assertRaises(SystemExit):
                execute_macro('float_env_macro', macro_def_float, logger)
            
            error_output = mock_stderr.getvalue()
            self.assertIn("must be a string", error_output)

        # Test with boolean value
        macro_def_bool = {
            'commands': ['echo "test"'],
            'env': {'TEST_VAR': True}
        }

        with patch('sys.stderr', new_callable=StringIO) as mock_stderr:
            with self.assertRaises(SystemExit):
                execute_macro('bool_env_macro', macro_def_bool, logger)
            
            error_output = mock_stderr.getvalue()
            self.assertIn("must be a string", error_output)

        # Test with list value
        macro_def_list = {
            'commands': ['echo "test"'],
            'env': {'TEST_VAR': ['value1', 'value2']}
        }

        with patch('sys.stderr', new_callable=StringIO) as mock_stderr:
            with self.assertRaises(SystemExit):
                execute_macro('list_env_macro', macro_def_list, logger)
            
            error_output = mock_stderr.getvalue()
            self.assertIn("must be a string", error_output)

        # Test with dict value
        macro_def_dict = {
            'commands': ['echo "test"'],
            'env': {'TEST_VAR': {'nested': 'value'}}
        }

        with patch('sys.stderr', new_callable=StringIO) as mock_stderr:
            with self.assertRaises(SystemExit):
                execute_macro('dict_env_macro', macro_def_dict, logger)
            
            error_output = mock_stderr.getvalue()
            self.assertIn("must be a string", error_output)

    def test_large_env_vars(self):        """Test very large environment variable values."""
        large_value = 'a' * 10000  # 10KB string
        macro_def = {
            'commands': ['echo "Testing large var"'],
            'env': {
                'LARGE_VAR': large_value,
                'NORMAL_VAR': 'normal'
            }
        }

        with patch('subprocess.run') as mock_subprocess:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = "Testing large var"
            mock_result.stderr = ""
            mock_subprocess.return_value = mock_result

            execute_macro('large_env_macro', macro_def, logger)

            # Verify subprocess was called and large value was preserved
            mock_subprocess.assert_called()
            args, kwargs = mock_subprocess.call_args
            env = kwargs['env']
            
            self.assertEqual(env['LARGE_VAR'], large_value)
            self.assertEqual(env['NORMAL_VAR'], 'normal')

    def test_many_env_vars(self):        """Test macro with many environment variables."""
        env_vars = {f'VAR_{i}': f'value_{i}' for i in range(100)}
        macro_def = {
            'commands': ['echo "Testing many vars"'],
            'env': env_vars
        }

        with patch('subprocess.run') as mock_subprocess:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = "Testing many vars"
            mock_result.stderr = ""
            mock_subprocess.return_value = mock_result

            execute_macro('many_env_macro', macro_def, logger)

            # Verify subprocess was called and all env vars were preserved
            mock_subprocess.assert_called()
            args, kwargs = mock_subprocess.call_args
            env = kwargs['env']
            
            for i in range(100):
                self.assertEqual(env[f'VAR_{i}'], f'value_{i}')

    def test_env_vars_override_os_environ(self):        """Test that macro env vars properly override system environment."""
        original_env = {
            'EXISTING_VAR': 'original_value',
            'SHARED_VAR': 'original_shared',
            'PATH': '/original/path'
        }
        
        macro_def = {
            'commands': ['echo "Testing override"'],
            'env': {
                'SHARED_VAR': 'overridden_value',  # Should override
                'NEW_VAR': 'new_value'  # Should be added
            }
        }

        with patch('os.environ.copy', return_value=original_env), \
             patch('subprocess.run') as mock_subprocess:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = "Testing override"
            mock_result.stderr = ""
            mock_subprocess.return_value = mock_result

            execute_macro('override_macro', macro_def, logger)

            # Verify subprocess was called with overridden environment
            mock_subprocess.assert_called()
            args, kwargs = mock_subprocess.call_args
            env = kwargs['env']
            
            # Check that original values are preserved where not overridden
            self.assertEqual(env['EXISTING_VAR'], 'original_value')
            self.assertEqual(env['PATH'], '/original/path')
            
            # Check that values are overridden where specified
            self.assertEqual(env['SHARED_VAR'], 'overridden_value')
            
            # Check that new values are added
            self.assertEqual(env['NEW_VAR'], 'new_value')

    def test_macro_with_no_env_and_no_commands(self):        """Test macro with no env and no commands (edge case)."""
        # This should fail validation since commands is required
        invalid_macro = {
            'env': {'TEST_VAR': 'value'}
            # Missing 'commands' key
        }

        with patch('sys.stderr', new_callable=StringIO) as mock_stderr:
            with self.assertRaises(SystemExit):
                execute_macro('no_commands_macro', invalid_macro, logger)
            
            error_output = mock_stderr.getvalue()
            self.assertIn("must have 'commands' key", error_output)

    def test_macro_with_empty_commands_list(self):        """Test macro with empty commands list."""
        macro_def = {
            'commands': [],  # Empty commands list
            'env': {'TEST_VAR': 'value'}
        }

        # This should execute without running any commands
        execute_macro('empty_commands_macro', macro_def, logger)

    def test_macro_with_empty_env_dict(self):        """Test macro with empty env dict."""
        macro_def = {
            'commands': ['echo "test"'],
            'env': {}  # Empty env dict
        }

        with patch('subprocess.run') as mock_subprocess:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = "test"
            mock_result.stderr = ""
            mock_subprocess.return_value = mock_result

            execute_macro('empty_env_macro', macro_def, logger)

            # Should execute normally with empty env (just inherits from os.environ)
            mock_subprocess.assert_called()

    def test_env_var_unicode_characters(self):        """Test environment variables with Unicode characters."""
        macro_def = {
            'commands': ['echo "Testing unicode: $UNICODE_VAR"'],
            'env': {
                'UNICODE_VAR': 'Hello 世界 🌍 Привет',
                'EMOJI_VAR': '🚀 🐍 📁',
                'ACCENT_VAR': 'café naïve résumé'
            }
        }

        with patch('subprocess.run') as mock_subprocess:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = "Testing unicode: Hello 世界 🌍 Привет"
            mock_result.stderr = ""
            mock_subprocess.return_value = mock_result

            execute_macro('unicode_macro', macro_def, logger)

            # Verify subprocess was called and Unicode values were preserved
            mock_subprocess.assert_called()
            args, kwargs = mock_subprocess.call_args
            env = kwargs['env']
            
            self.assertEqual(env['UNICODE_VAR'], 'Hello 世界 🌍 Привет')
            self.assertEqual(env['EMOJI_VAR'], '🚀 🐍 📁')
            self.assertEqual(env['ACCENT_VAR'], 'café naïve résumé')

    def test_env_var_shell_special_characters(self):        """Test environment variables with shell special characters."""
        macro_def = {
            'commands': ['echo "Testing shell chars: $SHELL_VAR"'],
            'env': {
                'SHELL_VAR': '$HOME && echo danger || echo safe',
                'GLOB_VAR': '*.txt ? [abc]',
                'REDIR_VAR': 'echo test > file.txt 2>&1'
            }
        }

        with patch('subprocess.run') as mock_subprocess:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = "Testing shell chars: $HOME && echo danger || echo safe"
            mock_result.stderr = ""
            mock_subprocess.return_value = mock_result

            execute_macro('shell_chars_macro', macro_def, logger)

            # Verify subprocess was called and shell special chars were preserved
            mock_subprocess.assert_called()
            args, kwargs = mock_subprocess.call_args
            env = kwargs['env']
            
            self.assertEqual(env['SHELL_VAR'], '$HOME && echo danger || echo safe')
            self.assertEqual(env['GLOB_VAR'], '*.txt ? [abc]')
            self.assertEqual(env['REDIR_VAR'], 'echo test > file.txt 2>&1')

    def test_env_var_with_quotes(self):        """Test environment variables with quote characters."""
        macro_def = {
            'commands': ['echo "Testing quotes: $QUOTE_VAR"'],
            'env': {
                'QUOTE_VAR': 'He said "Hello" and \'Goodbye\'',
                'SINGLE_QUOTE_VAR': "It's working",
                'ESCAPED_VAR': 'Path: "C:\\Program Files\\App" and \'file.txt\''
            }
        }

        with patch('subprocess.run') as mock_subprocess:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = "Testing quotes: He said \"Hello\" and 'Goodbye'"
            mock_result.stderr = ""
            mock_subprocess.return_value = mock_result

            execute_macro('quote_macro', macro_def, logger)

            # Verify subprocess was called and quote chars were preserved
            mock_subprocess.assert_called()
            args, kwargs = mock_subprocess.call_args
            env = kwargs['env']
            
            self.assertEqual(env['QUOTE_VAR'], 'He said "Hello" and \'Goodbye\'')
            self.assertEqual(env['SINGLE_QUOTE_VAR'], "It's working")
            self.assertEqual(env['ESCAPED_VAR'], 'Path: "C:\\Program Files\\App" and \'file.txt\'')

    def test_macro_chaining_with_env_var_conflicts(self):        """Test macro chaining where parent and child have conflicting env vars."""
        # Mock the called macro
        with patch('repeat_runner.executor.load_macros') as mock_load:
            mock_load.return_value = {
                'child_macro': {
                    'commands': ['echo "Child: $SHARED_VAR"'],
                    'env': {'SHARED_VAR': 'child_value', 'CHILD_VAR': 'child_only'}
                }
            }
            
            parent_macro_def = {
                'commands': [
                    {'call': 'child_macro'},
                    'echo "Parent: $SHARED_VAR"'
                ],
                'env': {'SHARED_VAR': 'parent_value', 'PARENT_VAR': 'parent_only'}
            }

            with patch('subprocess.run') as mock_subprocess:
                mock_result = MagicMock()
                mock_result.returncode = 0
                mock_result.stdout = "Child execution"
                mock_result.stderr = ""
                mock_subprocess.return_value = mock_result

                execute_macro('parent_macro', parent_macro_def, logger)

                # Should execute both parent and child commands
                mock_subprocess.assert_called()

    def test_env_var_with_null_bytes(self):        """Test environment variables with null bytes (should be handled properly by OS)."""
        # Note: This is an edge case that might cause issues in some contexts
        macro_def = {
            'commands': ['echo "Testing null bytes"'],
            'env': {
                'NULL_VAR': 'value\x00with\x00nulls'
            }
        }

        with patch('subprocess.run') as mock_subprocess:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = "Testing null bytes"
            mock_result.stderr = ""
            mock_subprocess.return_value = mock_result

            execute_macro('null_bytes_macro', macro_def, logger)

            # Verify subprocess was called
            mock_subprocess.assert_called()


if __name__ == '__main__':
    import sys
    from io import StringIO
    unittest.main()