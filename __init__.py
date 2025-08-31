"""
AIS System - Autocatalytic Intelligence System

A modular AI system with self-improvement capabilities, featuring:
- Core components for operational, regulatory, optimization, adaptive, and identity management
- Synthetic data generation and management
- Health monitoring and metrics collection
- Web API interface
- GUI interface (when PyQt6 is available)
- Comprehensive testing framework

Version: 1.0.0
"""

__version__ = "1.0.0"
__author__ = "AIS Development Team"
__description__ = "Autocatalytic Intelligence System"

# Import core components
try:
    from .ais.core.base import (
        SystemLevel,
        ComponentStatus,
        BaseComponent,
        create_component
    )
    
    from .ais.core.operational import OperationalComponent
    from .ais.core.regulatory import RegulatoryComponent
    from .ais.core.optimization import OptimizationComponent
    from .ais.core.adaptive import AdaptiveComponent
    from .ais.core.identity import IdentityComponent
    
    from .ais.core.synthetic_data_generator import SyntheticDataGenerator
    
    from .ais.core.models import (
        CNNPreprocessor,
        RLAgent,
        BayesianOptimizer,
        DarwinGoedelMachine,
        EthicalTransformer
    )
    
    # Import monitoring modules
    from .health import get_system_health, get_health_summary, HealthMonitor
    from .metrics import (
        MetricsCollector,
        MetricsMiddleware,
        record_metric,
        increment_counter,
        set_gauge,
        get_metric_summary,
        get_all_metrics
    )
    
    # Import main application
    from .app import AISSystem
    
    # Import GUI if available
    try:
        from .gui import AISMainWindow
        GUI_AVAILABLE = True
    except ImportError:
        GUI_AVAILABLE = False
    
    # Core exports
    __all__ = [
        # Core classes
        'SystemLevel',
        'ComponentStatus',
        'BaseComponent',
        'create_component',
        'OperationalComponent',
        'RegulatoryComponent',
        'OptimizationComponent',
        'AdaptiveComponent',
        'IdentityComponent',
        'SyntheticDataGenerator',
        
        # AI/ML Models
        'CNNPreprocessor',
        'RLAgent',
        'BayesianOptimizer',
        'DarwinGoedelMachine',
        'EthicalTransformer',
        
        # Monitoring
        'HealthMonitor',
        'get_system_health',
        'get_health_summary',
        'MetricsCollector',
        'MetricsMiddleware',
        'record_metric',
        'increment_counter',
        'set_gauge',
        'get_metric_summary',
        'get_all_metrics',
        
        # Main system
        'AISSystem',
        
        # GUI
        'AISMainWindow',
        'GUI_AVAILABLE',
        
        # Version info
        '__version__',
        '__author__',
        '__description__'
    ]
    
except ImportError as e:
    # If core components can't be imported, provide minimal exports
    __all__ = [
        '__version__',
        '__author__',
        '__description__'
    ]
    
    import warnings
    warnings.warn(f"Some AIS components could not be imported: {e}", ImportWarning)


def get_system_info():
    """Get system information."""
    return {
        "version": __version__,
        "author": __author__,
        "description": __description__,
        "gui_available": globals().get('GUI_AVAILABLE', False),
        "components_loaded": 'BaseComponent' in globals()
    }


def run_demo():
    """Run a demonstration of the AIS system."""
    try:
        print("AIS System Demo")
        print("=" * 50)
        print(f"Version: {__version__}")
        print(f"Description: {__description__}")
        print(f"GUI Available: {globals().get('GUI_AVAILABLE', False)}")
        print(f"Components Loaded: {'BaseComponent' in globals()}")
        
        if 'BaseComponent' in globals():
            print("\nCore components are available!")
            print("You can now:")
            print("- Create components using create_component()")
            print("- Monitor system health using get_system_health()")
            print("- Collect metrics using record_metric()")
            print("- Run the web API using app.py")
            print("- Run the GUI using gui.py (if PyQt6 is available)")
        
        print("\nDemo completed successfully!")
        
    except Exception as e:
        print(f"Demo failed: {e}")


if __name__ == "__main__":
    run_demo()
