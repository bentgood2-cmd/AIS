# AIS v3.2.1 Setup System

A comprehensive, refactored setup system for the Autocatalytic Intelligence System (AIS) v3.2.1.

## Overview

This setup system has been refactored to provide:
- **Modular Architecture**: Clean separation of concerns with dedicated classes for different responsibilities
- **Configuration Management**: Externalized configuration for easy maintenance
- **Error Handling**: Robust error handling with detailed reporting
- **Progress Tracking**: Visual progress indication during setup
- **System Validation**: Pre-flight checks for system requirements
- **CLI Interface**: Command-line options for customization

## Architecture

### Core Components

1. **`setup_ais.py`** - Main setup orchestrator
2. **`setup_config.py`** - Configuration constants and file templates
3. **`setup_utils.py`** - Utility functions and helper classes

### Class Structure

```
AISSetup (Main Orchestrator)
├── DirectoryManager (Directory operations)
├── FileGenerator (File creation)
├── DependencyManager (Package installation)
└── SetupConfig (Configuration)

SetupValidator (System checks)
ProgressTracker (Progress monitoring)
ErrorHandler (Error management)
SystemInfo (System information)
```

## Features

### ✅ Pre-flight Validation
- Python version compatibility check
- Disk space verification
- Write permissions validation
- Network connectivity testing

### ✅ Progress Tracking
- Step-by-step progress indication
- Percentage completion display
- Detailed logging of each operation

### ✅ Error Handling
- Graceful error recovery
- Detailed error reports
- Context-aware error messages
- Backup creation before destructive operations

### ✅ Configuration Options
- Cleanup existing installations
- Skip dependency installation
- Skip file generation
- Verbose logging
- Custom base directory

## Usage

### Basic Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Run setup
python setup_ais.py

# Test the system
python test_basic.py

# Start the AIS server
python start_ais.py
```

### Advanced Options

```bash
# Skip cleanup of existing installation
python setup_ais.py --no-cleanup

# Skip dependency installation
python setup_ais.py --no-deps

# Skip file generation
python setup_ais.py --no-files

# Enable verbose logging
python setup_ais.py --verbose

# Custom installation directory
python setup_ais.py --base-dir /path/to/install
```

### Command Line Arguments

| Argument | Description | Default |
|----------|-------------|---------|
| `--no-cleanup` | Skip cleanup of existing installation | False |
| `--no-deps` | Skip dependency installation | False |
| `--no-files` | Skip file generation | False |
| `--verbose, -v` | Enable verbose logging | False |
| `--base-dir` | Custom base directory | Current directory |

## Directory Structure

The setup creates the following directory structure:

```
ais/
├── core/           # Core AIS components
├── api/            # API endpoints
│   └── routes/     # Route definitions
├── utils/          # Utility functions
└── data_manager/   # Data management

config/             # Configuration files
docker/             # Docker configuration
│   └── nginx/      # Nginx configuration
kubernetes/         # Kubernetes manifests
src/                # Source code
│   ├── api/        # API source
│   ├── services/   # Service layer
│   ├── stores/     # State management
│   ├── hooks/      # React hooks
│   ├── components/ # UI components
│   └── pages/      # Page components

checkpoints/        # Model checkpoints
tests/              # Test files
```

## Dependencies

The setup installs a comprehensive set of dependencies including:

- **Web Framework**: FastAPI, Uvicorn
- **Data Processing**: PyTorch, NumPy, Pandas, Scikit-learn
- **Machine Learning**: Transformers, Accelerate, TensorBoard
- **Development Tools**: Pytest, Black, Flake8, MyPy
- **GUI**: PyQt6, PyOpenGL
- **Infrastructure**: Docker, Kubernetes support

## Logging

Setup progress and errors are logged to `setup_ais.log` with the following levels:

- **INFO**: General progress information
- **WARNING**: Non-critical issues
- **ERROR**: Critical errors that may affect setup
- **DEBUG**: Detailed information (when verbose mode is enabled)

## Error Handling

The system provides comprehensive error handling:

1. **System Validation Errors**: Clear messages about missing requirements
2. **Permission Errors**: Guidance on elevated privileges
3. **Network Errors**: Connectivity troubleshooting tips
4. **Disk Space Errors**: Space requirement information
5. **Installation Errors**: Detailed error reports with context

## Backup and Recovery

Before performing destructive operations (like cleanup), the system:

1. Creates automatic backups with timestamps
2. Provides rollback capabilities
3. Logs all backup operations
4. Cleans up backups after successful operations

## System Requirements

- **Python**: 3.8 or higher
- **Disk Space**: Minimum 1GB free space
- **Permissions**: Write access to target directory
- **Network**: Internet connection for dependency installation

## Troubleshooting

### Common Issues

1. **Permission Denied**
   - Run with elevated privileges (admin/sudo)
   - Check directory permissions

2. **Network Issues**
   - Verify internet connectivity
   - Check firewall settings
   - Try using a different network

3. **Disk Space**
   - Free up space on target drive
   - Use `--base-dir` to specify different location

4. **Python Version**
   - Upgrade to Python 3.8+
   - Use virtual environment if needed

### Getting Help

- Check the log file: `setup_ais.log`
- Enable verbose mode: `--verbose`
- Review system information in logs
- Check error reports for specific issues

## Development

### Adding New Components

1. **New Directory**: Add to `DIRECTORIES` in `setup_config.py`
2. **New File**: Add template to `FILE_TEMPLATES` in `setup_config.py`
3. **New Dependency**: Add to `REQUIREMENTS` in `setup_config.py`

### Extending Functionality

- Inherit from existing manager classes
- Add new validation methods to `SetupValidator`
- Extend error handling in `ErrorHandler`
- Add new progress tracking steps

## License

This setup system is part of the AIS v3.2.1 project.

## Contributing

When contributing to the setup system:

1. Maintain the modular architecture
2. Add comprehensive error handling
3. Include progress tracking for new operations
4. Update documentation for new features
5. Add tests for new functionality
