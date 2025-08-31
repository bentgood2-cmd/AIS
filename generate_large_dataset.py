#!/usr/bin/env python3
"""Generate large synthetic datasets for training."""

import numpy as np
import pandas as pd
import os

def generate_large_dataset(name, samples, features, classes=2):
    """Generate large synthetic dataset."""
    print(f"Generating {name} with {samples:,} samples, {features} features...")
    
    # Generate features
    X = np.random.randn(samples, features)
    
    # Add some structure for realistic patterns
    if features > 10:
        # Create feature interactions
        X[:, 1] = X[:, 0] * 0.5 + np.random.randn(samples) * 0.3
        X[:, 2] = X[:, 0] ** 2 + np.random.randn(samples) * 0.2
    
    # Generate target with some complexity
    if classes == 2:
        # Binary classification
        linear_combo = np.sum(X[:, :min(5, features)], axis=1)
        y = (linear_combo + np.random.randn(samples) * 0.5 > 0).astype(int)
    else:
        # Multi-class
        linear_combo = np.sum(X[:, :min(3, features)], axis=1)
        y = np.digitize(linear_combo, bins=np.linspace(linear_combo.min(), linear_combo.max(), classes))
        y = np.clip(y - 1, 0, classes - 1)
    
    # Combine features and target
    data = np.column_stack([X, y])
    
    # Save to CSV
    os.makedirs("data", exist_ok=True)
    filepath = f"data/{name}.csv"
    pd.DataFrame(data).to_csv(filepath, index=False, header=False)
    
    print(f"✓ Generated {filepath} ({os.path.getsize(filepath) / 1024 / 1024:.1f} MB)")
    return filepath

if __name__ == "__main__":
    # Generate large datasets
    generate_large_dataset("mega_classification", 500000, 100, 2)
    generate_large_dataset("ultra_multiclass", 250000, 50, 10)
    generate_large_dataset("extreme_features", 100000, 500, 5)
    print("✅ All large datasets generated!")