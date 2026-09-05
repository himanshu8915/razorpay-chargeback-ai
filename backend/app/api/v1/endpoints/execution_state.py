import time
from typing import Dict, List, Optional
from pydantic import BaseModel
import threading

class NodeState(BaseModel):
    id: str
    label: str
    status: str  # "pending", "running", "completed", "failed"

class ExecutionState(BaseModel):
    dispute_id: str
    status: str  # "QUEUED", "RUNNING", "COMPLETED", "FAILED", "TIMEOUT"
    active_agent: Optional[str] = None
    message: Optional[str] = None
    started_at: float
    updated_at: float
    completed_at: Optional[float] = None
    error_message: Optional[str] = None
    nodes: List[NodeState] = []

class ExecutionRegistry:
    def __init__(self):
        self._states: Dict[str, ExecutionState] = {}
        self._lock = threading.Lock()

    def get_state(self, dispute_id: str) -> Optional[ExecutionState]:
        with self._lock:
            return self._states.get(dispute_id)

    def start_analysis(self, dispute_id: str, nodes: List[Dict[str, str]]):
        with self._lock:
            self._states[dispute_id] = ExecutionState(
                dispute_id=dispute_id,
                status="RUNNING",
                started_at=time.time(),
                updated_at=time.time(),
                nodes=[NodeState(id=n["id"], label=n["label"], status="pending") for n in nodes]
            )

    def update_node(self, dispute_id: str, node_id: str, message: str, status: str = "running"):
        with self._lock:
            state = self._states.get(dispute_id)
            if not state:
                return
            state.active_agent = node_id
            state.message = message
            state.updated_at = time.time()
            for n in state.nodes:
                if n.id == node_id:
                    n.status = status
                # If moving forward, mark previous as completed
                elif status == "running" and n.status == "running":
                    n.status = "completed"

    def complete_node(self, dispute_id: str, node_id: str):
        with self._lock:
            state = self._states.get(dispute_id)
            if not state:
                return
            for n in state.nodes:
                if n.id == node_id:
                    n.status = "completed"
            state.updated_at = time.time()

    def fail_analysis(self, dispute_id: str, error_message: str):
        with self._lock:
            state = self._states.get(dispute_id)
            if not state:
                return
            state.status = "FAILED"
            state.error_message = error_message
            state.updated_at = time.time()
            state.completed_at = time.time()
            for n in state.nodes:
                if n.status == "running":
                    n.status = "failed"

    def timeout_analysis(self, dispute_id: str):
        with self._lock:
            state = self._states.get(dispute_id)
            if not state:
                return
            state.status = "TIMEOUT"
            state.error_message = "Analysis exceeded maximum execution time."
            state.updated_at = time.time()
            state.completed_at = time.time()
            for n in state.nodes:
                if n.status == "running":
                    n.status = "failed"

    def complete_analysis(self, dispute_id: str):
        with self._lock:
            state = self._states.get(dispute_id)
            if not state:
                return
            state.status = "COMPLETED"
            state.updated_at = time.time()
            state.completed_at = time.time()
            for n in state.nodes:
                if n.status == "running" or n.status == "pending":
                    n.status = "completed"

execution_registry = ExecutionRegistry()
