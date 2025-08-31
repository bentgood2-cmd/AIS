"""
Main application entry point for the AIS system.

This module provides the web API interface and orchestrates all system components.
"""

import asyncio
import logging
import os
import signal
import sys
import time
from contextlib import asynccontextmanager
from typing import Dict, Any, Optional
import re

import uvicorn
from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from psutil import cpu_percent

# Import AIS components
from ais.core.base import SystemLevel, ComponentStatus
from ais.core.operational import OperationalComponent
from ais.core.regulatory import RegulatoryComponent
from ais.core.optimization import OptimizationComponent
from ais.core.adaptive import AdaptiveComponent
from ais.core.identity import IdentityComponent
from ais.core.synthetic_data_generator import SyntheticDataGenerator

# Import monitoring modules
from health import get_system_health, get_health_summary
from metrics import metrics_collector, metrics_middleware, get_all_metrics

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def sanitize_for_logging(value: str) -> str:
    """Sanitize string for safe logging."""
    if not isinstance(value, str):
        value = str(value)
    return re.sub(r'[\r\n\x00-\x1f\x7f-\x9f]', '_', value)


class AISSystem:
    """Main AIS system orchestrator."""
    
    def __init__(self):
        self.components = {}
        self.synthetic_data_generator = None
        self.is_running = False
        self.logger = logger
        
        # Pre-create component map for performance
        self.component_map = {}
        
        # Initialize components
        self._init_components()
    
    def _init_components(self):
        """Initialize all system components."""
        try:
            # Create operational component
            self.components['operational'] = OperationalComponent(
                name="main_operational",
                system_level=SystemLevel.SYSTEM
            )
            
            # Create regulatory component
            self.components['regulatory'] = RegulatoryComponent(
                name="main_regulatory",
                system_level=SystemLevel.SYSTEM
            )
            
            # Create optimization component
            self.components['optimization'] = OptimizationComponent(
                name="main_optimization",
                system_level=SystemLevel.SYSTEM
            )
            
            # Create adaptive component
            self.components['adaptive'] = AdaptiveComponent(
                name="main_adaptive",
                system_level=SystemLevel.SYSTEM
            )
            
            # Create identity component
            self.components['identity'] = IdentityComponent(
                name="main_identity",
                system_level=SystemLevel.SYSTEM
            )
            
            # Create synthetic data generator
            self.synthetic_data_generator = SyntheticDataGenerator()
            
            # Create component map for efficient routing
            self.component_map = {
                "operational": self.components['operational'],
                "regulatory": self.components['regulatory'],
                "optimization": self.components['optimization'],
                "adaptive": self.components['adaptive'],
                "identity": self.components['identity']
            }
            
            self.logger.info("All components initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize components: {e}")
            raise
    
    async def start(self):
        """Start the AIS system."""
        started_components = []
        try:
            self.logger.info("Starting AIS system...")
            
            # Start all components
            for name, component in self.components.items():
                try:
                    await component.initialize()
                    started_components.append(name)
                    self.logger.info(f"Started component: {name}")
                except Exception as e:
                    self.logger.error(f"Failed to start component {name}: {e}")
                    # Rollback: stop previously started components
                    for started_name in started_components:
                        try:
                            await self.components[started_name].shutdown()
                        except Exception as rollback_error:
                            self.logger.warning(f"Rollback failed for {sanitize_for_logging(started_name)}: {sanitize_for_logging(str(rollback_error))}")
                    raise
            
            # Initialize synthetic data generator (no async init needed)
            self.logger.info("Synthetic data generator initialized")
            
            self.is_running = True
            self.logger.info("AIS system started successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to start AIS system: {e}")
            raise
    
    async def stop(self):
        """Stop the AIS system."""
        try:
            self.logger.info("Stopping AIS system...")
            
            # Stop all components
            for name, component in self.components.items():
                try:
                    await component.shutdown()
                    self.logger.info(f"Stopped component: {sanitize_for_logging(name)}")
                except Exception as e:
                    self.logger.error(f"Failed to stop component {sanitize_for_logging(name)}: {sanitize_for_logging(str(e))}")
            
            self.is_running = False
            self.logger.info("AIS system stopped successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to stop AIS system: {e}")
            raise
    
    def get_status(self) -> Dict[str, Any]:
        """Get system status."""
        status = {
            "is_running": self.is_running,
            "components": {},
            "timestamp": time.time()
        }
        
        for name, component in self.components.items():
            status["components"][name] = {
                "status": component.status.value,
                "name": component.name,
                "system_level": component.system_level.value
            }
        
        return status
    
    async def process_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process a request through the system."""
        try:
            # Record metrics
            metrics_collector.increment_counter("ais_requests_total")
            
            # Route request to appropriate component using pre-created map
            request_type = request_data.get("type", "general")
            component = self.component_map.get(request_type, self.components['operational'])
            result = await component.process(request_data)
            
            # Record success metrics
            metrics_collector.increment_counter("ais_requests_success_total")
            
            return {
                "success": True,
                "result": result,
                "timestamp": time.time()
            }
            
        except Exception as e:
            # Record error metrics
            metrics_collector.increment_counter("ais_requests_error_total", 
                                             labels={"error": str(e)})
            
            self.logger.error(f"Request processing failed: {e}")
            raise


# Global AIS system instance
ais_system = AISSystem()

@asynccontextmanager
async def lifespan_manager(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting AIS application...")
    try:
        await ais_system.start()
        logger.info("AIS application started successfully")
    except Exception as e:
        logger.error(f"Failed to start AIS application: {e}")
        sys.exit(1)
    
    yield
    
    # Shutdown
    logger.info("Shutting down AIS application...")
    try:
        await ais_system.stop()
        logger.info("AIS application shut down successfully")
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")


# Pydantic models for API requests/responses
class SystemStatusResponse(BaseModel):
    """System status response model."""
    is_running: bool
    components: Dict[str, Dict[str, Any]]
    timestamp: float


class ProcessRequestModel(BaseModel):
    """Process request model."""
    type: str = Field(..., description="Request type (operational, regulatory, etc.)")
    data: Dict[str, Any] = Field(default_factory=dict, description="Request data")
    priority: Optional[int] = Field(default=1, description="Request priority (1-10)")


class ProcessResponseModel(BaseModel):
    """Process response model."""
    success: bool
    result: Any
    timestamp: float
    message: Optional[str] = None


class HealthResponseModel(BaseModel):
    """Health check response model."""
    status: str
    timestamp: str
    uptime: str
    checks: list


class MetricsResponseModel(BaseModel):
    """Metrics response model."""
    timestamp: str
    total_metrics: int
    metrics_by_category: Dict[str, int]
    metrics_by_type: Dict[str, int]


# FastAPI app
app = FastAPI(
    title="AIS System API",
    description="API for the Autocatalytic Intelligence System",
    version="1.0.0",
    lifespan=lifespan_manager
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/", response_model=Dict[str, str])
async def root():
    """Root endpoint."""
    return {"message": "AIS System API", "version": "1.0.0"}


@app.get("/status", response_model=SystemStatusResponse)
async def get_status():
    """Get system status."""
    return ais_system.get_status()


@app.post("/process", response_model=ProcessResponseModel)
async def process_request(request: ProcessRequestModel):
    """Process a request through the AIS system."""
    try:
        async with metrics_middleware.measure_request("/process", "POST"):
            result = await ais_system.process_request({
                "type": request.type,
                "data": request.data,
                "priority": request.priority
            })
            
            return ProcessResponseModel(
                success=True,
                result=result["result"],
                timestamp=result["timestamp"],
                message="Request processed successfully"
            )
            
    except Exception as e:
        logger.error(f"Process request failed: {sanitize_for_logging(str(e))}")
        raise HTTPException(status_code=500, detail="Request processing failed")


@app.get("/health", response_model=HealthResponseModel)
async def health_check():
    """Get system health status."""
    try:
        health = await get_system_health()
        
        return HealthResponseModel(
            status=health.overall_status.value,
            timestamp=health.timestamp.isoformat(),
            uptime=str(health.uptime),
            checks=[
                {
                    "component": check.component,
                    "status": check.status.value,
                    "message": check.message,
                    "response_time": check.response_time
                }
                for check in health.checks
            ]
        )
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail="Health check failed")


@app.get("/health/summary")
async def health_summary():
    """Get health summary."""
    try:
        return get_health_summary()
    except Exception as e:
        logger.error(f"Health summary failed: {e}")
        raise HTTPException(status_code=500, detail="Health summary failed")


@app.get("/metrics", response_model=MetricsResponseModel)
async def get_metrics():
    """Get system metrics."""
    try:
        metrics = get_all_metrics()
        
        return MetricsResponseModel(
            timestamp=metrics["timestamp"],
            total_metrics=metrics["total_metrics"],
            metrics_by_category=metrics["metrics_by_category"],
            metrics_by_type=metrics["metrics_by_type"]
        )
        
    except Exception as e:
        logger.error(f"Metrics retrieval failed: {e}")
        raise HTTPException(status_code=500, detail="Metrics retrieval failed")


@app.get("/metrics/prometheus")
async def get_prometheus_metrics():
    """Get metrics in Prometheus format."""
    try:
        return metrics_collector.export_prometheus()
    except Exception as e:
        logger.error(f"Prometheus metrics export failed: {e}")
        raise HTTPException(status_code=500, detail="Prometheus export failed")


@app.get("/metrics/json")
async def get_metrics_json():
    """Get metrics in JSON format."""
    try:
        return metrics_collector.export_json()
    except Exception as e:
        logger.error(f"JSON metrics export failed: {e}")
        raise HTTPException(status_code=500, detail="JSON export failed")


@app.get("/components")
async def get_components():
    """Get information about all components."""
    try:
        components_info = {}
        
        for name, component in ais_system.components.items():
            components_info[name] = {
                "name": component.name,
                "status": component.status.value,
                "system_level": component.system_level.value,
                "description": component.__class__.__doc__ or "No description available"
            }
        
        return components_info
        
    except Exception as e:
        logger.error(f"Component info retrieval failed: {e}")
        raise HTTPException(status_code=500, detail="Component info retrieval failed")


@app.post("/components/{component_name}/start")
async def start_component(component_name: str):
    """Start a specific component."""
    try:
        if component_name not in ais_system.components:
            raise HTTPException(status_code=404, detail=f"Component {component_name} not found")
        
        component = ais_system.components[component_name]
        await component.initialize()
        
        return {"message": f"Component {component_name} started successfully"}
        
    except Exception as e:
        logger.error(f"Failed to start component {sanitize_for_logging(component_name)}: {sanitize_for_logging(str(e))}")
        raise HTTPException(status_code=500, detail="Component operation failed")


@app.post("/components/{component_name}/stop")
async def stop_component(component_name: str):
    """Stop a specific component."""
    try:
        if component_name not in ais_system.components:
            raise HTTPException(status_code=404, detail=f"Component {component_name} not found")
        
        component = ais_system.components[component_name]
        await component.shutdown()
        
        return {"message": f"Component {component_name} stopped successfully"}
        
    except Exception as e:
        logger.error(f"Failed to stop component {sanitize_for_logging(component_name)}: {sanitize_for_logging(str(e))}")
        raise HTTPException(status_code=500, detail="Component operation failed")


@app.get("/synthetic-data/schemas")
async def get_synthetic_data_schemas():
    """Get available synthetic data schemas."""
    try:
        if ais_system.synthetic_data_generator:
            return {"schemas": ["numerical", "categorical", "text", "time_series", "image"]}
        else:
            return {"error": "Synthetic data generator not available"}
            
    except Exception as e:
        logger.error(f"Schema retrieval failed: {e}")
        raise HTTPException(status_code=500, detail="Schema retrieval failed")


@app.post("/synthetic-data/generate")
async def generate_synthetic_data(request: Dict[str, Any]):
    """Generate synthetic data."""
    try:
        if not ais_system.synthetic_data_generator:
            raise HTTPException(status_code=500, detail="Synthetic data generator not available")
        
        schema_name = request.get("schema")
        count = request.get("count", 1)
        
        if not schema_name:
            raise HTTPException(status_code=400, detail="Schema name is required")
        
        from ais.core.synthetic_data_generator import DataSchema, DataType
        
        # Schema configuration
        schema_configs = {
            "numerical": DataSchema("value", DataType.NUMERICAL, {"distribution": "normal", "mean": 0, "std": 1}),
            "categorical": DataSchema("category", DataType.CATEGORICAL, {"categories": ["A", "B", "C"]}),
            "text": DataSchema("text", DataType.TEXT, {})
        }
        
        schema = [schema_configs.get(schema_name, schema_configs["numerical"])]
        
        generated_data = await ais_system.synthetic_data_generator.generate_data(schema, count)
        data = generated_data.data
        
        return {
            "success": True,
            "data": data,
            "schema": schema_name,
            "count": count
        }
        
    except Exception as e:
        logger.error(f"Data generation failed: {sanitize_for_logging(str(e))}")
        raise HTTPException(status_code=500, detail="Data generation failed")


# Error handlers
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler."""
    logger.error(f"Unhandled exception: {sanitize_for_logging(str(exc))}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )


def signal_handler(signum, frame):
    """Handle shutdown signals."""
    logger.info(f"Received signal {signum}, shutting down...")
    # Graceful shutdown instead of sys.exit
    try:
        loop = asyncio.get_event_loop()
        if not loop.is_closed():
            loop.create_task(ais_system.stop())
    except RuntimeError:
        pass  # Event loop not running
    finally:
        sys.exit(0)


if __name__ == "__main__":
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Get configuration from environment
    host = os.getenv("AIS_HOST", "0.0.0.0")
    try:
        port = int(os.getenv("AIS_PORT", "8000"))
    except ValueError:
        logger.error("Invalid AIS_PORT value, using default 8000")
        port = 8000
    log_level = os.getenv("AIS_LOG_LEVEL", "info")
    
    logger.info(f"Starting AIS API server on {host}:{port}")
    
    # Start the server
    uvicorn.run(
        "app:app",
        host=host,
        port=port,
        log_level=log_level,
        reload=False
    )
