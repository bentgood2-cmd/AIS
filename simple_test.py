#!/usr/bin/env python3
"""
Simple test script to verify the AIS system components.
"""

import sys
import asyncio
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

async def test_imports():
    """Test basic imports."""
    print("🧪 Testing basic imports...")
    
    try:
        from ais.core.base import SystemLevel, ComponentStatus, ProcessRequest, create_component
        print("✅ Base imports successful")
    except Exception as e:
        print(f"❌ Base imports failed: {e}")
        return False
    
    try:
        from ais.core.operational import OperationalComponent
        print("✅ Operational component import successful")
    except Exception as e:
        print(f"❌ Operational component import failed: {e}")
        return False
    
    try:
        from ais.core.synthetic_data_generator import SyntheticDataGenerator
        print("✅ Synthetic data generator import successful")
    except Exception as e:
        print(f"❌ Synthetic data generator import failed: {e}")
        return False
    
    try:
        from ais.main import AutocatalyticIntelligenceSystem
        print("✅ Main system import successful")
    except Exception as e:
        print(f"❌ Main system import failed: {e}")
        return False
    
    return True

async def test_component_creation():
    """Test component creation."""
    print("\n🧪 Testing component creation...")
    
    try:
        from ais.core.base import create_component, SystemLevel
        
        # Test creating an operational component
        op_comp = create_component("operational", "TestOp", SystemLevel.SYSTEM)
        print("✅ Operational component created successfully")
        
        # Test creating a regulatory component
        reg_comp = create_component("regulatory", "TestReg", SystemLevel.SYSTEM)
        print("✅ Regulatory component created successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Component creation failed: {e}")
        return False

async def test_synthetic_data():
    """Test synthetic data generation."""
    print("\n🧪 Testing synthetic data generation...")
    
    try:
        from ais.core.synthetic_data_generator import SyntheticDataGenerator, DataType, DataSchema
        
        generator = SyntheticDataGenerator()
        
        # Test numerical data generation using schema
        numerical_schema = [DataSchema("value", DataType.NUMERICAL, {"min": 0, "max": 100})]
        num_data = await generator.generate_data(numerical_schema, 5)
        print(f"✅ Numerical data generated: {len(num_data.data)} samples")
        
        # Test categorical data generation using schema
        categorical_schema = [DataSchema("category", DataType.CATEGORICAL, {"categories": ["A", "B", "C"]})]
        cat_data = await generator.generate_data(categorical_schema, 3)
        print(f"✅ Categorical data generated: {len(cat_data.data)} samples")
        
        # Test predefined schema generation
        predefined_data = await generator.generate_predefined_data("numerical", 4)
        print(f"✅ Predefined data generated: {len(predefined_data.data)} samples")
        
        return True
        
    except Exception as e:
        print(f"❌ Synthetic data generation failed: {e}")
        return False

async def test_main_system():
    """Test main system initialization."""
    print("\n🧪 Testing main system...")
    
    try:
        from ais.main import AutocatalyticIntelligenceSystem
        
        ais = AutocatalyticIntelligenceSystem()
        print("✅ AIS system created successfully")
        
        # Test initialization
        success = await ais.initialize()
        if success:
            print("✅ AIS system initialized successfully")
            
            # Test status
            status = ais.get_system_status()
            print(f"✅ System status: {status['status']}")
            print(f"✅ Components: {len(status['components'])}")
            
            # Test synthetic data generation using the correct interface
            from ais.core.synthetic_data_generator import DataType, DataSchema
            numerical_schema = [DataSchema("value", DataType.NUMERICAL, {"min": 0, "max": 100})]
            data_result = await ais.synthetic_data_generator.generate_data(numerical_schema, 10)
            print(f"✅ Synthetic data generated: {len(data_result.data)} samples")
            
            # Test shutdown
            await ais.shutdown()
            print("✅ AIS system shut down successfully")
            
            return True
        else:
            print("❌ AIS system initialization failed")
            return False
            
    except Exception as e:
        print(f"❌ Main system test failed: {e}")
        return False

async def main():
    """Run all tests."""
    print("🚀 AIS System Test Suite")
    print("=" * 50)
    
    tests = [
        test_imports,
        test_component_creation,
        test_synthetic_data,
        test_main_system
    ]
    
    results = []
    for test in tests:
        try:
            result = await test()
            results.append(result)
        except Exception as e:
            print(f"❌ Test {test.__name__} crashed: {e}")
            results.append(False)
    
    print("\n" + "=" * 50)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 50)
    
    passed = sum(results)
    total = len(results)
    
    for i, (test, result) in enumerate(zip(tests, results), 1):
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{i}. {test.__name__}: {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The AIS system is ready to run.")
        return 0
    else:
        print("⚠️  Some tests failed. Please check the errors above.")
        return 1

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n🛑 Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test suite crashed: {e}")
        sys.exit(1)
