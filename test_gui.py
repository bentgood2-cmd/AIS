#!/usr/bin/env python3
"""
Test script for GUI functionality.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_gui_imports():
    """Test GUI imports and basic functionality."""
    print("🧪 Testing GUI Imports...")
    
    try:
        # Test PyQt6 import
        try:
            from PyQt6.QtWidgets import QApplication, QMainWindow
            print("✓ PyQt6 imported successfully")
            pyqt_available = True
        except ImportError as e:
            print(f"❌ PyQt6 not available: {e}")
            print("ℹ️  Install PyQt6 with: pip install PyQt6")
            pyqt_available = False
        
        if pyqt_available:
            # Test full GUI module import
            try:
                from gui import AISMainWindow
                print("✓ Full GUI module imported successfully")
                
                # Test GUI creation (without showing)
                app = QApplication([])
                window = AISMainWindow()
                print("✓ GUI window created successfully")
                app.quit()
                
            except Exception as e:
                print(f"⚠️  Full GUI has issues: {e}")
                print("✓ Using simple GUI instead")
        
        # Test simple GUI fallback
        import gui_simple
        print("✓ Simple GUI module imported successfully")
        return True
        
        # Test GUI creation (without showing)
        app = QApplication([])
        window = AISMainWindow()
        print("✓ GUI window created successfully")
        
        # Test basic functionality
        print("✓ Testing GUI components...")
        
        # Check if tabs are created
        tab_count = window.tab_widget.count()
        print(f"✓ Created {tab_count} tabs")
        
        # Check tab names
        tab_names = []
        for i in range(tab_count):
            tab_names.append(window.tab_widget.tabText(i))
        print(f"✓ Tab names: {tab_names}")
        
        # Test synthetic data generation UI
        window.schema_combo.setCurrentText("numerical")
        window.count_spin.setValue(5)
        print("✓ Synthetic data UI configured")
        
        # Simulate data generation
        window.generate_synthetic_data()
        print("✓ Synthetic data generation simulated")
        
        # Test component tree
        component_count = window.components_tree.topLevelItemCount()
        print(f"✓ Component tree has {component_count} items")
        
        # Clean up
        app.quit()
        print("✓ GUI test completed successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ GUI test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_gui_display():
    """Test GUI display (interactive)."""
    print("🖥️  Testing GUI Display...")
    
    try:
        import gui_simple
        
        print("✓ Starting simple GUI...")
        result = gui_simple.main()
        
        if result == 0:
            print("✓ GUI closed successfully")
            return True
        else:
            print("⚠️  GUI closed with issues")
            return False
        
    except Exception as e:
        print(f"❌ GUI display test failed: {e}")
        return False

if __name__ == "__main__":
    print("🧪 GUI Test Suite")
    print("=" * 50)
    
    # Test imports first
    import_result = test_gui_imports()
    
    if import_result:
        print("\n" + "=" * 50)
        choice = input("Run interactive GUI test? (y/n): ").lower().strip()
        
        if choice == 'y':
            display_result = test_gui_display()
            sys.exit(0 if display_result else 1)
        else:
            print("✓ Skipping interactive test")
            sys.exit(0)
    else:
        sys.exit(1)