"""
Process management module for the AIS system.

This module provides process management capabilities including:
- Task scheduling and execution
- Workflow management
- Process monitoring and control
- Resource allocation and management
- Process lifecycle management
"""

import asyncio
import logging
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, Any, Optional, List, Callable, Union, Coroutine
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import threading
import queue
import weakref
import re

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def sanitize_log_input(value: Any) -> str:
    """Sanitize input for logging to prevent log injection."""
    if value is None:
        return "None"
    log_str = str(value)
    # Remove newlines and carriage returns
    log_str = re.sub(r'[\r\n]', ' ', log_str)
    # Limit length to prevent log flooding
    if len(log_str) > 200:
        log_str = log_str[:200] + "..."
    return log_str


class ProcessStatus(Enum):
    """Process status enumeration."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    SUSPENDED = "suspended"
    TIMEOUT = "timeout"


class ProcessPriority(Enum):
    """Process priority levels."""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4
    EMERGENCY = 5


class ProcessType(Enum):
    """Process type enumeration."""
    TASK = "task"
    WORKFLOW = "workflow"
    BATCH = "batch"
    STREAM = "stream"
    INTERACTIVE = "interactive"


@dataclass
class ProcessDefinition:
    """Definition of a process."""
    name: str
    description: str
    process_type: ProcessType
    handler: Callable
    parameters: Dict[str, Any] = field(default_factory=dict)
    timeout: Optional[float] = None
    retry_count: int = 0
    retry_delay: float = 1.0
    dependencies: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ProcessInstance:
    """Instance of a running process."""
    process_id: str
    definition: ProcessDefinition
    status: ProcessStatus
    priority: ProcessPriority
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Any] = None
    error: Optional[str] = None
    progress: float = 0.0
    current_step: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    retry_count: int = 0
    parent_process_id: Optional[str] = None
    child_processes: List[str] = field(default_factory=list)


@dataclass
class WorkflowStep:
    """Step in a workflow process."""
    step_id: str
    name: str
    handler: Callable
    parameters: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)
    timeout: Optional[float] = None
    retry_count: int = 0
    retry_delay: float = 1.0
    condition: Optional[Callable] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class ProcessManager:
    """Main process management class."""
    
    def __init__(self, max_workers: int = 10, max_processes: int = 1000):
        self.max_workers = max_workers
        self.max_processes = max_processes
        self.processes: Dict[str, ProcessInstance] = {}
        self.definitions: Dict[str, ProcessDefinition] = {}
        self.workflows: Dict[str, List[WorkflowStep]] = {}
        
        # Execution pools
        self.thread_pool = ThreadPoolExecutor(max_workers=max_workers)
        self.process_pool = ProcessPoolExecutor(max_workers=max_workers)
        
        # Queues
        self.pending_queue = queue.PriorityQueue()
        self.running_processes: Dict[str, asyncio.Task] = {}
        
        # Monitoring
        self.stats = {
            "total_created": 0,
            "total_completed": 0,
            "total_failed": 0,
            "total_cancelled": 0,
            "active_processes": 0
        }
        
        # Control
        self.running = False
        self.lock = threading.Lock()
        self.logger = logger
        
        # Start background tasks
        self._start_background_tasks()
    
    def _start_background_tasks(self):
        """Start background monitoring and cleanup tasks."""
        self.running = True
        
        # Start scheduler task
        asyncio.create_task(self._scheduler_task())
        
        # Start cleanup task
        asyncio.create_task(self._cleanup_task())
        
        # Start monitoring task
        asyncio.create_task(self._monitoring_task())
    
    async def _scheduler_task(self):
        """Background task for scheduling processes."""
        while self.running:
            try:
                # Process pending queue
                if not self.pending_queue.empty():
                    priority, process_id = self.pending_queue.get_nowait()
                    process = self.processes.get(process_id)
                    
                    if process and process.status == ProcessStatus.PENDING:
                        await self._start_process(process)
                
                await asyncio.sleep(0.1)  # Small delay to prevent busy waiting
                
            except Exception as e:
                self.logger.error(f"Scheduler task error: {e}")
                await asyncio.sleep(1.0)
    
    async def _cleanup_task(self):
        """Background task for cleaning up completed processes."""
        while self.running:
            try:
                # Clean up old completed processes
                cutoff_time = datetime.now() - timedelta(hours=24)
                to_remove = []
                
                for process_id, process in self.processes.items():
                    if (process.status in [ProcessStatus.COMPLETED, ProcessStatus.FAILED, ProcessStatus.CANCELLED] and
                        process.completed_at and process.completed_at < cutoff_time):
                        to_remove.append(process_id)
                
                for process_id in to_remove:
                    del self.processes[process_id]
                
                await asyncio.sleep(300)  # Run every 5 minutes
                
            except Exception as e:
                self.logger.error(f"Cleanup task error: {e}")
                await asyncio.sleep(60)
    
    async def _monitoring_task(self):
        """Background task for monitoring active processes."""
        while self.running:
            try:
                # Update statistics
                self.stats["active_processes"] = len([p for p in self.processes.values() 
                                                    if p.status == ProcessStatus.RUNNING])
                
                # Check for stuck processes
                for process_id, process in self.processes.items():
                    if (process.status == ProcessStatus.RUNNING and 
                        process.started_at and 
                        process.definition.timeout):
                        
                        elapsed = (datetime.now() - process.started_at).total_seconds()
                        if elapsed > process.definition.timeout:
                            await self._handle_process_timeout(process)
                
                await asyncio.sleep(10)  # Run every 10 seconds
                
            except Exception as e:
                self.logger.error(f"Monitoring task error: {e}")
                await asyncio.sleep(30)
    
    def register_process(self, name: str, definition: ProcessDefinition):
        """Register a process definition."""
        with self.lock:
            self.definitions[name] = definition
            self.logger.info(f"Registered process: {name}")
    
    def register_workflow(self, name: str, steps: List[WorkflowStep]):
        """Register a workflow definition."""
        with self.lock:
            self.workflows[name] = steps
            self.logger.info(f"Registered workflow: {name} with {len(steps)} steps")
    
    async def submit_process(self, name: str, priority: ProcessPriority = ProcessPriority.NORMAL,
                           parameters: Optional[Dict[str, Any]] = None,
                           parent_process_id: Optional[str] = None) -> str:
        """Submit a process for execution."""
        if name not in self.definitions:
            raise ValueError(f"Process '{name}' not registered")
        
        definition = self.definitions[name]
        process_id = str(uuid.uuid4())
        
        # Create process instance
        process = ProcessInstance(
            process_id=process_id,
            definition=definition,
            status=ProcessStatus.PENDING,
            priority=priority,
            created_at=datetime.now(),
            parameters=parameters or {},
            parent_process_id=parent_process_id
        )
        
        with self.lock:
            self.processes[process_id] = process
            self.stats["total_created"] += 1
        
        # Add to pending queue
        queue_priority = (priority.value, process.created_at.timestamp())
        self.pending_queue.put((queue_priority, process_id))
        
        self.logger.info(f"Submitted process {sanitize_log_input(process_id)} ({sanitize_log_input(name)}) with priority {priority.value}")
        
        return process_id
    
    async def submit_workflow(self, name: str, priority: ProcessPriority = ProcessPriority.NORMAL,
                            parameters: Optional[Dict[str, Any]] = None) -> str:
        """Submit a workflow for execution."""
        if name not in self.workflows:
            raise ValueError(f"Workflow '{name}' not registered")
        
        workflow_id = str(uuid.uuid4())
        steps = self.workflows[name]
        
        # Create workflow process
        workflow_definition = ProcessDefinition(
            name=f"workflow_{name}",
            description=f"Workflow: {name}",
            process_type=ProcessType.WORKFLOW,
            handler=self._execute_workflow,
            parameters={"workflow_name": name, "steps": steps, **parameters or {}},
            timeout=None  # Workflows don't have overall timeout
        )
        
        # Register the workflow process
        self.register_process(f"workflow_{name}", workflow_definition)
        
        # Submit the workflow
        return await self.submit_process(f"workflow_{name}", priority, parameters, workflow_id)
    
    async def _start_process(self, process: ProcessInstance):
        """Start a process execution."""
        if process.status != ProcessStatus.PENDING:
            return
        
        # Check dependencies
        if not await self._check_dependencies(process):
            return
        
        # Update status
        process.status = ProcessStatus.RUNNING
        process.started_at = datetime.now()
        
        # Create execution task
        task = asyncio.create_task(self._execute_process(process))
        self.running_processes[process.process_id] = task
        
        self.logger.info(f"Started process {sanitize_log_input(process.process_id)}")
    
    async def _execute_process(self, process: ProcessInstance):
        """Execute a process."""
        try:
            if process.definition.process_type == ProcessType.WORKFLOW:
                result = await self._execute_workflow(process)
            else:
                result = await self._execute_task(process)
            
            # Mark as completed
            process.status = ProcessStatus.COMPLETED
            process.completed_at = datetime.now()
            process.result = result
            process.progress = 100.0
            
            self.stats["total_completed"] += 1
            
        except asyncio.CancelledError:
            process.status = ProcessStatus.CANCELLED
            process.completed_at = datetime.now()
            self.stats["total_cancelled"] += 1
            
        except Exception as e:
            process.status = ProcessStatus.FAILED
            process.completed_at = datetime.now()
            process.error = str(e)
            self.stats["total_failed"] += 1
            
            self.logger.error(f"Process {sanitize_log_input(process.process_id)} failed: {sanitize_log_input(e)}")
            
            # Handle retries
            if process.retry_count < process.definition.retry_count:
                await self._retry_process(process)
                return
        
        finally:
            # Clean up
            if process.process_id in self.running_processes:
                del self.running_processes[process.process_id]
    
    async def _execute_task(self, process: ProcessInstance) -> Any:
        """Execute a single task process."""
        handler = process.definition.handler
        parameters = {**process.definition.parameters, **process.parameters}
        
        # Check if handler is async
        if asyncio.iscoroutinefunction(handler):
            result = await handler(**parameters)
        else:
            # Run in thread pool for synchronous handlers
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(self.thread_pool, handler, **parameters)
        
        return result
    
    async def _execute_workflow(self, process: ProcessInstance) -> Any:
        """Execute a workflow process."""
        workflow_name = process.parameters.get("workflow_name")
        steps = process.parameters.get("steps", [])
        
        if not steps:
            raise ValueError(f"No steps defined for workflow {workflow_name}")
        
        results = {}
        current_step = 0
        
        for step in steps:
            # Check step condition
            if step.condition and not step.condition(results):
                self.logger.info(f"Skipping step {step.step_id} due to condition")
                continue
            
            # Update progress
            process.current_step = step.step_id
            process.progress = (current_step / len(steps)) * 100
            
            # Execute step
            try:
                step_handler = step.handler
                step_parameters = {**step.parameters, **process.parameters, **results}
                
                if asyncio.iscoroutinefunction(step_handler):
                    step_result = await step_handler(**step_parameters)
                else:
                    loop = asyncio.get_event_loop()
                    step_result = await loop.run_in_executor(self.thread_pool, step_handler, **step_parameters)
                
                results[step.step_id] = step_result
                current_step += 1
                
                self.logger.info(f"Completed workflow step {sanitize_log_input(step.step_id)}")
                
            except Exception as e:
                self.logger.error(f"Workflow step {sanitize_log_input(step.step_id)} failed: {sanitize_log_input(str(e))}")
                raise
        
        # Update final progress
        process.progress = 100.0
        process.current_step = "completed"
        
        return results
    
    async def _check_dependencies(self, process: ProcessInstance) -> bool:
        """Check if process dependencies are satisfied."""
        for dep_id in process.definition.dependencies:
            dep_process = self.processes.get(dep_id)
            if not dep_process or dep_process.status != ProcessStatus.COMPLETED:
                return False
        return True
    
    async def _retry_process(self, process: ProcessInstance):
        """Retry a failed process."""
        if process.retry_count >= process.definition.retry_count:
            return
        
        process.retry_count += 1
        process.status = ProcessStatus.PENDING
        process.started_at = None
        process.completed_at = None
        process.error = None
        
        # Add back to pending queue with delay
        await asyncio.sleep(process.definition.retry_delay)
        
        queue_priority = (process.priority.value, process.created_at.timestamp())
        self.pending_queue.put((queue_priority, process.process_id))
        
        self.logger.info(f"Retrying process {sanitize_log_input(process.process_id)} (attempt {process.retry_count})")
    
    async def _handle_process_timeout(self, process: ProcessInstance):
        """Handle a process timeout."""
        process.status = ProcessStatus.TIMEOUT
        process.completed_at = datetime.now()
        process.error = "Process timeout"
        
        # Cancel the running task
        if process.process_id in self.running_processes:
            task = self.running_processes[process.process_id]
            task.cancel()
            del self.running_processes[process.process_id]
        
        self.logger.warning(f"Process {sanitize_log_input(process.process_id)} timed out")
    
    async def cancel_process(self, process_id: str) -> bool:
        """Cancel a running process."""
        if process_id not in self.processes:
            return False
        
        process = self.processes[process_id]
        if process.status not in [ProcessStatus.PENDING, ProcessStatus.RUNNING]:
            return False
        
        # Cancel if running
        if process_id in self.running_processes:
            task = self.running_processes[process_id]
            task.cancel()
            del self.running_processes[process_id]
        
        # Update status
        process.status = ProcessStatus.CANCELLED
        process.completed_at = datetime.now()
        
        self.logger.info(f"Cancelled process {sanitize_log_input(process_id)}")
        return True
    
    async def get_process_status(self, process_id: str) -> Optional[ProcessInstance]:
        """Get the status of a process."""
        return self.processes.get(process_id)
    
    def get_all_processes(self, status_filter: Optional[ProcessStatus] = None) -> List[ProcessInstance]:
        """Get all processes, optionally filtered by status."""
        processes = list(self.processes.values())
        
        if status_filter:
            processes = [p for p in processes if p.status == status_filter]
        
        return processes
    
    def get_process_statistics(self) -> Dict[str, Any]:
        """Get process management statistics."""
        return {
            **self.stats,
            "total_processes": len(self.processes),
            "pending_processes": len([p for p in self.processes.values() if p.status == ProcessStatus.PENDING]),
            "running_processes": len([p for p in self.processes.values() if p.status == ProcessStatus.RUNNING]),
            "completed_processes": len([p for p in self.processes.values() if p.status == ProcessStatus.COMPLETED]),
            "failed_processes": len([p for p in self.processes.values() if p.status == ProcessStatus.FAILED]),
            "cancelled_processes": len([p for p in self.processes.values() if p.status == ProcessStatus.CANCELLED]),
            "suspended_processes": len([p for p in self.processes.values() if p.status == ProcessStatus.SUSPENDED]),
            "timeout_processes": len([p for p in self.processes.values() if p.status == ProcessStatus.TIMEOUT])
        }
    
    async def shutdown(self):
        """Shutdown the process manager."""
        self.running = False
        
        # Cancel all running processes
        for task in self.running_processes.values():
            task.cancel()
        
        # Wait for tasks to complete
        if self.running_processes:
            await asyncio.gather(*self.running_processes.values(), return_exceptions=True)
        
        # Shutdown pools
        self.thread_pool.shutdown(wait=True)
        self.process_pool.shutdown(wait=True)
        
        self.logger.info("Process manager shutdown complete")


# Convenience functions for common process types
def create_task_process(name: str, handler: Callable, **kwargs) -> ProcessDefinition:
    """Create a task process definition."""
    return ProcessDefinition(
        name=name,
        description=kwargs.get("description", f"Task: {name}"),
        process_type=ProcessType.TASK,
        handler=handler,
        **kwargs
    )


def create_batch_process(name: str, handler: Callable, **kwargs) -> ProcessDefinition:
    """Create a batch process definition."""
    return ProcessDefinition(
        name=name,
        description=kwargs.get("description", f"Batch: {name}"),
        process_type=ProcessType.BATCH,
        handler=handler,
        **kwargs
    )


def create_workflow_step(step_id: str, name: str, handler: Callable, **kwargs) -> WorkflowStep:
    """Create a workflow step."""
    return WorkflowStep(
        step_id=step_id,
        name=name,
        handler=handler,
        **kwargs
    )


# Global process manager instance
process_manager = ProcessManager()


if __name__ == "__main__":
    async def main():
        """Test the process management system."""
        print("Testing process management system...")
        
        # Define a simple task
        def simple_task(message: str, delay: float = 1.0):
            import time
            time.sleep(delay)
            return f"Task completed: {message}"
        
        # Register the task
        task_def = create_task_process(
            "simple_task",
            simple_task,
            description="A simple test task",
            timeout=10.0,
            retry_count=2
        )
        process_manager.register_process("simple_task", task_def)
        
        # Submit a process
        process_id = await process_manager.submit_process(
            "simple_task",
            priority=ProcessPriority.HIGH,
            parameters={"message": "Hello, World!", "delay": 2.0}
        )
        
        print(f"Submitted process: {process_id}")
        
        # Wait for completion
        while True:
            process = await process_manager.get_process_status(process_id)
            if process.status in [ProcessStatus.COMPLETED, ProcessStatus.FAILED, ProcessStatus.CANCELLED]:
                break
            await asyncio.sleep(0.5)
        
        print(f"Process completed with status: {process.status}")
        if process.result:
            print(f"Result: {process.result}")
        
        # Get statistics
        stats = process_manager.get_process_statistics()
        print(f"Statistics: {stats}")
        
        # Shutdown
        await process_manager.shutdown()
    
    asyncio.run(main())
