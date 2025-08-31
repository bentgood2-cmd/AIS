# 🚀 AIS System - Run Instructions

## 🎯 Quick Start

The AIS (Autocatalytic Intelligence System) is now ready to run! Here are the different ways to start the system:

### **Option 1: Use the System Launcher (Recommended)**

#### **Windows Users:**
- **Double-click** `run_ais_system.bat` (Batch file)
- **Right-click** `run_ais_system.ps1` → "Run with PowerShell" (PowerShell script)

#### **All Platforms:**
```bash
python run_ais_system.py
```

The launcher provides a menu with these options:
1. 🧠 **Run Complete AIS System** - All components running together
2. 🌐 **Run Web API Server** - FastAPI server on http://localhost:8000
3. 🖥️ **Run GUI Interface** - PyQt6 graphical interface
4. 🧪 **Run System Tests** - Verify everything is working
5. 📊 **Run Health Check** - Comprehensive system diagnostics
6. 🔧 **Run Setup/Installation** - Install missing dependencies
7. 📚 **Show System Information** - Display system status
8. 🚪 **Exit**

### **Option 2: Direct Component Execution**

#### **Run the Main AIS System:**
```bash
python ais/main.py
```

#### **Run the Web API:**
```bash
python app.py
```

#### **Run the GUI:**
```bash
python gui.py
```

#### **Run Tests:**
```bash
python test_refactored_ais.py
```

## 🔧 System Requirements

- **Python**: 3.8 or higher
- **Dependencies**: All required packages are automatically installed
- **Platform**: Windows, macOS, or Linux

## 📋 What's Included

The AIS system consists of these core components:

### **🧠 Core Components**
- **Operational Component**: Resource management and task queuing
- **Regulatory Component**: Governance and compliance rules
- **Optimization Component**: System performance optimization
- **Adaptive Component**: Self-learning and adaptation
- **Identity Component**: System self-awareness and consciousness

### **🛠️ Supporting Systems**
- **Synthetic Data Generator**: Creates test data for all types
- **Web API**: RESTful interface for programmatic access
- **GUI Interface**: Graphical user interface for management
- **Health Monitoring**: System diagnostics and metrics
- **Logging**: Comprehensive logging and audit trails

## 🌐 Web API Access

When running the web API, you can access:

- **API Documentation**: http://localhost:8000/docs
- **System Status**: http://localhost:8000/status
- **Health Check**: http://localhost:8000/health
- **Metrics**: http://localhost:8000/metrics
- **Synthetic Data**: http://localhost:8000/synthetic-data

## 🧪 Testing the System

The system includes comprehensive tests:

```bash
python test_refactored_ais.py
```

This will test:
- ✅ Base component creation and initialization
- ✅ Synthetic data generation capabilities
- ✅ Complete system integration
- ✅ Component lifecycle management

## 🚨 Troubleshooting

### **Python Not Found**
- Install Python 3.8+ from [python.org](https://python.org)
- Ensure Python is added to your PATH

### **Missing Dependencies**
- Run the launcher and select option 6 (Setup/Installation)
- Or manually run: `pip install -r requirements.txt`

### **Import Errors**
- Ensure you're running from the project root directory
- Check that all Python files are present in the `ais/` directory

### **Permission Errors**
- On Windows, try running as Administrator
- On Linux/macOS, check file permissions

## 📁 File Structure

```
AIS_Project/
├── run_ais_system.py          # Main launcher (Python)
├── run_ais_system.bat         # Windows batch launcher
├── run_ais_system.ps1         # Windows PowerShell launcher
├── ais/                       # Core AIS system
│   ├── main.py               # Main orchestrator
│   └── core/                 # Core components
│       ├── base.py           # Base classes
│       ├── operational.py    # Resource management
│       ├── regulatory.py     # Governance
│       ├── optimization.py   # Optimization
│       ├── adaptive.py       # Adaptation
│       ├── identity.py       # Self-awareness
│       ├── models.py         # AI/ML models
│       └── synthetic_data_generator.py
├── app.py                     # Web API server
├── gui.py                     # Graphical interface
├── health.py                  # Health monitoring
├── metrics.py                 # Metrics collection
├── test_refactored_ais.py     # Test suite
└── requirements.txt            # Python dependencies
```

## 🎉 Success Indicators

When the system is running correctly, you should see:

- ✅ All components initialized successfully
- ✅ System status showing "running" or "active"
- ✅ No error messages in the console
- ✅ Web API accessible at http://localhost:8000
- ✅ GUI window displaying system information

## 🔄 Stopping the System

- **Launcher**: Select option 8 (Exit) or press Ctrl+C
- **Direct execution**: Press Ctrl+C in the terminal
- **GUI**: Close the window
- **Web API**: Press Ctrl+C in the terminal

## 📞 Support

If you encounter issues:

1. **Run the health check** (option 5 in launcher)
2. **Check system information** (option 7 in launcher)
3. **Run the test suite** (option 4 in launcher)
4. **Review the logs** for error details

---

**🎯 The AIS system is now ready to run! Use the launcher for the best experience.**
