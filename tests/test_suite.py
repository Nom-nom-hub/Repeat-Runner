import unittest
import sys
import os

# Add the project root to the Python path so tests can import modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Import all test modules
from tests.unit.test_macros import TestMacros
from tests.unit.test_executor import TestExecutor
from tests.unit.test_logger import TestLogger
from tests.unit.test_runner import TestRunner
from tests.test_integration import TestIntegration
from tests.test_env_vars import TestEnvironmentVariableSupport
from tests.test_macro_chaining import TestMacroChaining
from tests.test_logging import TestCommandExecutionLogging
from tests.test_error_handling import TestErrorHandling
from tests.test_edge_cases import TestEdgeCases
from tests.test_circular_calls import TestCircularMacroCalls
from tests.test_file_permissions import TestFilePermissionIssues


def create_test_suite():
    """Create a test suite with all tests."""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test cases to the suite
    suite.addTests(loader.loadTestsFromTestCase(TestMacros))
    suite.addTests(loader.loadTestsFromTestCase(TestExecutor))
    suite.addTests(loader.loadTestsFromTestCase(TestLogger))
    suite.addTests(loader.loadTestsFromTestCase(TestRunner))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegration))
    suite.addTests(loader.loadTestsFromTestCase(TestEnvironmentVariableSupport))
    suite.addTests(loader.loadTestsFromTestCase(TestMacroChaining))
    suite.addTests(loader.loadTestsFromTestCase(TestCommandExecutionLogging))
    suite.addTests(loader.loadTestsFromTestCase(TestErrorHandling))
    suite.addTests(loader.loadTestsFromTestCase(TestEdgeCases))
    suite.addTests(loader.loadTestsFromTestCase(TestCircularMacroCalls))
    suite.addTests(loader.loadTestsFromTestCase(TestFilePermissionIssues))
    
    return suite


if __name__ == '__main__':
    # Create and run the test suite
    test_suite = create_test_suite()
    
    # Create a test runner
    runner = unittest.TextTestRunner(verbosity=2)
    
    # Run the tests
    result = runner.run(test_suite)
    
    # Exit with error code if tests failed
    if result.failures or result.errors:
        sys.exit(1)
    else:
        print("\nAll tests passed! ✓")