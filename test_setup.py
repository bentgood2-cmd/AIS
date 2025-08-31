"""
Test script for the refactored AIS setup system.
Verifies that all components can be imported and basic functionality works.
"""
import sys
from pathlib import Path
import logging

# Configure basic logging for tests
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def test_imports():
    """Test that all setup modules can be imported."""
    try:
        from setup_config import AIS_VERSION, DIRECTORIES, FILE_TEMPLATES
        logger.info(f"✓ Configuration module imported successfully (AIS v{AIS_VERSION})")
        
        from setup_utils import SetupValidator, ProgressTracker, ErrorHandler, SystemInfo
        logger.info("✓ Utilities module imported successfully")
        
        from setup_ais import AISSetup, SetupConfig
        logger.info("✓ Main setup module imported successfully")
        
        return True
    except ImportError as e:
        logger.error(f"✗ Import failed: {e}")
        return False

def test_configuration():
    """Test configuration values."""
    try:
        from setup_config import AIS_VERSION, DIRECTORIES, FILE_TEMPLATES
        
        # Check version
        assert AIS_VERSION == "3.2.1", f"Expected version 3.2.1, got {AIS_VERSION}"
        logger.info(f"✓ Version check passed: {AIS_VERSION}")
        
        # Check directories
        assert DIRECTORIES, "No directories defined"
        logger.info(f"✓ Directory count: {len(DIRECTORIES)}")
        
        # Check file templates
        assert FILE_TEMPLATES, "No file templates defined"
        template_count = len(FILE_TEMPLATES)
        logger.info(f"✓ File template count: {template_count}")
        
        return True
    except Exception as e:
        logger.error(f"✗ Configuration test failed: {e}")
        return False

def test_utility_classes():
    """Test utility class instantiation."""
    try:
        from setup_utils import SetupValidator, ProgressTracker, ErrorHandler, SystemInfo
        
        # Test SetupValidator
        validator = SetupValidator()
        logger.info("✓ SetupValidator instantiated")
        
        # Test ProgressTracker
        tracker = ProgressTracker(5)
        tracker.add_step("Test Step")
        tracker.start_step("Test Step")
        tracker.complete_step("Test Step")
        assert tracker.get_progress() == 20.0, "Progress calculation failed"
        logger.info("✓ ProgressTracker functionality verified")
        
        # Test SystemInfo
        info = SystemInfo.get_system_info()
        assert "platform" in info, "System info missing platform"
        logger.info("✓ SystemInfo functionality verified")
        
        return True
    except Exception as e:
        logger.error(f"✗ Utility classes test failed: {e}")
        return False

def test_setup_classes():
    """Test setup class instantiation."""
    try:
        from setup_ais import AISSetup, SetupConfig
        from pathlib import Path
        
        # Test SetupConfig
        config = SetupConfig()
        assert config.version == "3.2.1", "Config version mismatch"
        logger.info("✓ SetupConfig instantiated")
        
        # Test AISSetup (without running setup)
        setup = AISSetup(config)
        assert setup.config.version == "3.2.1", "Setup config version mismatch"
        logger.info("✓ AISSetup instantiated")
        
        return True
    except Exception as e:
        logger.error(f"✗ Setup classes test failed: {e}")
        return False

def test_file_structure():
    """Test that expected files exist."""
    expected_files = [
        "setup_ais.py",
        "setup_config.py", 
        "setup_utils.py",
        "README.md"
    ]
    
    missing_files = [file_name for file_name in expected_files if not Path(file_name).exists()]
    
    if missing_files:
        logger.error(f"✗ Missing files: {missing_files}")
        return False
    
    logger.info("✓ All expected files present")
    return True

def run_all_tests():
    """Run all tests and report results."""
    logger.info("Starting AIS Setup System Tests")
    logger.info("=" * 40)
    
    tests = [
        ("File Structure", test_file_structure),
        ("Module Imports", test_imports),
        ("Configuration", test_configuration),
        ("Utility Classes", test_utility_classes),
        ("Setup Classes", test_setup_classes),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        logger.info(f"\nRunning: {test_name}")
        try:
            if test_func():
                logger.info(f"✓ {test_name} PASSED")
                passed += 1
            else:
                logger.error(f"✗ {test_name} FAILED")
        except (ImportError, AssertionError, ValueError) as e:
            logger.error(f"✗ {test_name} ERROR: {e}")
        except Exception as e:
            logger.error(f"✗ {test_name} UNEXPECTED ERROR: {e}")
    
    logger.info("\n" + "=" * 40)
    logger.info(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 All tests passed! Setup system is ready.")
        return True
    else:
        logger.error("❌ Some tests failed. Please check the errors above.")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
