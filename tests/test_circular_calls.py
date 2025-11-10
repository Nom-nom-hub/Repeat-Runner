import unittest
import tempfile
import os
from io import StringIO
from unittest.mock import patch, MagicMock
from repeat_runner.executor import execute_macro
from repeat_runner.logger import Logger


class TestCircularMacroCalls(unittest.TestCase):

    def setUp(self):
        """Set up test fixtures before each test method."""
        self.logger = Logger()  # Use normal logger to allow subprocess calls

    def test_direct_circular_macro_call_detection(self):
        """Test that direct circular macro calls are detected."""
        # Mock the called macro to call back to the original
        with patch('repeat_runner.executor.load_macros') as mock_load:
            mock_load.return_value = {
                'circular_macro': {
                    'commands': [
                        {'call': 'circular_macro'}  # Calls itself
                    ]
                }
            }
            
            macro_def = {
                'commands': [
                    {'call': 'circular_macro'}
                ]
            }

            with patch('sys.stderr', new_callable=StringIO) as mock_stderr:
                with self.assertRaises(SystemExit):
                    execute_macro('starting_macro', macro_def, self.logger)
                
                error_output = mock_stderr.getvalue()
                self.assertIn("Circular macro call detected", error_output)
                self.assertIn("circular_macro", error_output)

    def test_indirect_circular_macro_call_detection(self):
        """Test that indirect circular macro calls are detected."""
        # Create a circular chain: A -> B -> C -> A
        with patch('repeat_runner.executor.load_macros') as mock_load:
            mock_load.return_value = {
                'macro_a': {
                    'commands': [
                        {'call': 'macro_b'}
                    ]
                },
                'macro_b': {
                    'commands': [
                        {'call': 'macro_c'}
                    ]
                },
                'macro_c': {
                    'commands': [
                        {'call': 'macro_a'}  # Back to macro_a, creating circle
                    ]
                }
            }
            
            # Start with macro_a
            macro_def = {
                'commands': [
                    {'call': 'macro_a'}
                ]
            }

            with patch('sys.stderr', new_callable=StringIO) as mock_stderr:
                with self.assertRaises(SystemExit):
                    execute_macro('starting_macro', macro_def, self.logger)
                
                error_output = mock_stderr.getvalue()
                self.assertIn("Circular macro call detected", error_output)
                self.assertIn("macro_a", error_output)

    def test_circular_call_with_multiple_paths(self):
        """Test circular detection when there are multiple paths to the same macro."""
        # A -> B -> C -> A (circular)
        # A -> D -> C -> A (also circular)
        with patch('repeat_runner.executor.load_macros') as mock_load:
            mock_load.return_value = {
                'macro_a': {
                    'commands': [
                        {'call': 'macro_b'},
                        {'call': 'macro_d'}
                    ]
                },
                'macro_b': {
                    'commands': [
                        {'call': 'macro_c'}
                    ]
                },
                'macro_c': {
                    'commands': [
                        {'call': 'macro_a'}  # Back to macro_a
                    ]
                },
                'macro_d': {
                    'commands': [
                        {'call': 'macro_c'}  # Also leads to macro_c
                    ]
                }
            }
            
            macro_def = {
                'commands': [
                    {'call': 'macro_a'}
                ]
            }

            with patch('sys.stderr', new_callable=StringIO) as mock_stderr:
                with self.assertRaises(SystemExit):
                    execute_macro('starting_macro', macro_def, self.logger)
                
                error_output = mock_stderr.getvalue()
                self.assertIn("Circular macro call detected", error_output)

    def test_self_circular_macro(self):
        """Test a macro that directly calls itself."""
        with patch('repeat_runner.executor.load_macros') as mock_load:
            mock_load.return_value = {
                'self_calling_macro': {
                    'commands': [
                        {'call': 'self_calling_macro'}
                    ]
                }
            }
            
            macro_def = {
                'commands': [
                    {'call': 'self_calling_macro'}
                ]
            }

            with patch('sys.stderr', new_callable=StringIO) as mock_stderr:
                with self.assertRaises(SystemExit):
                    execute_macro('starting_macro', macro_def, self.logger)
                
                error_output = mock_stderr.getvalue()
                self.assertIn("Circular macro call detected", error_output)
                self.assertIn("self_calling_macro", error_output)

    def test_deep_circular_chain(self):
        """Test circular detection in a deep chain."""
        # A -> B -> C -> D -> E -> A (deep circle)
        with patch('repeat_runner.executor.load_macros') as mock_load:
            mock_load.return_value = {
                'macro_a': {
                    'commands': [{'call': 'macro_b'}]
                },
                'macro_b': {
                    'commands': [{'call': 'macro_c'}]
                },
                'macro_c': {
                    'commands': [{'call': 'macro_d'}]
                },
                'macro_d': {
                    'commands': [{'call': 'macro_e'}]
                },
                'macro_e': {
                    'commands': [{'call': 'macro_a'}]  # Back to start
                }
            }
            
            macro_def = {
                'commands': [
                    {'call': 'macro_a'}
                ]
            }

            with patch('sys.stderr', new_callable=StringIO) as mock_stderr:
                with self.assertRaises(SystemExit):
                    execute_macro('starting_macro', macro_def, self.logger)
                
                error_output = mock_stderr.getvalue()
                self.assertIn("Circular macro call detected", error_output)

    def test_non_circular_chain_passes(self):
        """Test that non-circular chains execute without error."""
        macros = {
            'macro_a': {
                'commands': [{'call': 'macro_b'}]
            },
            'macro_b': {
                'commands': [{'call': 'macro_c'}]
            },
            'macro_c': {
                'commands': ['echo "End of chain"']  # No further calls
            }
        }
        
        macro_def = {
            'commands': [
                {'call': 'macro_a'}
            ]
        }

        with patch('repeat_runner.executor.load_macros', return_value=macros), \
             patch('subprocess.run') as mock_subprocess:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = "End of chain"
            mock_result.stderr = ""
            mock_subprocess.return_value = mock_result

            # Should execute without circular error
            execute_macro('starting_macro', macro_def, self.logger)

            # Should execute the final command in the chain
            self.assertEqual(mock_subprocess.call_count, 1)  # Only the echo command from macro_c

    def test_circular_detection_with_environment_variables(self):
        """Test circular detection works even when macros have environment variables."""
        with patch('repeat_runner.executor.load_macros') as mock_load:
            mock_load.return_value = {
                'env_macro_a': {
                    'commands': [{'call': 'env_macro_b'}],
                    'env': {'VAR_A': 'value_a'}
                },
                'env_macro_b': {
                    'commands': [{'call': 'env_macro_a'}],  # Circular call
                    'env': {'VAR_B': 'value_b'}
                }
            }
            
            macro_def = {
                'commands': [
                    {'call': 'env_macro_a'}
                ],
                'env': {'START_VAR': 'start_value'}
            }

            with patch('sys.stderr', new_callable=StringIO) as mock_stderr:
                with self.assertRaises(SystemExit):
                    execute_macro('starting_macro', macro_def, self.logger)
                
                error_output = mock_stderr.getvalue()
                self.assertIn("Circular macro call detected", error_output)

    def test_circular_detection_in_complex_macro(self):
        """Test circular detection in a complex macro with multiple calls."""
        with patch('repeat_runner.executor.load_macros') as mock_load:
            mock_load.return_value = {
                'complex_macro': {
                    'commands': [
                        'echo "start"',
                        {'call': 'helper_macro'},
                        'echo "middle"',
                        {'call': 'problematic_macro'}  # This one causes the circle
                    ]
                },
                'helper_macro': {
                    'commands': ['echo "helping"']
                },
                'problematic_macro': {
                    'commands': [
                        {'call': 'complex_macro'}  # Calls back to original
                    ]
                }
            }
            
            macro_def = {
                'commands': [
                    {'call': 'complex_macro'}
                ]
            }

            with patch('sys.stderr', new_callable=StringIO) as mock_stderr:
                with self.assertRaises(SystemExit):
                    execute_macro('entry_macro', macro_def, self.logger)
                
                error_output = mock_stderr.getvalue()
                self.assertIn("Circular macro call detected", error_output)
                self.assertIn("complex_macro", error_output)

    def test_circular_detection_with_mixed_commands(self):
        """Test circular detection when macros have mixed regular commands and macro calls."""
        with patch('repeat_runner.executor.load_macros') as mock_load:
            mock_load.return_value = {
                'mixed_a': {
                    'commands': [
                        'echo "before call A"',
                        {'call': 'mixed_b'},
                        'echo "after call A"'
                    ]
                },
                'mixed_b': {
                    'commands': [
                        'echo "before call B"',
                        {'call': 'mixed_a'},  # Circular call back to A
                        'echo "after call B"'
                    ]
                }
            }
            
            macro_def = {
                'commands': [
                    {'call': 'mixed_a'}
                ]
            }

            with patch('sys.stderr', new_callable=StringIO) as mock_stderr:
                with self.assertRaises(SystemExit):
                    execute_macro('start_mixed', macro_def, self.logger)
                
                error_output = mock_stderr.getvalue()
                self.assertIn("Circular macro call detected", error_output)

    def test_circular_detection_with_deep_nesting(self):
        """Test circular detection with deeply nested macro calls."""
        # Create a deep nesting that eventually circles back
        macros = {}
        chain_length = 10  # Create a long chain
        
        # Create chain: macro_0 -> macro_1 -> ... -> macro_9 -> macro_0 (circle)
        for i in range(chain_length):
            next_i = (i + 1) % chain_length  # Circle back to 0 after 9
            macros[f'macro_{i}'] = {
                'commands': [
                    {'call': f'macro_{next_i}'}
                ]
            }
        
        macro_def = {
            'commands': [
                {'call': 'macro_0'}  # Start the chain
            ]
        }

        with patch('repeat_runner.executor.load_macros', return_value=macros), \
             patch('sys.stderr', new_callable=StringIO) as mock_stderr:
            with self.assertRaises(SystemExit):
                execute_macro('deep_start', macro_def, self.logger)
            
            error_output = mock_stderr.getvalue()
            self.assertIn("Circular macro call detected", error_output)

    def test_circular_detection_reset_between_executions(self):
        """Test that circular detection state is reset between separate macro executions."""
        with patch('repeat_runner.executor.load_macros') as mock_load:
            mock_load.return_value = {
                'safe_macro': {
                    'commands': ['echo "safe"']
                },
                'circular_macro': {
                    'commands': [
                        {'call': 'circular_macro'}  # Self-calling
                    ]
                }
            }
            
            safe_macro_def = {
                'commands': [
                    {'call': 'safe_macro'}
                ]
            }
            
            circular_macro_def = {
                'commands': [
                    {'call': 'circular_macro'}
                ]
            }

            # First, execute a safe macro (should succeed)
            with patch('subprocess.run') as mock_subprocess:
                mock_result = MagicMock()
                mock_result.returncode = 0
                mock_result.stdout = "safe"
                mock_result.stderr = ""
                mock_subprocess.return_value = mock_result

                execute_macro('safe_start', safe_macro_def, self.logger)

            # Then, try to execute a circular macro (should fail)
            with patch('sys.stderr', new_callable=StringIO) as mock_stderr:
                with self.assertRaises(SystemExit):
                    execute_macro('circular_start', circular_macro_def, self.logger)
                
                error_output = mock_stderr.getvalue()
                self.assertIn("Circular macro call detected", error_output)

    def test_circular_detection_with_execution_path_tracking(self):
        """Test that the error message includes the execution path."""
        with patch('repeat_runner.executor.load_macros') as mock_load:
            mock_load.return_value = {
                'path_a': {
                    'commands': [
                        {'call': 'path_b'}
                    ]
                },
                'path_b': {
                    'commands': [
                        {'call': 'path_a'}  # Creates A -> B -> A circle
                    ]
                }
            }
            
            macro_def = {
                'commands': [
                    {'call': 'path_a'}
                ]
            }

            with patch('sys.stderr', new_callable=StringIO) as mock_stderr:
                with self.assertRaises(SystemExit):
                    execute_macro('path_start', macro_def, self.logger)
                
                error_output = mock_stderr.getvalue()
                self.assertIn("Circular macro call detected", error_output)
                # Should mention the call stack/path in the error
                self.assertIn("path_a", error_output)
                self.assertIn("path_b", error_output)


if __name__ == '__main__':
    unittest.main()