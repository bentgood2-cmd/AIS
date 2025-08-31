"""
Health monitoring module for the AIS system.
Provides system health checks and monitoring capabilities.
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import psutil
import platform

logger = logging.getLogger(__name__)

class HealthStatus(Enum):
    """Health status enumeration."""
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"

@dataclass
class HealthCheck:
    """Individual health check result."""
    component: str
    status: HealthStatus
    message: str
    response_time: float
    details: Optional[Dict[str, Any]] = None

@dataclass
class SystemHealth:
    """Overall system health status."""
    overall_status: HealthStatus
    timestamp: datetime
    uptime: timedelta
    checks: List[HealthCheck]

class HealthMonitor:
    """System health monitor."""
    
    def __init__(self):
        self.start_time = time.time()
        self.logger = logger
    
    def get_uptime(self) -> float:
        """Get system uptime in seconds."""
        return time.time() - self.start_time
    
    async def get_system_health(self) -> SystemHealth:
        """Get comprehensive system health status."""
        checks = []
        
        # CPU check
        checks.append(await self._check_cpu())
        
        # Memory check
        checks.append(await self._check_memory())
        
        # Disk check
        checks.append(await self._check_disk())
        
        # Network check
        checks.append(await self._check_network())
        
        # Process check
        checks.append(await self._check_processes())
        
        # Determine overall status
        overall_status = self._determine_overall_status(checks)
        
        return SystemHealth(
            overall_status=overall_status,
            timestamp=datetime.now(timezone.utc),
            uptime=timedelta(seconds=self.get_uptime()),
            checks=checks
        )
    
    async def _check_cpu(self) -> HealthCheck:
        """Check CPU health."""
        start_time = time.time()
        
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            response_time = time.time() - start_time
            
            if cpu_percent < 80:
                status = HealthStatus.HEALTHY
                message = f"CPU usage normal: {cpu_percent:.1f}%"
            elif cpu_percent < 95:
                status = HealthStatus.WARNING
                message = f"CPU usage high: {cpu_percent:.1f}%"
            else:
                status = HealthStatus.CRITICAL
                message = f"CPU usage critical: {cpu_percent:.1f}%"
            
            return HealthCheck(
                component="cpu",
                status=status,
                message=message,
                response_time=response_time,
                details={"cpu_percent": cpu_percent}
            )
            
        except Exception as e:
            return HealthCheck(
                component="cpu",
                status=HealthStatus.UNKNOWN,
                message=f"CPU check failed: {str(e)}",
                response_time=time.time() - start_time
            )
    
    async def _check_memory(self) -> HealthCheck:
        """Check memory health."""
        start_time = time.time()
        
        try:
            memory = psutil.virtual_memory()
            response_time = time.time() - start_time
            
            if memory.percent < 80:
                status = HealthStatus.HEALTHY
                message = f"Memory usage normal: {memory.percent:.1f}%"
            elif memory.percent < 95:
                status = HealthStatus.WARNING
                message = f"Memory usage high: {memory.percent:.1f}%"
            else:
                status = HealthStatus.CRITICAL
                message = f"Memory usage critical: {memory.percent:.1f}%"
            
            return HealthCheck(
                component="memory",
                status=status,
                message=message,
                response_time=response_time,
                details={
                    "percent": memory.percent,
                    "available": memory.available,
                    "total": memory.total
                }
            )
            
        except Exception as e:
            return HealthCheck(
                component="memory",
                status=HealthStatus.UNKNOWN,
                message=f"Memory check failed: {str(e)}",
                response_time=time.time() - start_time
            )
    
    async def _check_disk(self) -> HealthCheck:
        """Check disk health."""
        start_time = time.time()
        
        try:
            # Use current directory for Windows compatibility
            disk = psutil.disk_usage('.')
            response_time = time.time() - start_time
            
            if disk.percent < 80:
                status = HealthStatus.HEALTHY
                message = f"Disk usage normal: {disk.percent:.1f}%"
            elif disk.percent < 95:
                status = HealthStatus.WARNING
                message = f"Disk usage high: {disk.percent:.1f}%"
            else:
                status = HealthStatus.CRITICAL
                message = f"Disk usage critical: {disk.percent:.1f}%"
            
            return HealthCheck(
                component="disk",
                status=status,
                message=message,
                response_time=response_time,
                details={
                    "percent": disk.percent,
                    "free": disk.free,
                    "total": disk.total
                }
            )
            
        except Exception as e:
            return HealthCheck(
                component="disk",
                status=HealthStatus.UNKNOWN,
                message=f"Disk check failed: {str(e)}",
                response_time=time.time() - start_time
            )
    
    async def _check_network(self) -> HealthCheck:
        """Check network health."""
        start_time = time.time()
        
        try:
            # Simple network check - verify network interfaces are available
            net_io = psutil.net_io_counters()
            response_time = time.time() - start_time
            
            if net_io:
                status = HealthStatus.HEALTHY
                message = "Network interfaces available"
                details = {
                    "bytes_sent": net_io.bytes_sent,
                    "bytes_recv": net_io.bytes_recv
                }
            else:
                status = HealthStatus.WARNING
                message = "No network activity detected"
                details = {}
            
            return HealthCheck(
                component="network",
                status=status,
                message=message,
                response_time=response_time,
                details=details
            )
            
        except Exception as e:
            return HealthCheck(
                component="network",
                status=HealthStatus.UNKNOWN,
                message=f"Network check failed: {str(e)}",
                response_time=time.time() - start_time
            )
    
    async def _check_processes(self) -> HealthCheck:
        """Check process health."""
        start_time = time.time()
        
        try:
            process_count = len(psutil.pids())
            response_time = time.time() - start_time
            
            if process_count < 500:
                status = HealthStatus.HEALTHY
                message = f"Process count normal: {process_count}"
            elif process_count < 1000:
                status = HealthStatus.WARNING
                message = f"Process count high: {process_count}"
            else:
                status = HealthStatus.CRITICAL
                message = f"Process count critical: {process_count}"
            
            return HealthCheck(
                component="processes",
                status=status,
                message=message,
                response_time=response_time,
                details={"process_count": process_count}
            )
            
        except Exception as e:
            return HealthCheck(
                component="processes",
                status=HealthStatus.UNKNOWN,
                message=f"Process check failed: {str(e)}",
                response_time=time.time() - start_time
            )
    
    def _determine_overall_status(self, checks: List[HealthCheck]) -> HealthStatus:
        """Determine overall system health status."""
        if not checks:
            return HealthStatus.UNKNOWN
        
        # Count status types
        status_counts = {status: 0 for status in HealthStatus}
        for check in checks:
            status_counts[check.status] += 1
        
        # Determine overall status based on priority
        if status_counts[HealthStatus.CRITICAL] > 0:
            return HealthStatus.CRITICAL
        elif status_counts[HealthStatus.WARNING] > 0:
            return HealthStatus.WARNING
        elif status_counts[HealthStatus.UNKNOWN] > 0:
            return HealthStatus.WARNING  # Treat unknown as warning
        else:
            return HealthStatus.HEALTHY

# Global health monitor instance
health_monitor = HealthMonitor()

async def get_system_health() -> SystemHealth:
    """Get system health status."""
    return await health_monitor.get_system_health()

def get_health_summary() -> Dict[str, Any]:
    """Get health summary."""
    return {
        "uptime_seconds": health_monitor.get_uptime(),
        "platform": platform.system(),
        "python_version": platform.python_version(),
        "last_check": datetime.now(timezone.utc).isoformat()
    }