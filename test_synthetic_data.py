#!/usr/bin/env python3
"""
Test script for synthetic data generator.
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

async def test_synthetic_data_generator():
    """Test the synthetic data generator."""
    print("🧪 Testing Synthetic Data Generator...")
    
    try:
        # Test imports
        from ais.core.synthetic_data_generator import SyntheticDataGenerator, DataSchema, DataType
        print("✓ Synthetic data generator imported successfully")
        
        # Create generator
        generator = SyntheticDataGenerator()
        print("✓ Generator created")
        
        # Initialize generator
        success = await generator.initialize()
        if not success:
            print("❌ Generator initialization failed")
            return False
        print("✓ Generator initialized")
        
        # Test numerical data generation (synchronous method)
        print("✓ Testing numerical data generation...")
        numerical_data = generator.generate_numerical_data(5)
        print(f"✓ Generated numerical data: {numerical_data}")
        
        # Test schema-based generation
        print("✓ Testing schema-based generation...")
        schemas = [
            DataSchema("value", DataType.NUMERICAL, {"mean": 10, "std": 2}),
            DataSchema("category", DataType.CATEGORICAL, {"categories": ["A", "B", "C"]}),
            DataSchema("description", DataType.TEXT, {"length": 5})
        ]
        
        generated_data = await generator.generate_data(schemas, 3)
        print(f"✓ Generated schema data: {generated_data.data}")
        print(f"✓ Metadata: {generated_data.metadata}")
        
        # Test different data types
        print("✓ Testing different data types...")
        
        # Numerical
        num_schema = [DataSchema("number", DataType.NUMERICAL, {"distribution": "uniform", "min": 0, "max": 100})]
        num_data = await generator.generate_data(num_schema, 2)
        print(f"✓ Uniform numerical: {num_data.data}")
        
        # Categorical
        cat_schema = [DataSchema("type", DataType.CATEGORICAL, {"categories": ["X", "Y", "Z"], "weights": [0.5, 0.3, 0.2]})]
        cat_data = await generator.generate_data(cat_schema, 5)
        print(f"✓ Weighted categorical: {cat_data.data}")
        
        # Time series
        ts_schema = [DataSchema("series", DataType.TIME_SERIES, {"length": 5, "trend": 0.5, "noise": 0.1})]
        ts_data = await generator.generate_data(ts_schema, 1)
        print(f"✓ Time series: {ts_data.data}")
        
        # Image placeholder
        img_schema = [DataSchema("image", DataType.IMAGE, {"width": 32, "height": 32, "channels": 3})]
        img_data = await generator.generate_data(img_schema, 1)
        print(f"✓ Image placeholder: {img_data.data}")
        
        # Get metrics
        metrics = await generator.get_generation_metrics()
        print(f"✓ Generation metrics: {metrics}")
        
        # Shutdown
        success = await generator.shutdown()
        if success:
            print("✓ Generator shutdown successful")
        else:
            print("❌ Generator shutdown failed")
            return False
        
        print("\n🎉 Synthetic data generator tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    try:
        result = asyncio.run(test_synthetic_data_generator())
        sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        print("\n🛑 Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Fatal test error: {e}")
        sys.exit(1)