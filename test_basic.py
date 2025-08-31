"""
Basic test to verify AIS system components can be imported and initialized.
"""

import asyncio
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

async def test_imports():
    """Test that all components can be imported."""
    try:
        # Test core imports
        from ais.core.base import BaseComponent, SystemLevel, ComponentStatus
        from ais.core.exceptions import AISException, ResourceException
        from ais.core.operational import OperationalComponent
        from ais.core.regulatory import RegulatoryComponent
        from ais.core.optimization import OptimizationComponent
        from ais.core.adaptive import AdaptiveComponent
        from ais.core.identity import IdentityComponent
        from ais.core.synthetic_data_generator import SyntheticDataGenerator
        
        print("✓ All core components imported successfully")
        
        # Test utility imports
        from health import get_system_health, get_health_summary
        from metrics import metrics_collector, get_all_metrics
        
        print("✓ All utility modules imported successfully")
        
        return True
        
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return False

async def test_component_creation():
    """Test that components can be created and initialized."""
    try:
        # Create operational component
        operational = OperationalComponent("test_operational", SystemLevel.SYSTEM)
        await operational.initialize()
        print("✓ Operational component created and initialized")
        
        # Create regulatory component
        regulatory = RegulatoryComponent("test_regulatory", SystemLevel.SYSTEM)
        await regulatory.initialize()
        print("✓ Regulatory component created and initialized")
        
        # Create optimization component
        optimization = OptimizationComponent("test_optimization", SystemLevel.SYSTEM)
        await optimization.initialize()
        print("✓ Optimization component created and initialized")
        
        # Create adaptive component
        adaptive = AdaptiveComponent("test_adaptive", SystemLevel.SYSTEM)
        await adaptive.initialize()
        print("✓ Adaptive component created and initialized")
        
        # Create identity component
        identity = IdentityComponent("test_identity", SystemLevel.SYSTEM)
        await identity.initialize()
        print("✓ Identity component created and initialized")
        
        # Test synthetic data generator
        generator = SyntheticDataGenerator()
        print("✓ Synthetic data generator created")
        
        # Shutdown components
        await operational.shutdown()
        await regulatory.shutdown()
        await optimization.shutdown()
        await adaptive.shutdown()
        await identity.shutdown()
        print("✓ All components shut down successfully")
        
        return True
        
    except Exception as e:
        print(f"✗ Component creation error: {e}")
        return False

async def test_health_system():
    """Test health monitoring system."""
    try:
        health = await get_system_health()
        print(f"✓ Health check completed: {health.overall_status.value}")
        
        summary = get_health_summary()
        print(f"✓ Health summary retrieved: {summary['platform']}")
        
        return True
        
    except Exception as e:
        print(f"✗ Health system error: {e}")
        return False

async def test_metrics_system():
    """Test metrics collection system."""
    try:
        # Record a test metric
        metrics_collector.set_gauge("test_metric", 42.0)
        
        # Get metrics
        all_metrics = get_all_metrics()
        print(f"✓ Metrics system working: {all_metrics['total_metrics']} metrics")
        
        return True
        
    except Exception as e:
        print(f"✗ Metrics system error: {e}")
        return False

async def main():
    """Run all tests."""
    print("Starting AIS System Basic Tests...")
    print("=" * 50)
    
    tests = [
        ("Import Tests", test_imports),
        ("Component Creation Tests", test_component_creation),
        ("Health System Tests", test_health_system),
        ("Metrics System Tests", test_metrics_system)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        print("-" * 30)
        
        try:
            result = await test_func()
            if result:
                passed += 1
                print(f"✓ {test_name} PASSED")
            else:
                print(f"✗ {test_name} FAILED")
        except Exception as e:
            print(f"✗ {test_name} FAILED with exception: {e}")
    
    print("\n" + "=" * 50)
    print(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! AIS system is ready.")
        return 0
    else:
        print("❌ Some tests failed. Check the errors above.")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)