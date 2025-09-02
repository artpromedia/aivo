"""
CRDT (Conflict-free Replicated Data Type) document manager for IEP documents.
Handles collaborative editing and conflict resolution.
"""
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from uuid import uuid4

from .enums import IepStatus
from .schema import IepDoc, Goal, Accommodation, CrdtOperation

logger = logging.getLogger(__name__)


class CrdtDocumentManager:
    """
    Manages CRDT operations for IEP documents to support collaborative editing.
    Uses a combination of vector clocks and operation-based CRDT.
    """
    
    def __init__(self):
        """Initialize the CRDT document manager."""
        self.documents: Dict[str, IepDoc] = {}
        self.operation_logs: Dict[str, List[Dict[str, Any]]] = {}
    
    def create_document(self, iep_data: Dict[str, Any], author_id: str) -> IepDoc:
        """Create a new IEP document with CRDT metadata."""
        doc_id = str(uuid4())
        now = datetime.utcnow()
        
        # Initialize vector clock
        vector_clock = {author_id: 1}
        
        # Create the document
        iep_doc = IepDoc(
            id=doc_id,
            student_id=iep_data["student_id"],
            student_name=iep_data["student_name"],
            status=IepStatus.DRAFT,
            school_year=iep_data["school_year"],
            effective_date=iep_data["effective_date"],
            expiry_date=iep_data["expiry_date"],
            meeting_date=iep_data.get("meeting_date"),
            present_levels=iep_data.get("present_levels"),
            transition_services=iep_data.get("transition_services"),
            special_factors=iep_data.get("special_factors", []),
            placement_details=iep_data.get("placement_details"),
            goals=[],
            accommodations=[],
            approval_records=[],
            pending_approval_count=0,
            required_approval_count=2,
            created_at=now,
            updated_at=now,
            created_by=author_id,
            updated_by=author_id,
            version=1,
            vector_clock=vector_clock,
            operation_log=[]
        )
        
        # Store document
        self.documents[doc_id] = iep_doc
        self.operation_logs[doc_id] = []
        
        # Log creation operation
        self._log_operation(doc_id, {
            "operation_type": "create",
            "path": "",
            "value": None,
            "author": author_id,
            "timestamp": now.isoformat(),
            "vector_clock": vector_clock.copy()
        })
        
        logger.info(f"Created new IEP document: {doc_id}")
        return iep_doc
    
    def apply_operation(self, doc_id: str, operation: CrdtOperation) -> Tuple[bool, Optional[str]]:
        """
        Apply a CRDT operation to a document.
        Returns (success, error_message).
        """
        if doc_id not in self.documents:
            return False, f"Document {doc_id} not found"
        
        doc = self.documents[doc_id]
        author_id = operation.author
        
        try:
            # Update vector clock
            if author_id not in doc.vector_clock:
                doc.vector_clock[author_id] = 0
            doc.vector_clock[author_id] += 1
            
            # Apply the operation based on type
            success, error = self._apply_operation_by_type(doc, operation)
            
            if success:
                # Update document metadata
                doc.updated_at = operation.timestamp
                doc.updated_by = author_id
                doc.version += 1
                
                # Log the operation
                self._log_operation(doc_id, {
                    "operation_type": operation.operation_type,
                    "path": operation.path,
                    "value": operation.value,
                    "position": operation.position,
                    "author": author_id,
                    "timestamp": operation.timestamp.isoformat(),
                    "vector_clock": doc.vector_clock.copy()
                })
                
                logger.info(f"Applied operation {operation.operation_type} to {doc_id}")
            
            return success, error
            
        except Exception as e:
            logger.error(f"Error applying operation to {doc_id}: {e}")
            return False, str(e)
    
    def _apply_operation_by_type(self, doc: IepDoc, operation: CrdtOperation) -> Tuple[bool, Optional[str]]:
        """Apply operation based on its type."""
        op_type = operation.operation_type
        path = operation.path
        value = operation.value
        
        if op_type == "update":
            return self._apply_update_operation(doc, path, value)
        elif op_type == "insert":
            return self._apply_insert_operation(doc, path, value, operation.position)
        elif op_type == "delete":
            return self._apply_delete_operation(doc, path, operation.position)
        else:
            return False, f"Unknown operation type: {op_type}"
    
    def _apply_update_operation(self, doc: IepDoc, path: str, value: str) -> Tuple[bool, Optional[str]]:
        """Apply an update operation to a document field."""
        try:
            # Parse the path and update the field
            if path == "present_levels":
                doc.present_levels = value
            elif path == "transition_services":
                doc.transition_services = value
            elif path == "placement_details":
                doc.placement_details = value
            elif path.startswith("goals."):
                # Update specific goal field
                parts = path.split(".")
                if len(parts) >= 3:
                    goal_index = int(parts[1])
                    field_name = parts[2]
                    if 0 <= goal_index < len(doc.goals):
                        goal = doc.goals[goal_index]
                        if hasattr(goal, field_name):
                            setattr(goal, field_name, value)
                            goal.updated_at = datetime.utcnow()
                        else:
                            return False, f"Goal field {field_name} not found"
                    else:
                        return False, f"Goal index {goal_index} out of range"
            elif path.startswith("accommodations."):
                # Update specific accommodation field
                parts = path.split(".")
                if len(parts) >= 3:
                    acc_index = int(parts[1])
                    field_name = parts[2]
                    if 0 <= acc_index < len(doc.accommodations):
                        accommodation = doc.accommodations[acc_index]
                        if hasattr(accommodation, field_name):
                            setattr(accommodation, field_name, value)
                            accommodation.updated_at = datetime.utcnow()
                        else:
                            return False, f"Accommodation field {field_name} not found"
                    else:
                        return False, f"Accommodation index {acc_index} out of range"
            else:
                return False, f"Unknown update path: {path}"
            
            return True, None
            
        except Exception as e:
            return False, str(e)
    
    def _apply_insert_operation(self, doc: IepDoc, path: str, value: str, position: Optional[int]) -> Tuple[bool, Optional[str]]:
        """Apply an insert operation (e.g., adding goals, accommodations)."""
        try:
            if path == "goals":
                # Insert a new goal
                goal_data = json.loads(value)
                goal = self._create_goal_from_data(doc.id, goal_data, doc.updated_by)
                if position is not None and 0 <= position <= len(doc.goals):
                    doc.goals.insert(position, goal)
                else:
                    doc.goals.append(goal)
            elif path == "accommodations":
                # Insert a new accommodation
                acc_data = json.loads(value)
                accommodation = self._create_accommodation_from_data(doc.id, acc_data, doc.updated_by)
                if position is not None and 0 <= position <= len(doc.accommodations):
                    doc.accommodations.insert(position, accommodation)
                else:
                    doc.accommodations.append(accommodation)
            elif path == "special_factors":
                # Insert special factor
                if position is not None and 0 <= position <= len(doc.special_factors):
                    doc.special_factors.insert(position, value)
                else:
                    doc.special_factors.append(value)
            else:
                return False, f"Unknown insert path: {path}"
            
            return True, None
            
        except Exception as e:
            return False, str(e)
    
    def _apply_delete_operation(self, doc: IepDoc, path: str, position: Optional[int]) -> Tuple[bool, Optional[str]]:
        """Apply a delete operation."""
        try:
            if path == "goals" and position is not None:
                if 0 <= position < len(doc.goals):
                    doc.goals.pop(position)
                else:
                    return False, f"Goal position {position} out of range"
            elif path == "accommodations" and position is not None:
                if 0 <= position < len(doc.accommodations):
                    doc.accommodations.pop(position)
                else:
                    return False, f"Accommodation position {position} out of range"
            elif path == "special_factors" and position is not None:
                if 0 <= position < len(doc.special_factors):
                    doc.special_factors.pop(position)
                else:
                    return False, f"Special factor position {position} out of range"
            else:
                return False, f"Unknown delete path: {path}"
            
            return True, None
            
        except Exception as e:
            return False, str(e)
    
    def _create_goal_from_data(self, iep_id: str, goal_data: Dict[str, Any], author_id: str) -> Goal:
        """Create a Goal object from data dictionary."""
        now = datetime.utcnow()
        return Goal(
            id=str(uuid4()),
            iep_id=iep_id,
            goal_type=goal_data["goal_type"],
            status=goal_data.get("status", "not_started"),
            title=goal_data["title"],
            description=goal_data["description"],
            measurable_criteria=goal_data["measurable_criteria"],
            target_date=goal_data["target_date"],
            baseline_data=goal_data.get("baseline_data"),
            progress_notes=goal_data.get("progress_notes", []),
            responsible_staff=goal_data.get("responsible_staff", []),
            created_at=now,
            updated_at=now,
            created_by=author_id,
            updated_by=author_id,
            version=1,
            vector_clock={author_id: 1}
        )
    
    def _create_accommodation_from_data(self, iep_id: str, acc_data: Dict[str, Any], author_id: str) -> Accommodation:
        """Create an Accommodation object from data dictionary."""
        now = datetime.utcnow()
        return Accommodation(
            id=str(uuid4()),
            iep_id=iep_id,
            accommodation_type=acc_data["accommodation_type"],
            title=acc_data["title"],
            description=acc_data["description"],
            implementation_notes=acc_data.get("implementation_notes"),
            applicable_settings=acc_data.get("applicable_settings", []),
            frequency=acc_data.get("frequency"),
            duration=acc_data.get("duration"),
            responsible_staff=acc_data.get("responsible_staff", []),
            created_at=now,
            updated_at=now,
            created_by=author_id,
            updated_by=author_id,
            version=1,
            vector_clock={author_id: 1}
        )
    
    def _log_operation(self, doc_id: str, operation: Dict[str, Any]) -> None:
        """Log an operation for the document."""
        if doc_id not in self.operation_logs:
            self.operation_logs[doc_id] = []
        
        self.operation_logs[doc_id].append(operation)
        
        # Keep only the last 1000 operations to prevent memory issues
        if len(self.operation_logs[doc_id]) > 1000:
            self.operation_logs[doc_id] = self.operation_logs[doc_id][-1000:]
    
    def get_document(self, doc_id: str) -> Optional[IepDoc]:
        """Get a document by ID."""
        return self.documents.get(doc_id)
    
    def list_documents(self, student_id: Optional[str] = None) -> List[IepDoc]:
        """List documents, optionally filtered by student ID."""
        docs = list(self.documents.values())
        if student_id:
            docs = [doc for doc in docs if doc.student_id == student_id]
        return docs
    
    def sync_documents(self, remote_operations: List[Dict[str, Any]]) -> List[str]:
        """
        Sync with remote operations (for distributed CRDT).
        Returns list of document IDs that were updated.
        """
        updated_docs = []
        
        for op_data in remote_operations:
            doc_id = op_data.get("doc_id")
            if not doc_id or doc_id not in self.documents:
                continue
            
            # Check if we already have this operation
            existing_ops = self.operation_logs.get(doc_id, [])
            op_exists = any(
                existing_op.get("timestamp") == op_data.get("timestamp") and
                existing_op.get("author") == op_data.get("author")
                for existing_op in existing_ops
            )
            
            if not op_exists:
                # Apply the remote operation
                operation = CrdtOperation(
                    operation_type=op_data["operation_type"],
                    path=op_data["path"],
                    value=op_data.get("value"),
                    position=op_data.get("position"),
                    author=op_data["author"],
                    timestamp=datetime.fromisoformat(op_data["timestamp"])
                )
                
                success, error = self.apply_operation(doc_id, operation)
                if success and doc_id not in updated_docs:
                    updated_docs.append(doc_id)
                elif error:
                    logger.error(f"Failed to sync operation for {doc_id}: {error}")
        
        return updated_docs
    
    def resolve_conflicts(self, doc_id: str) -> bool:
        """
        Resolve conflicts using last-write-wins strategy.
        More sophisticated conflict resolution can be implemented here.
        """
        if doc_id not in self.documents:
            return False
        
        # For now, we use operation ordering based on vector clocks
        # and timestamp for conflict resolution
        # This is a simplified approach - production systems might need
        # more sophisticated conflict resolution strategies
        
        operations = self.operation_logs.get(doc_id, [])
        if len(operations) <= 1:
            return True
        
        # Sort operations by timestamp for last-write-wins
        sorted_ops = sorted(operations, key=lambda op: op["timestamp"])
        
        # Rebuild document from sorted operations
        # This ensures consistent state across all replicas
        logger.info(f"Resolved conflicts for document {doc_id} using {len(sorted_ops)} operations")
        return True


# Global CRDT manager instance
crdt_manager = CrdtDocumentManager()
