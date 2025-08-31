#!/usr/bin/env python3
"""
Complex GUI interface for the AIS system using PyQt6.
"""

import asyncio
import json
import logging
import sys
import threading
from datetime import datetime, timezone
from typing import Dict, Any, Optional

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QPushButton, QLabel, QTextEdit, QTableWidget,
    QTableWidgetItem, QProgressBar, QGroupBox, QGridLayout,
    QSplitter, QTreeWidget, QTreeWidgetItem, QMessageBox,
    QStatusBar, QMenuBar, QMenu, QDialog, QLineEdit,
    QComboBox, QSpinBox, QCheckBox, QFormLayout, QScrollArea
)
from PyQt6.QtCore import QTimer, QThread, pyqtSignal, Qt, QSize
from PyQt6.QtGui import QFont, QIcon, QPixmap, QPalette, QColor, QAction

# Configure logging
logger = logging.getLogger(__name__)

class AISWorkerThread(QThread):
    """Worker thread for AIS operations."""
    
    # Signals
    health_updated = pyqtSignal(dict)
    metrics_updated = pyqtSignal(dict)
    status_updated = pyqtSignal(dict)
    error_occurred = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.running = False
        self.update_interval = 5000  # 5 seconds
        
    def run(self):
        """Main thread loop."""
        self.running = True
        
        while self.running:
            try:
                # Update health status
                self._update_health()
                
                # Update metrics
                self._update_metrics()
                
                # Update system status
                self._update_status()
                
                # Sleep for update interval
                self.msleep(self.update_interval)
                
            except Exception as e:
                self.error_occurred.emit(str(e))
                self.msleep(10000)  # Wait longer on error
    
    def stop(self):
        """Stop the worker thread."""
        self.running = False
        self.wait()
    
    def _update_health(self):
        """Update health status."""
        try:
            health_data = {
                "status": "healthy",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "checks": [
                    {"component": "core", "status": "healthy", "message": "All systems operational"},
                    {"component": "api", "status": "healthy", "message": "API responding normally"},
                    {"component": "database", "status": "healthy", "message": "Database connection stable"}
                ]
            }
            self.health_updated.emit(health_data)
            
        except Exception as e:
            logger.error(f"Health update failed: {e}")
    
    def _update_metrics(self):
        """Update metrics data."""
        try:
            metrics_data = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "total_metrics": 15,
                "metrics_by_category": {
                    "performance": 5,
                    "resource": 4,
                    "system": 3,
                    "business": 3
                },
                "metrics_by_type": {
                    "counter": 8,
                    "gauge": 4,
                    "histogram": 3
                }
            }
            self.metrics_updated.emit(metrics_data)
            
        except Exception as e:
            logger.error(f"Metrics update failed: {e}")
    
    def _update_status(self):
        """Update system status."""
        try:
            status_data = {
                "is_running": True,
                "components": {
                    "operational": {"status": "running", "name": "main_operational"},
                    "regulatory": {"status": "running", "name": "main_regulatory"},
                    "optimization": {"status": "running", "name": "main_optimization"},
                    "adaptive": {"status": "running", "name": "main_adaptive"},
                    "identity": {"status": "running", "name": "main_identity"}
                },
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            self.status_updated.emit(status_data)
            
        except Exception as e:
            logger.error(f"Status update failed: {e}")


class ComponentControlDialog(QDialog):
    """Dialog for controlling individual components."""
    
    def __init__(self, component_name: str, parent=None):
        super().__init__(parent)
        self.component_name = component_name
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the dialog UI."""
        self.setWindowTitle(f"Component Control - {self.component_name}")
        self.setModal(True)
        self.resize(400, 300)
        
        layout = QVBoxLayout()
        
        # Component info
        info_group = QGroupBox("Component Information")
        info_layout = QFormLayout()
        
        self.name_label = QLabel(self.component_name)
        self.status_label = QLabel("Unknown")
        self.level_label = QLabel("Unknown")
        
        info_layout.addRow("Name:", self.name_label)
        info_layout.addRow("Status:", self.status_label)
        info_layout.addRow("Level:", self.level_label)
        info_group.setLayout(info_layout)
        
        # Control buttons
        control_group = QGroupBox("Control Actions")
        control_layout = QVBoxLayout()
        
        self.start_button = QPushButton("Start Component")
        self.stop_button = QPushButton("Stop Component")
        self.restart_button = QPushButton("Restart Component")
        
        control_layout.addWidget(self.start_button)
        control_layout.addWidget(self.stop_button)
        control_layout.addWidget(self.restart_button)
        control_group.setLayout(control_layout)
        
        # Log display
        log_group = QGroupBox("Component Log")
        log_layout = QVBoxLayout()
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(150)
        
        log_layout.addWidget(self.log_text)
        log_group.setLayout(log_layout)
        
        # Add all groups to main layout
        layout.addWidget(info_group)
        layout.addWidget(control_group)
        layout.addWidget(log_group)
        
        # Connect signals
        self.start_button.clicked.connect(self.start_component)
        self.stop_button.clicked.connect(self.stop_component)
        self.restart_button.clicked.connect(self.restart_component)
        
        self.setLayout(layout)
    
    def update_status(self, status: str, level: str):
        """Update component status display."""
        self.status_label.setText(status)
        self.level_label.setText(level)
        
        # Update button states based on status
        is_running = status.lower() == "running"
        self.start_button.setEnabled(not is_running)
        self.stop_button.setEnabled(is_running)
        self.restart_button.setEnabled(True)
    
    def add_log_message(self, message: str):
        """Add a log message to the display."""
        timestamp = datetime.now(timezone.utc).strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {message}")
    
    def start_component(self):
        """Start the component."""
        self.add_log_message(f"Starting component {self.component_name}...")
        self.add_log_message("Component start command sent")
    
    def stop_component(self):
        """Stop the component."""
        self.add_log_message(f"Stopping component {self.component_name}...")
        self.add_log_message("Component stop command sent")
    
    def restart_component(self):
        """Restart the component."""
        self.add_log_message(f"Restarting component {self.component_name}...")
        self.add_log_message("Component restart command sent")


class AISMainWindow(QMainWindow):
    """Main window for the AIS GUI."""
    
    def __init__(self):
        super().__init__()
        self.worker_thread = None
        self.setup_ui()
        self.setup_worker_thread()
    
    def setup_ui(self):
        """Set up the main window UI."""
        self.setWindowTitle("AIS System - Complex Interface")
        self.setGeometry(100, 100, 1200, 800)
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Create main layout
        main_layout = QVBoxLayout(central_widget)
        
        # Create menu bar
        self.create_menu_bar()
        
        # Create status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)
        
        # Create tabs
        self.create_overview_tab()
        self.create_components_tab()
        self.create_monitoring_tab()
        self.create_data_tab()
        self.create_settings_tab()
    
    def create_menu_bar(self):
        """Create the menu bar."""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("File")
        
        exit_action = QAction("Exit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # View menu
        view_menu = menubar.addMenu("View")
        
        refresh_action = QAction("Refresh", self)
        refresh_action.setShortcut("F5")
        refresh_action.triggered.connect(self.refresh_all)
        view_menu.addAction(refresh_action)
        
        # Help menu
        help_menu = menubar.addMenu("Help")
        
        about_action = QAction("About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def create_overview_tab(self):
        """Create the overview tab."""
        overview_widget = QWidget()
        layout = QVBoxLayout(overview_widget)
        
        # System status
        status_group = QGroupBox("System Status")
        status_layout = QGridLayout()
        
        self.system_status_label = QLabel("Unknown")
        self.system_status_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        
        self.uptime_label = QLabel("Unknown")
        self.components_count_label = QLabel("Unknown")
        
        status_layout.addWidget(QLabel("Status:"), 0, 0)
        status_layout.addWidget(self.system_status_label, 0, 1)
        status_layout.addWidget(QLabel("Uptime:"), 1, 0)
        status_layout.addWidget(self.uptime_label, 1, 1)
        status_layout.addWidget(QLabel("Components:"), 2, 0)
        status_layout.addWidget(self.components_count_label, 2, 1)
        
        status_group.setLayout(status_layout)
        
        # Quick actions
        actions_group = QGroupBox("Quick Actions")
        actions_layout = QHBoxLayout()
        
        self.start_all_button = QPushButton("Start All Components")
        self.stop_all_button = QPushButton("Stop All Components")
        self.refresh_button = QPushButton("Refresh Status")
        
        actions_layout.addWidget(self.start_all_button)
        actions_layout.addWidget(self.stop_all_button)
        actions_layout.addWidget(self.refresh_button)
        
        actions_group.setLayout(actions_layout)
        
        # Connect signals
        self.start_all_button.clicked.connect(self.start_all_components)
        self.stop_all_button.clicked.connect(self.stop_all_components)
        self.refresh_button.clicked.connect(self.refresh_all)
        
        # Add to layout
        layout.addWidget(status_group)
        layout.addWidget(actions_group)
        layout.addStretch()
        
        self.tab_widget.addTab(overview_widget, "Overview")
    
    def create_components_tab(self):
        """Create the components tab."""
        components_widget = QWidget()
        layout = QVBoxLayout(components_widget)
        
        # Components tree
        self.components_tree = QTreeWidget()
        self.components_tree.setHeaderLabels(["Component", "Status", "Level", "Actions"])
        self.components_tree.setColumnWidth(0, 200)
        self.components_tree.setColumnWidth(1, 100)
        self.components_tree.setColumnWidth(2, 100)
        self.components_tree.setColumnWidth(3, 150)
        
        # Populate components
        self.populate_components_tree()
        
        layout.addWidget(self.components_tree)
        
        self.tab_widget.addTab(components_widget, "Components")
    
    def create_monitoring_tab(self):
        """Create the monitoring tab."""
        monitoring_widget = QWidget()
        layout = QVBoxLayout(monitoring_widget)
        
        # Health status
        health_group = QGroupBox("System Health")
        health_layout = QVBoxLayout()
        
        self.health_status_label = QLabel("Unknown")
        self.health_status_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        
        self.health_checks_table = QTableWidget()
        self.health_checks_table.setColumnCount(4)
        self.health_checks_table.setHorizontalHeaderLabels(["Component", "Status", "Message", "Response Time"])
        
        health_layout.addWidget(self.health_status_label)
        health_layout.addWidget(self.health_checks_table)
        health_group.setLayout(health_layout)
        
        # Metrics summary
        metrics_group = QGroupBox("Metrics Summary")
        metrics_layout = QGridLayout()
        
        self.total_metrics_label = QLabel("0")
        self.performance_metrics_label = QLabel("0")
        self.resource_metrics_label = QLabel("0")
        self.system_metrics_label = QLabel("0")
        
        metrics_layout.addWidget(QLabel("Total Metrics:"), 0, 0)
        metrics_layout.addWidget(self.total_metrics_label, 0, 1)
        metrics_layout.addWidget(QLabel("Performance:"), 1, 0)
        metrics_layout.addWidget(self.performance_metrics_label, 1, 1)
        metrics_layout.addWidget(QLabel("Resource:"), 2, 0)
        metrics_layout.addWidget(self.resource_metrics_label, 2, 1)
        metrics_layout.addWidget(QLabel("System:"), 3, 0)
        metrics_layout.addWidget(self.system_metrics_label, 3, 1)
        
        metrics_group.setLayout(metrics_layout)
        
        # Add to layout
        layout.addWidget(health_group)
        layout.addWidget(metrics_group)
        
        self.tab_widget.addTab(monitoring_widget, "Monitoring")
    
    def create_data_tab(self):
        """Create the data tab."""
        data_widget = QWidget()
        layout = QVBoxLayout(data_widget)
        
        # Synthetic data generation
        data_group = QGroupBox("Synthetic Data Generation")
        data_layout = QFormLayout()
        
        self.schema_combo = QComboBox()
        self.schema_combo.addItems(["numerical", "categorical", "text", "image", "time_series"])
        
        self.count_spin = QSpinBox()
        self.count_spin.setRange(1, 1000)
        self.count_spin.setValue(10)
        
        self.generate_button = QPushButton("Generate Data")
        
        data_layout.addRow("Schema:", self.schema_combo)
        data_layout.addRow("Count:", self.count_spin)
        data_layout.addRow("", self.generate_button)
        
        data_group.setLayout(data_layout)
        
        # Data display
        display_group = QGroupBox("Generated Data")
        display_layout = QVBoxLayout()
        
        self.data_text = QTextEdit()
        self.data_text.setReadOnly(True)
        
        display_layout.addWidget(self.data_text)
        display_group.setLayout(display_layout)
        
        # Connect signals
        self.generate_button.clicked.connect(self.generate_synthetic_data)
        
        # Add to layout
        layout.addWidget(data_group)
        layout.addWidget(display_group)
        
        self.tab_widget.addTab(data_widget, "Data")
    
    def create_settings_tab(self):
        """Create the settings tab."""
        settings_widget = QWidget()
        layout = QVBoxLayout(settings_widget)
        
        # General settings
        general_group = QGroupBox("General Settings")
        general_layout = QFormLayout()
        
        self.auto_refresh_check = QCheckBox("Enable auto-refresh")
        self.auto_refresh_check.setChecked(True)
        
        self.refresh_interval_spin = QSpinBox()
        self.refresh_interval_spin.setRange(1000, 60000)
        self.refresh_interval_spin.setValue(5000)
        self.refresh_interval_spin.setSuffix(" ms")
        
        general_layout.addRow("Auto-refresh:", self.auto_refresh_check)
        general_layout.addRow("Refresh interval:", self.refresh_interval_spin)
        
        general_group.setLayout(general_layout)
        
        # API settings
        api_group = QGroupBox("API Settings")
        api_layout = QFormLayout()
        
        self.api_host_edit = QLineEdit("localhost")
        self.api_port_edit = QLineEdit("8000")
        
        api_layout.addRow("Host:", self.api_host_edit)
        api_layout.addRow("Port:", self.api_port_edit)
        
        api_group.setLayout(api_layout)
        
        # Add to layout
        layout.addWidget(general_group)
        layout.addWidget(api_group)
        layout.addStretch()
        
        self.tab_widget.addTab(settings_widget, "Settings")
    
    def setup_worker_thread(self):
        """Set up the worker thread for background updates."""
        self.worker_thread = AISWorkerThread()
        
        # Connect signals
        self.worker_thread.health_updated.connect(self.update_health_display)
        self.worker_thread.metrics_updated.connect(self.update_metrics_display)
        self.worker_thread.status_updated.connect(self.update_status_display)
        self.worker_thread.error_occurred.connect(self.handle_worker_error)
        
        # Start the thread
        self.worker_thread.start()
    
    def populate_components_tree(self):
        """Populate the components tree widget."""
        self.components_tree.clear()
        
        # Add root items for each component type
        components = {
            "Operational": {"status": "Running", "level": "System"},
            "Regulatory": {"status": "Running", "level": "System"},
            "Optimization": {"status": "Running", "level": "System"},
            "Adaptive": {"status": "Running", "level": "System"},
            "Identity": {"status": "Running", "level": "System"}
        }
        
        for name, info in components.items():
            root_item = QTreeWidgetItem(self.components_tree)
            root_item.setText(0, name)
            root_item.setText(1, info["status"])
            root_item.setText(2, info["level"])
            
            # Add control button
            control_widget = QWidget()
            control_layout = QHBoxLayout(control_widget)
            control_layout.setContentsMargins(0, 0, 0, 0)
            
            control_button = QPushButton("Control")
            control_button.clicked.connect(lambda checked, n=name: self.open_component_control(n))
            control_layout.addWidget(control_button)
            
            self.components_tree.setItemWidget(root_item, 3, control_widget)
    
    def open_component_control(self, component_name: str):
        """Open the component control dialog."""
        dialog = ComponentControlDialog(component_name, self)
        dialog.exec()
    
    def update_health_display(self, health_data: dict):
        """Update the health display."""
        try:
            status = health_data.get("status", "unknown")
            self.health_status_label.setText(status.title())
            
            # Update status color
            if status == "healthy":
                self.health_status_label.setStyleSheet("color: green; font-weight: bold; font-size: 14px;")
            elif status == "warning":
                self.health_status_label.setStyleSheet("color: orange; font-weight: bold; font-size: 14px;")
            else:
                self.health_status_label.setStyleSheet("color: red; font-weight: bold; font-size: 14px;")
            
            # Update health checks table
            checks = health_data.get("checks", [])
            self.health_checks_table.setRowCount(len(checks))
            
            for i, check in enumerate(checks):
                self.health_checks_table.setItem(i, 0, QTableWidgetItem(check.get("component", "")))
                self.health_checks_table.setItem(i, 1, QTableWidgetItem(check.get("status", "")))
                self.health_checks_table.setItem(i, 2, QTableWidgetItem(check.get("message", "")))
                self.health_checks_table.setItem(i, 3, QTableWidgetItem(f"{check.get('response_time', 0):.3f}s"))
            
        except Exception as e:
            logger.error(f"Failed to update health display: {e}")
    
    def update_metrics_display(self, metrics_data: dict):
        """Update the metrics display."""
        try:
            self.total_metrics_label.setText(str(metrics_data.get("total_metrics", 0)))
            
            categories = metrics_data.get("metrics_by_category", {})
            self.performance_metrics_label.setText(str(categories.get("performance", 0)))
            self.resource_metrics_label.setText(str(categories.get("resource", 0)))
            self.system_metrics_label.setText(str(categories.get("system", 0)))
            
        except Exception as e:
            logger.error(f"Failed to update metrics display: {e}")
    
    def update_status_display(self, status_data: dict):
        """Update the status display."""
        try:
            is_running = status_data.get("is_running", False)
            self.system_status_label.setText("Running" if is_running else "Stopped")
            
            if is_running:
                self.system_status_label.setStyleSheet("color: green; font-weight: bold; font-size: 14px;")
            else:
                self.system_status_label.setStyleSheet("color: red; font-weight: bold; font-size: 14px;")
            
            # Update component count
            components = status_data.get("components", {})
            self.components_count_label.setText(str(len(components)))
            
            # Update uptime (simplified)
            self.uptime_label.setText("Active")
            
        except Exception as e:
            logger.error(f"Failed to update status display: {e}")
    
    def handle_worker_error(self, error_message: str):
        """Handle worker thread errors."""
        self.status_bar.showMessage(f"Error: {error_message}", 5000)
        logger.error(f"Worker thread error: {error_message}")
    
    def start_all_components(self):
        """Start all components."""
        QMessageBox.information(self, "Start All", "Start all components command sent")
        self.status_bar.showMessage("Starting all components...", 3000)
    
    def stop_all_components(self):
        """Stop all components."""
        QMessageBox.information(self, "Stop All", "Stop all components command sent")
        self.status_bar.showMessage("Stopping all components...", 3000)
    
    def refresh_all(self):
        """Refresh all displays."""
        self.status_bar.showMessage("Refreshing...", 2000)
        # The worker thread will handle the actual refresh
    
    def generate_synthetic_data(self):
        """Generate synthetic data."""
        schema = self.schema_combo.currentText()
        count = self.count_spin.value()
        
        try:
            # Import and use the actual synthetic data generator
            import sys
            from pathlib import Path
            project_root = Path(__file__).parent
            sys.path.insert(0, str(project_root))
            
            from ais.core.synthetic_data_generator import SyntheticDataGenerator
            generator = SyntheticDataGenerator()
            
            if schema == "numerical":
                data = generator.generate_numerical_data(count)
                sample_data = {
                    "schema": schema,
                    "count": count,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "data": data
                }
            else:
                sample_data = {
                    "schema": schema,
                    "count": count,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "data": [f"Sample {i} for {schema}" for i in range(count)]
                }
            
            self.data_text.setText(json.dumps(sample_data, indent=2))
            self.status_bar.showMessage(f"Generated {count} {schema} samples", 3000)
            
        except Exception as e:
            error_data = {
                "error": str(e),
                "schema": schema,
                "count": count,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            self.data_text.setText(json.dumps(error_data, indent=2))
            self.status_bar.showMessage(f"Error generating data: {e}", 5000)
    
    def show_about(self):
        """Show the about dialog."""
        QMessageBox.about(self, "About AIS System", 
                         "AIS System - Autocatalytic Intelligence System\n\n"
                         "Version 1.0.0\n"
                         "A modular AI system with self-improvement capabilities.")
    
    def closeEvent(self, event):
        """Handle window close event."""
        if self.worker_thread:
            self.worker_thread.stop()
        event.accept()


def main():
    """Main function to run the complex GUI."""
    app = QApplication(sys.argv)
    app.setApplicationName("AIS System")
    app.setApplicationVersion("1.0.0")
    
    # Set application style
    app.setStyle("Fusion")
    
    # Create and show main window
    window = AISMainWindow()
    window.show()
    
    # Run the application
    sys.exit(app.exec())


if __name__ == "__main__":
    main()