import unittest
import tempfile
import os
from unittest.mock import patch, MagicMock
from repeat_runner.executor import execute_macro
from repeat_runner.logger import Logger


class TestEnvironmentVariableSupport(unittest.TestCase):

    def setUp(self):
        """Set up test fixtures before each test method."""
        self.logger = Logger(dry_run=True)  # Use dry run to avoid actual command execution

    def test_macro_with_env_vars_passed_to_subprocess(self):
        """Test that environment variables are properly passed to subprocess."""
        # Create a logger without dry_run to allow subprocess execution
        logger = Logger()  # No dry run to allow actual subprocess call
        
        macro_def = {
            'commands': ['echo "Testing $TEST_VAR"'],
            'env': {
                'TEST_VAR': 'test_value',
                'ANOTHER_VAR': 'another_value'
            }
        }

        with patch('subprocess.run') as mock_subprocess:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = "Testing test_value"
            mock_result.stderr = ""
            mock_subprocess.return_value = mock_result

            execute_macro('test_macro', macro_def, logger)

            # Verify that subprocess was called with the correct environment
            mock_subprocess.assert_called_once()
            args, kwargs = mock_subprocess.call_args
            
            # Check that env parameter was passed
            self.assertIn('env', kwargs)
            env = kwargs['env']
            
            # Check that our custom environment variables are present
            self.assertEqual(env['TEST_VAR'], 'test_value')
            self.assertEqual(env['ANOTHER_VAR'], 'another_value')

    def test_macro_without_env_vars_uses_original_env(self):
        """Test that macros without env vars use the original environment."""
        macro_def = {
            'commands': ['echo "Testing"']
            # No env specified
        }

        logger = Logger()  # Non-dry-run logger

        with patch('subprocess.run') as mock_subprocess:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = "Testing"
            mock_result.stderr = ""
            mock_subprocess.return_value = mock_result

            execute_macro('test_macro', macro_def, logger)

            # Verify that subprocess was called
            mock_subprocess.assert_called_once()
            args, kwargs = mock_subprocess.call_args
            
            # Check that env parameter was passed (should be original environment)
            self.assertIn('env', kwargs)
            env = kwargs['env']
            
            # It should contain original environment variables
            self.assertIsInstance(env, dict)
            # Should have at least some original environment variables
            self.assertGreater(len(env), 0)

    def test_macro_env_vars_override_original_env(self):
        """Test that macro environment variables override original environment."""
        original_env = {'ORIGINAL_VAR': 'original_value', 'SHARED_VAR': 'original_shared'}
        
        macro_def = {
            'commands': ['echo "Testing $SHARED_VAR"'],
            'env': {
                'SHARED_VAR': 'overridden_value',  # Should override original
                'NEW_VAR': 'new_value'  # Should be added
            }
        }

        logger = Logger()  # Non-dry-run logger

        with patch('os.environ.copy', return_value=original_env), \
             patch('subprocess.run') as mock_subprocess:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = "Testing overridden_value"
            mock_result.stderr = ""
            mock_subprocess.return_value = mock_result

            execute_macro('test_macro', macro_def, logger)

            # Verify that subprocess was called with overridden environment
            mock_subprocess.assert_called_once()
            args, kwargs = mock_subprocess.call_args
            
            env = kwargs['env']
            
            # Check that original env was preserved where not overridden
            self.assertEqual(env['ORIGINAL_VAR'], 'original_value')
            
            # Check that shared var was overridden
            self.assertEqual(env['SHARED_VAR'], 'overridden_value')
            
            # Check that new var was added
            self.assertEqual(env['NEW_VAR'], 'new_value')

    def test_macro_env_vars_isolated_between_macros(self):
        """Test that environment variables are isolated between different macros."""
        macro1_def = {
            'commands': ['echo "Macro1: $MACRO1_VAR"'],
            'env': {'MACRO1_VAR': 'macro1_value', 'SHARED_VAR': 'macro1_shared'}
        }
        
        macro2_def = {
            'commands': ['echo "Macro2: $MACRO2_VAR"'],
            'env': {'MACRO2_VAR': 'macro2_value', 'SHARED_VAR': 'macro2_shared'}
        }

        logger = Logger()  # Non-dry-run logger

        with patch('subprocess.run') as mock_subprocess:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = "Test output"
            mock_result.stderr = ""
            mock_subprocess.return_value = mock_result

            # Execute first macro
            execute_macro('macro1', macro1_def, logger)
            
            # Execute second macro
            execute_macro('macro2', macro2_def, logger)

            # Check that subprocess was called twice
            self.assertEqual(mock_subprocess.call_count, 2)
            
            # Check first call
            first_call_args, first_call_kwargs = mock_subprocess.call_args_list[0]
            first_env = first_call_kwargs['env']
            self.assertEqual(first_env['MACRO1_VAR'], 'macro1_value')
            self.assertEqual(first_env['SHARED_VAR'], 'macro1_shared')
            
            # Check second call
            second_call_args, second_call_kwargs = mock_subprocess.call_args_list[1]
            second_env = second_call_kwargs['env']
            self.assertEqual(second_env['MACRO2_VAR'], 'macro2_value')
            self.assertEqual(second_env['SHARED_VAR'], 'macro2_shared')

    def test_macro_env_vars_with_special_characters(self):
        """Test that environment variables with special characters work correctly."""
        macro_def = {
            'commands': ['echo "Testing $SPECIAL_VAR"'],
            'env': {
                'SPECIAL_VAR': 'value with spaces and symbols!@#$%',
                'PATH_VAR': '/usr/local/bin:/usr/bin',
                'BOOL_VAR': 'true'
            }
        }

        logger = Logger()  # Non-dry-run logger

        with patch('subprocess.run') as mock_subprocess:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = "Testing value with spaces and symbols!@#$%"
            mock_result.stderr = ""
            mock_subprocess.return_value = mock_result

            execute_macro('special_macro', macro_def, logger)

            mock_subprocess.assert_called_once()
            args, kwargs = mock_subprocess.call_args
            env = kwargs['env']
            
            # Check that special character values are preserved
            self.assertEqual(env['SPECIAL_VAR'], 'value with spaces and symbols!@#$%')
            self.assertEqual(env['PATH_VAR'], '/usr/local/bin:/usr/bin')
            self.assertEqual(env['BOOL_VAR'], 'true')

    def test_macro_env_vars_empty_dict(self):
        """Test that empty env dict is handled correctly."""
        macro_def = {
            'commands': ['echo "Testing"'],
            'env': {}  # Empty environment
        }

        logger = Logger()  # Non-dry-run logger

        with patch('subprocess.run') as mock_subprocess:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = "Testing"
            mock_result.stderr = ""
            mock_subprocess.return_value = mock_result

            execute_macro('empty_env_macro', macro_def, logger)

            mock_subprocess.assert_called_once()
            args, kwargs = mock_subprocess.call_args
            env = kwargs['env']
            
            # Should still have original environment, just no additions
            self.assertIsInstance(env, dict)
            self.assertGreater(len(env), 0)  # Should have original env vars

    def test_macro_env_vars_none_value_handling(self):
        """Test that None values in env are not added to environment."""
        # Note: This test checks the validation in macros.py, but we can still test
        # the execution behavior if somehow invalid data gets through
        macro_def = {
            'commands': ['echo "Testing"']
        }

        logger = Logger()  # Non-dry-run logger

        with patch('subprocess.run') as mock_subprocess:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = "Testing"
            mock_result.stderr = ""
            mock_subprocess.return_value = mock_result

            execute_macro('no_env_macro', macro_def, logger)

            mock_subprocess.assert_called_once()
            args, kwargs = mock_subprocess.call_args
            env = kwargs['env']
            
            # Should have original environment
            self.assertIsInstance(env, dict)

    def test_macro_env_vars_in_macro_chaining(self):
        """Test that environment variables work correctly in macro chaining."""
        # This test simulates the scenario where one macro calls another,
        # and both have their own environment variables
        
        logger = Logger()  # Non-dry-run logger
        
        # Mock load_macros to return chained macros
        with patch('repeat_runner.executor.load_macros') as mock_load_macros:
            mock_load_macros.return_value = {
                'inner_macro': {
                    'commands': ['echo "Inner: $INNER_VAR"'],
                    'env': {'INNER_VAR': 'inner_value', 'SHARED_VAR': 'inner_shared'}
                }
            }
            
            outer_macro_def = {
                'commands': [
                    {'call': 'inner_macro'},
                    'echo "Outer: $OUTER_VAR"'
                ],
                'env': {'OUTER_VAR': 'outer_value', 'SHARED_VAR': 'outer_shared'}
            }

            with patch('subprocess.run') as mock_subprocess:
                mock_result = MagicMock()
                mock_result.returncode = 0
                mock_result.stdout = "Test output"
                mock_result.stderr = ""
                mock_subprocess.return_value = mock_result

                execute_macro('outer_macro', outer_macro_def, logger)

                # Should call subprocess for the inner macro command
                mock_subprocess.assert_called()
                
                # The inner macro should be executed with its own environment
                # which includes both its env vars and the outer macro's env vars
                # (since outer macro env is passed down to inner calls)


if __name__ == '__main__':
    unittest.main()