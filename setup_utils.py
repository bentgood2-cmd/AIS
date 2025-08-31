"""
Utility classes and functions for the AIS setup system.
"""

import os
import sys
import time
import platform
import shutil
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import re

logger = logging.getLogger(__name__)

def sanitize_for_logging(value: str) -> str:
    """Sanitize string for safe logging."""
    if not isinstance(value, str):
        value = str(value)
    return re.sub(r'[\r\n\x00-\x1f\x7f-\x9f]', '_', value)

@dataclass
class ValidationResult:
    """Result of a validation check."""
    passed: bool
    message: str
    details: Optional[Dict[str, Any]] = None

class SetupValidator:
    """Validates system requirements for AIS setup."""
    
    def __init__(self):
        self.logger = logger
    
    def validate_python_version(self, min_version: tuple = (3, 8)) -> ValidationResult:
        """Validate Python version."""
        try:
            current_version = sys.version_info[:2]
            if current_version >= min_version:
                return ValidationResult(
                    passed=True,
                    message=f"Python version {'.'.join(map(str, current_version))} meets requirements",
                    details={"current": current_version, "required": min_version}
                )
            else:
                return ValidationResult(
                    passed=False,
                    message=f"Python {'.'.join(map(str, min_version))}+ required, found {'.'.join(map(str, current_version))}",
                    details={"current": current_version, "required": min_version}
                )
        except Exception as e:
            return ValidationResult(
                passed=False,
                message=f"Failed to check Python version: {sanitize_for_logging(str(e))}"
            )
    
    def validate_disk_space(self, required_gb: float = 1.0) -> ValidationResult:
        """Validate available disk space."""
        try:
            free_bytes = shutil.disk_usage('.').free
            free_gb = free_bytes / (1024**3)
            
            if free_gb >= required_gb:
                return ValidationResult(
                    passed=True,
                    message=f"Sufficient disk space: {free_gb:.1f}GB available",
                    details={"available_gb": free_gb, "required_gb": required_gb}
                )
            else:
                return ValidationResult(
                    passed=False,
                    message=f"Insufficient disk space: {free_gb:.1f}GB available, {required_gb}GB required",
                    details={"available_gb": free_gb, "required_gb": required_gb}
                )
        except Exception as e:
            return ValidationResult(
                passed=False,
                message=f"Failed to check disk space: {sanitize_for_logging(str(e))}"
            )
    
    def validate_write_permissions(self, path: Path = None) -> ValidationResult:
        """Validate write permissions."""
        try:
            test_path = path or Path('.')
            test_file = test_path / '.ais_write_test'
            
            # Try to create and delete a test file
            test_file.write_text('test')
            test_file.unlink()
            
            return ValidationResult(
                passed=True,
                message=f"Write permissions verified for {test_path}",
                details={"path": str(test_path)}
            )
        except Exception as e:
            return ValidationResult(
                passed=False,
                message=f"No write permissions for {test_path}: {sanitize_for_logging(str(e))}",
                details={"path": str(test_path)}
            )
    
    def validate_all(self) -> List[ValidationResult]:
        """Run all validation checks."""
        results = []
        results.append(self.validate_python_version())
        results.append(self.validate_disk_space())
        results.append(self.validate_write_permissions())
        return results

class ProgressTracker:
    """Tracks setup progress."""
    
    def __init__(self, total_steps: int):
        self.total_steps = total_steps
        self.completed_steps = 0
        self.current_step = ""
        self.step_times: Dict[str, float] = {}
        self.start_time = time.time()
        self.logger = logger
    
    def add_step(self, step_name: str) -> None:
        """Add a step to track."""
        self.step_times[step_name] = 0.0
    
    def start_step(self, step_name: str) -> None:
        """Start tracking a step."""
        self.current_step = step_name
        self.step_times[step_name] = time.time()
        sanitized_name = sanitize_for_logging(step_name)
        self.logger.info("Starting step: %s", sanitized_name)
    
    def complete_step(self, step_name: str) -> None:
        """Complete a step."""
        if step_name in self.step_times:
            duration = time.time() - self.step_times[step_name]
            self.step_times[step_name] = duration
            self.completed_steps += 1
            
            sanitized_name = sanitize_for_logging(step_name)
            self.logger.info(f"Completed step: {sanitized_name} ({duration:.2f}s)")
    
    def get_progress(self) -> float:
        """Get progress percentage."""
        if self.total_steps == 0:
            return 100.0
        return (self.completed_steps / self.total_steps) * 100.0
    
    def get_eta(self) -> Optional[float]:
        """Get estimated time to completion."""
        if self.completed_steps == 0:
            return None
        
        elapsed = time.time() - self.start_time
        avg_time_per_step = elapsed / self.completed_steps
        remaining_steps = self.total_steps - self.completed_steps
        
        return remaining_steps * avg_time_per_step
    
    def get_summary(self) -> Dict[str, Any]:
        """Get progress summary."""
        return {
            "total_steps": self.total_steps,
            "completed_steps": self.completed_steps,
            "progress_percent": self.get_progress(),
            "current_step": self.current_step,
            "elapsed_time": time.time() - self.start_time,
            "eta": self.get_eta(),
            "step_times": self.step_times.copy()
        }

class ErrorHandler:
    """Handles and reports setup errors."""
    
    def __init__(self):
        self.errors: List[Dict[str, Any]] = []
        self.warnings: List[Dict[str, Any]] = []
        self.logger = logger
    
    def add_error(self, error: Exception, context: str = "") -> None:
        """Add an error."""
        error_info = {
            "type": type(error).__name__,
            "message": str(error),
            "context": context,
            "timestamp": time.time()
        }
        self.errors.append(error_info)
        
        sanitized_context = sanitize_for_logging(context)
        sanitized_message = sanitize_for_logging(str(error))
        self.logger.error(f"Error in {sanitized_context}: {sanitized_message}")
    
    def add_warning(self, message: str, context: str = "") -> None:
        """Add a warning."""
        warning_info = {
            "message": message,
            "context": context,
            "timestamp": time.time()
        }
        self.warnings.append(warning_info)
        
        sanitized_context = sanitize_for_logging(context)
        sanitized_message = sanitize_for_logging(message)
        self.logger.warning(f"Warning in {sanitized_context}: {sanitized_message}")
    
    def has_errors(self) -> bool:
        """Check if there are any errors."""
        return len(self.errors) > 0
    
    def has_warnings(self) -> bool:
        """Check if there are any warnings."""
        return len(self.warnings) > 0
    
    def get_error_report(self) -> Dict[str, Any]:
        """Get error report."""
        return {
            "error_count": len(self.errors),
            "warning_count": len(self.warnings),
            "errors": self.errors,
            "warnings": self.warnings
        }
    
    def clear(self) -> None:
        """Clear all errors and warnings."""
        self.errors.clear()
        self.warnings.clear()

class SystemInfo:
    """Provides system information."""
    
    @staticmethod
    def get_system_info() -> Dict[str, Any]:
        """Get comprehensive system information."""
        try:
            return {
                "platform": platform.system(),
                "platform_release": platform.release(),
                "platform_version": platform.version(),
                "architecture": platform.machine(),
                "processor": platform.processor(),
                "python_version": platform.python_version(),
                "python_implementation": platform.python_implementation(),
                "hostname": platform.node(),
                "current_directory": str(Path.cwd()),
                "home_directory": str(Path.home()),
                "environment_variables": dict(os.environ)
            }
        except Exception as e:
            logger.error(f"Failed to get system info: {sanitize_for_logging(str(e))}")
            return {"error": str(e)}
    
    @staticmethod
    def get_python_info() -> Dict[str, Any]:
        """Get Python-specific information."""
        try:
            return {
                "version": sys.version,
                "version_info": sys.version_info,
                "executable": sys.executable,
                "path": sys.path,
                "platform": sys.platform,
                "modules": list(sys.modules.keys())
            }
        except Exception as e:
            logger.error(f"Failed to get Python info: {sanitize_for_logging(str(e))}")
            return {"error": str(e)}
    
    @staticmethod
    def get_disk_info() -> Dict[str, Any]:
        """Get disk usage information."""
        try:
            usage = shutil.disk_usage('.')
            return {
                "total_bytes": usage.total,
                "used_bytes": usage.used,
                "free_bytes": usage.free,
                "total_gb": usage.total / (1024**3),
                "used_gb": usage.used / (1024**3),
                "free_gb": usage.free / (1024**3),
                "usage_percent": (usage.used / usage.total) * 100
            }
        except Exception as e:
            logger.error(f"Failed to get disk info: {sanitize_for_logging(str(e))}")
            return {"error": str(e)}