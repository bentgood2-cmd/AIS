#!/usr/bin/env python3
"""
Simple test for synthetic data generator functionality.
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

async def test_synthetic_data_simple():
    """Simple test of synthetic data generator."""
    print("🧪 Testing Synthetic Data Generator...")
    
    try:
        from ais.core.synthetic_data_generator import SyntheticDataGenerator
        print("✓ Imported SyntheticDataGenerator")
        
        # Create generator
        generator = SyntheticDataGenerator()
        print("✓ Created generator instance")
        
        # Test synchronous numerical data generation
        print("✓ Testing numerical data generation...")
        data = generator.generate_numerical_data(5)
        print(f"✓ Generated data: {data}")
        
        # Initialize for async operations
        await generator.initialize()
        print("✓ Generator initialized")
        
        # Test async generation
        from ais.core.synthetic_data_generator import DataSchema, DataType
        schema = [DataSchema("test_value", DataType.NUMERICAL, {"mean": 10, "std": 2})]
        result = await generator.generate_data(schema, 3)
        print(f"✓ Generated async data: {result.data}")
        
        # Shutdown
        await generator.shutdown()
        print("✓ Generator shutdown complete")
        
        print("\n🎉 Synthetic data generator is working!")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    result = asyncio.run(test_synthetic_data_simple())
    sys.exit(0 if result else 1)