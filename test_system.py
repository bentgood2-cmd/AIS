#!/usr/bin/env python3
"""
Simple test script to verify AIS system functionality.
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

async def test_ais_system():
    """Test the AIS system components."""
    print("🧪 Testing AIS System Components...")
    
    try:
        # Test imports
        print("✓ Testing imports...")
        from ais.main import AutocatalyticIntelligenceSystem
        from ais.core.base import SystemLevel, ComponentStatus
        print("✓ All imports successful")
        
        # Test system creation
        print("✓ Creating AIS system...")
        ais_system = AutocatalyticIntelligenceSystem()
        print("✓ AIS system created successfully")
        
        # Test initialization
        print("✓ Initializing system...")
        success = await ais_system.initialize()
        if success:
            print("✓ System initialized successfully")
        else:
            print("❌ System initialization failed")
            return False
        
        # Test status
        print("✓ Getting system status...")
        status = await ais_system.get_system_status()
        print(f"✓ System status: {status['status']}")
        print(f"✓ Components: {len(status['components'])}")
        
        # Test data processing
        print("✓ Testing data processing...")
        test_data = {"test": "data", "value": 42}
        result = await ais_system.process_data(test_data)
        print("✓ Data processing successful")
        
        # Test shutdown
        print("✓ Shutting down system...")
        success = await ais_system.shutdown()
        if success:
            print("✓ System shutdown successful")
        else:
            print("❌ System shutdown failed")
            return False
        
        print("\n🎉 All tests passed! AIS system is working correctly.")
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        return False

if __name__ == "__main__":
    try:
        result = asyncio.run(test_ais_system())
        sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        print("\n🛑 Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Fatal test error: {e}")
        sys.exit(1)