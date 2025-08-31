"""
Simple startup script for the AIS system.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def check_dependencies():
    """Check if required dependencies are installed."""
    required_packages = [
        'fastapi',
        'uvicorn',
        'psutil',
        'pydantic'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print("❌ Missing required packages:")
        for package in missing_packages:
            print(f"   - {package}")
        print("\nPlease install missing packages with:")
        print("pip install " + " ".join(missing_packages))
        return False
    
    print("✓ All required packages are installed")
    return True

async def run_basic_test():
    """Run basic system test."""
    print("Running basic system test...")
    
    try:
        # Import test
        from test_basic import test_imports, test_component_creation
        
        # Run import test
        if not await test_imports():
            return False
        
        # Run component creation test
        if not await test_component_creation():
            return False
        
        print("✓ Basic system test passed")
        return True
        
    except Exception as e:
        print(f"❌ Basic system test failed: {e}")
        return False

def start_server():
    """Start the AIS server."""
    print("Starting AIS server...")
    
    try:
        import uvicorn
        from app import app
        
        # Get configuration
        host = os.getenv("AIS_HOST", "127.0.0.1")
        port = int(os.getenv("AIS_PORT", "8000"))
        
        print(f"🚀 Starting AIS server on http://{host}:{port}")
        print("Press Ctrl+C to stop the server")
        
        uvicorn.run(
            app,
            host=host,
            port=port,
            log_level="info",
            reload=False
        )
        
    except KeyboardInterrupt:
        print("\n👋 AIS server stopped")
    except Exception as e:
        print(f"❌ Failed to start server: {e}")
        return False
    
    return True

async def main():
    """Main startup function."""
    print("🤖 AIS v3.2.1 Startup")
    print("=" * 40)
    
    # Check dependencies
    if not check_dependencies():
        return 1
    
    # Run basic test
    if not await run_basic_test():
        print("❌ Basic tests failed. Please check the system.")
        return 1
    
    print("\n✅ System checks passed!")
    print("Starting AIS server...")
    
    # Start server
    start_server()
    
    return 0

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n👋 Startup cancelled")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Startup failed: {e}")
        sys.exit(1)