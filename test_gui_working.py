#!/usr/bin/env python3
"""
Working GUI test that properly handles PyQt6.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_gui_simple():
    """Test the simple GUI."""
    print("🖥️  Testing Simple GUI...")
    
    try:
        # Check PyQt6
        from PyQt6.QtWidgets import QApplication
        print("✓ PyQt6 is available")
        
        # Test simple GUI
        import gui_simple
        print("✓ Simple GUI module imported")
        
        # Test GUI creation (without showing)
        pyqt_available, qt_classes = gui_simple.check_pyqt6()
        if pyqt_available:
            print("✓ PyQt6 classes available")
            
            # Create GUI instance (don't show)
            gui = gui_simple.SimpleAISGUI(qt_classes)
            print("✓ Simple GUI created successfully")
            
            # Test synthetic data function
            gui.test_synthetic_data()
            print("✓ Synthetic data test completed")
            
            return True
        else:
            print("❌ PyQt6 not properly available")
            return False
            
    except Exception as e:
        print(f"❌ GUI test failed: {e}")
        return False

def run_gui_interactive():
    """Run GUI interactively."""
    print("🖥️  Starting Interactive GUI...")
    
    try:
        import gui_simple
        result = gui_simple.main()
        return result == 0
        
    except Exception as e:
        print(f"❌ Interactive GUI failed: {e}")
        return False

def main():
    """Main test function."""
    print("🧪 GUI Working Test")
    print("=" * 30)
    
    # Test GUI creation
    if test_gui_simple():
        print("\n✅ GUI test passed!")
        
        choice = input("\nRun interactive GUI? (y/n): ").lower().strip()
        if choice == 'y':
            return run_gui_interactive()
        else:
            return True
    else:
        print("\n❌ GUI test failed")
        return False

if __name__ == "__main__":
    try:
        result = main()
        sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        print("\n🛑 Test interrupted")
        sys.exit(1)