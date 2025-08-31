#!/usr/bin/env python3
"""
Test core functionality without external dependencies.
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_core_imports():
    """Test core module imports."""
    print("🧪 Testing Core Imports...")
    try:
        from ais.core.base import SystemLevel, ComponentStatus, BaseComponent
        print("✓ Base classes imported")
        
        from ais.core.synthetic_data_generator import SyntheticDataGenerator, DataType, DataSchema
        print("✓ Synthetic data generator imported")
        
        from ais.core.operational import OperationalComponent
        print("✓ Operational component imported")
        
        return True
    except Exception as e:
        print(f"❌ Import error: {e}")
        return False

def test_synthetic_data_basic():
    """Test basic synthetic data generation."""
    print("\n🧪 Testing Synthetic Data Generation...")
    try:
        from ais.core.synthetic_data_generator import SyntheticDataGenerator
        
        generator = SyntheticDataGenerator()
        print("✓ Generator created")
        
        # Test synchronous generation
        data = generator.generate_numerical_data(5)
        print(f"✓ Generated numerical data: {data}")
        
        return True
    except Exception as e:
        print(f"❌ Synthetic data error: {e}")
        return False

async def test_async_functionality():
    """Test async functionality."""
    print("\n🧪 Testing Async Functionality...")
    try:
        from ais.core.synthetic_data_generator import SyntheticDataGenerator, DataSchema, DataType
        
        generator = SyntheticDataGenerator()
        
        # Initialize
        success = await generator.initialize()
        if not success:
            print("❌ Generator initialization failed")
            return False
        print("✓ Generator initialized")
        
        # Test async generation
        schema = [DataSchema("test_value", DataType.NUMERICAL, {"mean": 0, "std": 1})]
        result = await generator.generate_data(schema, 3)
        print(f"✓ Generated async data: {result.data}")
        
        # Shutdown
        await generator.shutdown()
        print("✓ Generator shutdown complete")
        
        return True
    except Exception as e:
        print(f"❌ Async test error: {e}")
        return False

async def test_core_system():
    """Test core AIS system."""
    print("\n🧪 Testing Core AIS System...")
    try:
        from ais.main import AutocatalyticIntelligenceSystem
        
        system = AutocatalyticIntelligenceSystem()
        print("✓ System created")
        
        # Initialize
        success = await system.initialize()
        if not success:
            print("❌ System initialization failed")
            return False
        print("✓ System initialized")
        
        # Get status
        status = await system.get_system_status()
        print(f"✓ System status: {status['status']}")
        print(f"✓ Components: {len(status['components'])}")
        
        # Test data processing
        test_data = {"test": "data", "value": 42}
        result = await system.process_data(test_data)
        print("✓ Data processing successful")
        
        # Shutdown
        await system.shutdown()
        print("✓ System shutdown complete")
        
        return True
    except Exception as e:
        print(f"❌ Core system error: {e}")
        return False

async def main():
    """Run all core tests."""
    print("🚀 AIS Core Functionality Test")
    print("=" * 40)
    
    results = []
    
    # Test imports
    results.append(test_core_imports())
    
    # Test basic synthetic data
    results.append(test_synthetic_data_basic())
    
    # Test async functionality
    results.append(await test_async_functionality())
    
    # Test core system
    results.append(await test_core_system())
    
    # Summary
    print("\n📋 TEST RESULTS:")
    print("-" * 30)
    
    test_names = ["Core Imports", "Synthetic Data", "Async Functions", "Core System"]
    passed = 0
    
    for i, result in enumerate(results):
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status} - {test_names[i]}")
        if result:
            passed += 1
    
    print(f"\nResults: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("🎉 All core tests passed! System is working!")
        return 0
    else:
        print("⚠️  Some tests failed, but basic functionality may still work")
        return 1

if __name__ == "__main__":
    try:
        result = asyncio.run(main())
        sys.exit(result)
    except KeyboardInterrupt:
        print("\n🛑 Tests interrupted")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        sys.exit(1)