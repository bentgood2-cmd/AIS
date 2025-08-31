#!/usr/bin/env python3
"""
Simple GUI interface for the AIS system using PyQt6.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def check_pyqt6():
    """Check if PyQt6 is available."""
    try:
        from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QPushButton, QLabel, QTextEdit
        from PyQt6.QtCore import Qt
        return True, (QApplication, QMainWindow, QWidget, QVBoxLayout, QPushButton, QLabel, QTextEdit, Qt)
    except ImportError:
        return False, None

class SimpleAISGUI:
    """Simple AIS GUI when PyQt6 is available."""
    
    def __init__(self, qt_classes):
        QApplication, QMainWindow, QWidget, QVBoxLayout, QPushButton, QLabel, QTextEdit, Qt = qt_classes
        
        self.app = QApplication(sys.argv)
        self.window = QMainWindow()
        self.window.setWindowTitle("AIS System - Simple GUI")
        self.window.setGeometry(100, 100, 600, 400)
        
        # Central widget
        central_widget = QWidget()
        self.window.setCentralWidget(central_widget)
        
        # Layout
        layout = QVBoxLayout(central_widget)
        
        # Title
        title = QLabel("🚀 AIS System - Simple Interface")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 18px; font-weight: bold; margin: 10px;")
        layout.addWidget(title)
        
        # Status
        self.status_label = QLabel("Status: Ready")
        self.status_label.setStyleSheet("font-size: 14px; margin: 5px;")
        layout.addWidget(self.status_label)
        
        # Buttons
        self.test_button = QPushButton("Test Synthetic Data Generator")
        self.test_button.clicked.connect(self.test_synthetic_data)
        layout.addWidget(self.test_button)
        
        self.health_button = QPushButton("Run Health Check")
        self.health_button.clicked.connect(self.run_health_check)
        layout.addWidget(self.health_button)
        
        # Output area
        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        layout.addWidget(self.output_text)
        
        # Clear button
        clear_button = QPushButton("Clear Output")
        clear_button.clicked.connect(self.clear_output)
        layout.addWidget(clear_button)
    
    def log(self, message):
        """Add message to output."""
        self.output_text.append(message)
    
    def test_synthetic_data(self):
        """Test synthetic data generator."""
        self.status_label.setText("Status: Testing Synthetic Data...")
        self.log("🧪 Testing Synthetic Data Generator...")
        
        try:
            from ais.core.synthetic_data_generator import SyntheticDataGenerator
            generator = SyntheticDataGenerator()
            data = generator.generate_numerical_data(5)
            self.log(f"✓ Generated data: {data}")
            self.status_label.setText("Status: Synthetic Data Test Complete")
        except Exception as e:
            self.log(f"❌ Error: {e}")
            self.status_label.setText("Status: Test Failed")
    
    def run_health_check(self):
        """Run health check."""
        self.status_label.setText("Status: Running Health Check...")
        self.log("📊 Running Health Check...")
        
        try:
            # Check core modules
            from ais.core.base import SystemLevel, ComponentStatus
            self.log("✓ Core modules imported")
            
            # Check synthetic data
            from ais.core.synthetic_data_generator import SyntheticDataGenerator
            generator = SyntheticDataGenerator()
            test_data = generator.generate_numerical_data(3)
            self.log("✓ Synthetic data working")
            
            self.log("🎉 Health check passed!")
            self.status_label.setText("Status: Health Check Complete")
        except Exception as e:
            self.log(f"❌ Health check failed: {e}")
            self.status_label.setText("Status: Health Check Failed")
    
    def clear_output(self):
        """Clear output text."""
        self.output_text.clear()
    
    def show(self):
        """Show the GUI."""
        self.window.show()
        return self.app.exec()

def main():
    """Main function to run the simple GUI."""
    print("🖥️  Starting Simple AIS GUI...")
    
    # Check PyQt6 availability
    pyqt_available, qt_classes = check_pyqt6()
    
    if not pyqt_available:
        print("❌ PyQt6 not available. Please install it with:")
        print("   pip install PyQt6")
        print("\nAlternatively, use the web interface or command line.")
        return 1
    
    print("✓ PyQt6 available")
    print("✓ Creating simple GUI...")
    
    try:
        gui = SimpleAISGUI(qt_classes)
        print("✓ GUI created successfully")
        print("✓ Showing GUI window...")
        
        return gui.show()
        
    except Exception as e:
        print(f"❌ Error creating GUI: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())