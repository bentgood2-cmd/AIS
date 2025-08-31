#!/usr/bin/env python3
"""
Quick launcher for recursive learning system
"""

import asyncio
from recursive_learning import main

if __name__ == "__main__":
    print("🚀 LAUNCHING RECURSIVE LEARNING - 10,000 ITERATIONS")
    print("="*60)
    asyncio.run(main())