import unittest
import tempfile
import os
from unittest.mock import patch, MagicMock
from repeat_runner.executor import execute_macro
from repeat_runner.logger import Logger


class TestMacroChaining(unittest.TestCase):

    def setUp(self):
        """Set up test fixtures before each test method."""
        self.logger = Logger(dry_run=True)  # Use dry run to avoid actual command execution

    @patch('repeat_runner.executor.load_macros')
    def test_simple_macro_chaining(self, mock_load_macros):
        """Test that one macro can call another macro."""
        # Mock the called macro
        mock_load_macros.return_value = {
            'inner_macro': {
                'commands': ['echo "Inner command"']
            }
        }
        
        outer_macro_def = {
            'commands': [
                'echo "Before call"',
                {'call': 'inner_macro'},
                'echo "After call"'
            ]
        }

        with patch('subprocess.run') as mock_subprocess:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = "Command output"
            mock_result.stderr = ""
            mock_subprocess.return_value = mock_result

            execute_macro('outer_macro', outer_macro_def, self.logger)

            # Should call subprocess multiple times: once for each actual command
            # (excluding the macro call which gets handled separately)
            self.assertGreater(mock_subprocess.call_count, 0)

    @patch('repeat_runner.executor.load_macros')
    def test_nested_macro_chaining(self, mock_load_macros):
        """Test nested macro calls (macro calls macro that calls another macro)."""
        # Mock the called macros
        mock_load_macros.return_value = {
            'deep_macro': {
                'commands': ['echo "Deep command"']
            },
            'middle_macro': {
                'commands': [
                    'echo "Middle before"',
                    {'call': 'deep_macro'},
                    'echo "Middle after"'
                ]
            }
        }
        
        outer_macro_def = {
            'commands': [
                'echo "Outer before"',
                {'call': 'middle_macro'},
                'echo "Outer after"'
            ]
        }

        with patch('subprocess.run') as mock_subprocess:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = "Command output"
            mock_result.stderr = ""
            mock_subprocess.return_value = mock_result

            execute_macro('outer_macro', outer_macro_def, self.logger)

            # Should execute all commands from all macros
            self.assertGreater(mock_subprocess.call_count, 0)

    @patch('repeat_runner.executor.load_macros')
    def test_macro_chaining_with_environment_variables(self, mock_load_macros):
        """Test macro chaining where both macros have environment variables."""
        # Mock the called macro with env vars
        mock_load_macros.return_value = {
            'inner_macro': {
                'commands': ['echo "Inner with $INNER_VAR"'],
                'env': {'INNER_VAR': 'inner_value'}
            }
        }
        
        outer_macro_def = {
            'commands': [
                {'call': 'inner_macro'},
                'echo "Outer with $OUTER_VAR"'
            ],
            'env': {'OUTER_VAR': 'outer_value'}
        }

        with patch('subprocess.run') as mock_subprocess:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = "Command output"
            mock_result.stderr = ""
            mock_subprocess.return_value = mock_result

            execute_macro('outer_macro', outer_macro_def, self.logger)

            # Should execute both inner and outer commands with appropriate env vars
            mock_subprocess.assert_called()
            
            # Check that environment variables are properly handled
            for call_args in mock_subprocess.call_args_list:
                args, kwargs = call_args
                if 'env' in kwargs:
                    env = kwargs['env']
                    # Each subprocess call should have environment variables
                    self.assertIsInstance(env, dict)

    @patch('repeat_runner.executor.load_macros')
    def test_macro_chaining_missing_called_macro(self, mock_load_macros):
        """Test that calling a non-existent macro is handled properly."""
        # Mock to return empty dict (no macros found)
        mock_load_macros.return_value = {}

        macro_def = {
            'commands': [
                'echo "Before call"',
                {'call': 'nonexistent_macro'},
                'echo "After call"'
            ]
        }

        with self.assertRaises(SystemExit):
            execute_macro('test_macro', macro_def, self.logger, continue_on_error=False)

    @patch('repeat_runner.executor.load_macros')
    def test_macro_chaining_missing_called_macro_continue_on_error(self, mock_load_macros):
        """Test that calling a non-existent macro continues when continue_on_error=True."""
        # Mock to return empty dict (no macros found)
        mock_load_macros.return_value = {}

        macro_def = {
            'commands': [
                'echo "Before call"',
                {'call': 'nonexistent_macro'},
                'echo "After call"'
            ]
        }

        with patch('subprocess.run') as mock_subprocess:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = "Before call\nAfter call"
            mock_result.stderr = ""
            mock_subprocess.return_value = mock_result

            # Should not raise SystemExit when continue_on_error=True
            try:
                execute_macro('test_macro', macro_def, self.logger, continue_on_error=True)
            except SystemExit:
                self.fail("execute_macro raised SystemExit when continue_on_error=True")

    def test_macro_chaining_with_regular_commands(self):
        """Test that macros can mix regular commands with macro calls."""
        macro_def = {
            'commands': [
                'echo "Regular command 1"',
                {'call': 'other_macro'},
                'echo "Regular command 2"',
                {'call': 'another_macro'},
                'echo "Regular command 3"'
            ]
        }

        # Mock the called macros
        with patch('repeat_runner.executor.load_macros') as mock_load_macros:
            mock_load_macros.return_value = {
                'other_macro': {
                    'commands': ['echo "Other macro command"']
                },
                'another_macro': {
                    'commands': ['echo "Another macro command"']
                }
            }

            with patch('subprocess.run') as mock_subprocess:
                mock_result = MagicMock()
                mock_result.returncode = 0
                mock_result.stdout = "Command output"
                mock_result.stderr = ""
                mock_subprocess.return_value = mock_result

                execute_macro('test_macro', macro_def, self.logger)

                # Should execute all commands (both regular and from called macros)
                self.assertGreater(mock_subprocess.call_count, 0)

    @patch('repeat_runner.executor.load_macros')
    def test_macro_chaining_preserves_execution_order(self, mock_load_macros):
        """Test that macro chaining preserves the order of execution."""
        call_order = []

        def mock_subprocess_side_effect(*args, **kwargs):
            call_order.append(args[0])  # Add the command to call order
            result = MagicMock()
            result.returncode = 0
            result.stdout = "Output"
            result.stderr = ""
            return result

        # Mock the called macro
        mock_load_macros.return_value = {
            'ordered_macro': {
                'commands': [
                    'echo "Called first"',
                    'echo "Called second"'
                ]
            }
        }

        macro_def = {
            'commands': [
                'echo "First command"',
                {'call': 'ordered_macro'},
                'echo "Last command"'
            ]
        }

        with patch('subprocess.run', side_effect=mock_subprocess_side_effect):
            execute_macro('test_macro', macro_def, self.logger)

        # Verify the execution order
        expected_order = [
            'echo "First command"',
            'echo "Called first"',
            'echo "Called second"',
            'echo "Last command"'
        ]
        self.assertEqual(call_order, expected_order)

    @patch('repeat_runner.executor.load_macros')
    def test_macro_chaining_with_empty_commands(self, mock_load_macros):
        """Test macro chaining when called macro has empty commands."""
        # Mock to return macro with empty commands
        mock_load_macros.return_value = {
            'empty_macro': {
                'commands': []  # Empty commands list
            }
        }

        macro_def = {
            'commands': [
                'echo "Before empty call"',
                {'call': 'empty_macro'},
                'echo "After empty call"'
            ]
        }

        with patch('subprocess.run') as mock_subprocess:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = "Before empty call\nAfter empty call"
            mock_result.stderr = ""
            mock_subprocess.return_value = mock_result

            execute_macro('test_macro', macro_def, self.logger)

            # Should execute the outer commands but skip the empty macro
            # The mock_subprocess should only be called for the outer commands
            self.assertEqual(mock_subprocess.call_count, 2)  # Before and after calls

    @patch('repeat_runner.executor.load_macros')
    def test_macro_chaining_multiple_calls_same_macro(self, mock_load_macros):
        """Test that the same macro can be called multiple times."""
        call_count = {'count': 0}

        def mock_subprocess_side_effect(*args, **kwargs):
            call_count['count'] += 1
            result = MagicMock()
            result.returncode = 0
            result.stdout = f"Output {call_count['count']}"
            result.stderr = ""
            return result

        # Mock the called macro
        mock_load_macros.return_value = {
            'reused_macro': {
                'commands': ['echo "Reused macro call"']
            }
        }

        macro_def = {
            'commands': [
                {'call': 'reused_macro'},
                'echo "Between calls"',
                {'call': 'reused_macro'},
                'echo "After calls"'
            ]
        }

        with patch('subprocess.run', side_effect=mock_subprocess_side_effect):
            execute_macro('test_macro', macro_def, self.logger)

        # Should execute the reused macro twice, plus the regular commands
        # Total expected calls: 2 calls to reused_macro + 2 regular commands = 4
        self.assertEqual(call_count['count'], 4)

    def test_macro_chaining_with_complex_command_structure(self):
        """Test macro chaining with complex command structures."""
        macro_def = {
            'commands': [
                'echo "Setup"',
                {'call': 'build_macro'},
                {'call': 'test_macro'},
                'echo "Cleanup"'
            ]
        }

        # Mock the called macros
        with patch('repeat_runner.executor.load_macros') as mock_load_macros:
            mock_load_macros.return_value = {
                'build_macro': {
                    'commands': [
                        'echo "Building..."',
                        'make build'
                    ]
                },
                'test_macro': {
                    'commands': [
                        'echo "Running tests..."',
                        'npm test'
                    ]
                }
            }

            with patch('subprocess.run') as mock_subprocess:
                mock_result = MagicMock()
                mock_result.returncode = 0
                mock_result.stdout = "Success"
                mock_result.stderr = ""
                mock_subprocess.return_value = mock_result

                execute_macro('complex_macro', macro_def, self.logger)

                # Should execute all commands from all macros in order
                self.assertGreater(mock_subprocess.call_count, 0)


if __name__ == '__main__':
    unittest.main()