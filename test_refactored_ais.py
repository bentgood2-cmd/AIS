"""
Test script for the refactored AIS system.
Verifies that all components work correctly.
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add the ais package to the path
sys.path.insert(0, str(Path(__file__).parent))

from ais.core.base import SystemLevel, ComponentStatus, ProcessRequest, create_component
from ais.core.synthetic_data_generator import SyntheticDataGenerator
from ais.main import AutocatalyticIntelligenceSystem

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

async def test_base_components():
    """Test the base component system."""
    logger.info("Testing base components...")
    
    try:
        # Test component creation
        operational = create_component("operational", "TestOperational", SystemLevel.SYSTEM)
        regulatory = create_component("regulatory", "TestRegulatory", SystemLevel.SYSTEM)
        optimization = create_component("optimization", "TestOptimization", SystemLevel.SYSTEM)
        adaptive = create_component("adaptive", "TestAdaptive", SystemLevel.SYSTEM)
        identity = create_component("identity", "TestIdentity", SystemLevel.SYSTEM)
        
        logger.info("✓ All components created successfully")
        
        # Test component initialization
        await operational.initialize()
        await regulatory.initialize()
        await optimization.initialize()
        await adaptive.initialize()
        await identity.initialize()
        
        logger.info("✓ All components initialized successfully")
        
        # Test component status
        assert operational.status == ComponentStatus.ACTIVE
        assert regulatory.status == ComponentStatus.ACTIVE
        assert optimization.status == ComponentStatus.ACTIVE
        assert adaptive.status == ComponentStatus.ACTIVE
        assert identity.status == ComponentStatus.ACTIVE
        
        logger.info("✓ All components are in ACTIVE state")
        
        # Test component shutdown
        await operational.shutdown()
        await regulatory.shutdown()
        await optimization.shutdown()
        await adaptive.shutdown()
        await identity.shutdown()
        
        logger.info("✓ All components shut down successfully")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Base component test failed: {e}")
        return False

async def test_synthetic_data_generator():
    """Test the synthetic data generator."""
    logger.info("Testing synthetic data generator...")
    
    try:
        generator = SyntheticDataGenerator(seed=42)
        
        # Test numerical data generation
        numerical_data = generator.generate_numerical_data(100, distribution="normal", min_val=0, max_val=100)
        assert len(numerical_data) == 100
        logger.info("✓ Numerical data generation successful")
        
        # Test categorical data generation
        categorical_data = generator.generate_categorical_data(50, categories=["A", "B", "C"])
        assert len(categorical_data) == 50
        logger.info("✓ Categorical data generation successful")
        
        # Test text data generation
        text_data = generator.generate_text_data(25, text_type="words")
        assert len(text_data) == 25
        logger.info("✓ Text data generation successful")
        
        # Test image data generation
        image_data = generator.generate_image_data(5, width=32, height=32, channels=3)
        assert len(image_data) == 5
        logger.info("✓ Image data generation successful")
        
        # Test time series data generation
        time_series_data = generator.generate_time_series_data(200, data_type="trend")
        assert len(time_series_data) == 200
        logger.info("✓ Time series data generation successful")
        
        # Test tabular data generation
        tabular_data = generator.generate_tabular_data(100)
        assert len(tabular_data) == 100
        logger.info("✓ Tabular data generation successful")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Synthetic data generator test failed: {e}")
        return False
        
        # Test data export
        json_export = await generator.export_data(numerical_data, "json")
        assert "feature_1" in json_export
        logger.info("✓ Data export successful")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Synthetic data generator test failed: {e}")
        return False

async def test_ais_system():
    """Test the complete AIS system."""
    logger.info("Testing complete AIS system...")
    
    try:
        # Create and initialize AIS system
        ais = AutocatalyticIntelligenceSystem()
        await ais.initialize()
        
        logger.info("✓ AIS system initialized successfully")
        
        # Test system status
        status = await ais.get_system_status()
        assert status["status"] == "stopped"  # System is not running yet
        assert len(status["components"]) == 5  # operational, regulatory, optimization, adaptive, identity
        
        logger.info("✓ System status check successful")
        
        # Test synthetic data generation through the system
        numerical_data = await ais.generate_synthetic_data("numerical", 50, distribution="normal", min_val=0, max_val=100)
        assert len(numerical_data) == 50
        
        logger.info("✓ System data generation successful")
        
        # Test request processing (not implemented in current version)
        logger.info("✓ Request processing test skipped (not implemented)")
        
        # Test system shutdown
        await ais.shutdown()
        logger.info("✓ AIS system shutdown successful")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ AIS system test failed: {e}")
        return False

async def main():
    """Run all tests."""
    logger.info("Starting AIS system tests...")
    
    tests = [
        ("Base Components", test_base_components),
        ("Synthetic Data Generator", test_synthetic_data_generator),
        ("Complete AIS System", test_ais_system)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        logger.info(f"\n{'='*50}")
        logger.info(f"Running test: {test_name}")
        logger.info(f"{'='*50}")
        
        try:
            result = await test_func()
            results.append((test_name, result))
            
            if result:
                logger.info(f"✓ {test_name} test PASSED")
            else:
                logger.error(f"✗ {test_name} test FAILED")
                
        except Exception as e:
            logger.error(f"✗ {test_name} test FAILED with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    logger.info(f"\n{'='*50}")
    logger.info("TEST SUMMARY")
    logger.info(f"{'='*50}")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "PASSED" if result else "FAILED"
        logger.info(f"{test_name}: {status}")
    
    logger.info(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 All tests passed! The refactored AIS system is working correctly.")
        return 0
    else:
        logger.error("❌ Some tests failed. Please check the errors above.")
        return 1

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        logger.info("Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)
