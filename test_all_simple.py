#!/usr/bin/env python3
"""
Simple test script to verify all components work.
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_synthetic_data():
    """Test synthetic data generator."""
    print("🧪 Testing Synthetic Data Generator...")
    try:
        from ais.core.synthetic_data_generator import SyntheticDataGenerator
        generator = SyntheticDataGenerator()
        data = generator.generate_numerical_data(3)
        print(f"✓ Generated data: {data}")
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_gui_availability():
    """Test GUI availability."""
    print("🖥️  Testing GUI Availability...")
    try:
        # Check PyQt6
        try:
            from PyQt6.QtWidgets import QApplication
            print("✓ PyQt6 is available")
            pyqt_available = True
        except ImportError:
            print("❌ PyQt6 not available")
            pyqt_available = False
        
        # Test simple GUI
        import gui_simple
        print("✓ Simple GUI module available")
        
        if pyqt_available:
            print("✓ Full GUI functionality available")
        else:
            print("ℹ️  Install PyQt6 for full GUI: pip install PyQt6")
        
        return True
    except Exception as e:
        print(f"❌ GUI test error: {e}")
        return False

async def test_core_system():
    """Test core AIS system."""
    print("🧠 Testing Core AIS System...")
    try:
        from ais.main import AutocatalyticIntelligenceSystem
        system = AutocatalyticIntelligenceSystem()
        
        success = await system.initialize()
        if not success:
            print("❌ System initialization failed")
            return False
        
        print("✓ System initialized")
        
        # Test data processing
        test_data = {"test": "data"}
        result = await system.process_data(test_data)
        print("✓ Data processing works")
        
        # Shutdown
        await system.shutdown()
        print("✓ System shutdown complete")
        
        return True
    except Exception as e:
        print(f"❌ Core system error: {e}")
        return False

async def main():
    """Run all tests."""
    print("🚀 AIS System - Quick Test Suite")
    print("=" * 50)
    
    results = []
    
    # Test synthetic data
    results.append(test_synthetic_data())
    print()
    
    # Test GUI
    results.append(test_gui_availability())
    print()
    
    # Test core system
    results.append(await test_core_system())
    print()
    
    # Summary
    print("📋 TEST SUMMARY:")
    print("-" * 30)
    
    passed = sum(results)
    total = len(results)
    
    for i, result in enumerate(results, 1):
        status = "✅ PASS" if result else "❌ FAIL"
        test_names = ["Synthetic Data", "GUI", "Core System"]
        print(f"  {status} - {test_names[i-1]}")
    
    print(f"\nResults: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! System is ready to use.")
        return 0
    else:
        print("⚠️  Some tests failed. Check the output above.")
        return 1

if __name__ == "__main__":
    try:
        result = asyncio.run(main())
        sys.exit(result)
    except KeyboardInterrupt:
        print("\n🛑 Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Fatal test error: {e}")
        sys.exit(1)