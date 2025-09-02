"""
Approval service integration for dual approval workflow.
"""
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import uuid4
import httpx

from .config import settings
from .enums import ApprovalStatus, EventType
from .schema import ApprovalRecord, IepDoc

logger = logging.getLogger(__name__)


class ApprovalService:
    """
    Handles integration with approval-svc for dual approval workflow.
    """
    
    def __init__(self):
        """Initialize the approval service."""
        self.base_url = settings.approval_service_url
        self.timeout = settings.approval_timeout
        self.dual_approval_required = settings.dual_approval_required
    
    async def submit_for_approval(self, iep_doc: IepDoc, submitted_by: str) -> Dict[str, Any]:
        """
        Submit an IEP document for dual approval.
        Returns approval request details.
        """
        try:
            approval_request = {
                "resource_type": "iep_document",
                "resource_id": iep_doc.id,
                "submitted_by": submitted_by,
                "title": f"IEP Approval - {iep_doc.student_name}",
                "description": f"IEP document for {iep_doc.student_name} ({iep_doc.school_year})",
                "metadata": {
                    "student_id": iep_doc.student_id,
                    "student_name": iep_doc.student_name,
                    "school_year": iep_doc.school_year,
                    "effective_date": iep_doc.effective_date.isoformat(),
                    "expiry_date": iep_doc.expiry_date.isoformat(),
                    "goals_count": len(iep_doc.goals),
                    "accommodations_count": len(iep_doc.accommodations)
                },
                "approval_requirements": {
                    "dual_approval": self.dual_approval_required,
                    "required_roles": ["special_education_coordinator", "administrator"],
                    "minimum_approvals": 2
                },
                "expires_at": (datetime.utcnow().replace(hour=23, minute=59, second=59)).isoformat()
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/requests",
                    json=approval_request,
                    timeout=self.timeout
                )
                response.raise_for_status()
                
                result = response.json()
                logger.info(f"Submitted IEP {iep_doc.id} for approval: {result.get('request_id')}")
                
                return {
                    "success": True,
                    "approval_request_id": result.get("request_id"),
                    "status": "pending",
                    "message": "IEP submitted for dual approval"
                }
                
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error submitting IEP for approval: {e}")
            return {
                "success": False,
                "error": f"HTTP {e.response.status_code}: {e.response.text}",
                "message": "Failed to submit IEP for approval"
            }
        except Exception as e:
            logger.error(f"Error submitting IEP for approval: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to submit IEP for approval"
            }
    
    async def check_approval_status(self, approval_request_id: str) -> Dict[str, Any]:
        """
        Check the status of an approval request.
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/requests/{approval_request_id}",
                    timeout=self.timeout
                )
                response.raise_for_status()
                
                result = response.json()
                return {
                    "success": True,
                    "status": result.get("status"),
                    "approvals": result.get("approvals", []),
                    "completed": result.get("completed", False)
                }
                
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error checking approval status: {e}")
            return {
                "success": False,
                "error": f"HTTP {e.response.status_code}: {e.response.text}"
            }
        except Exception as e:
            logger.error(f"Error checking approval status: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def process_approval_webhook(self, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process approval webhook from approval-svc.
        This is called when an approval status changes.
        """
        try:
            event_type = webhook_data.get("event_type")
            approval_data = webhook_data.get("data", {})
            resource_id = approval_data.get("resource_id")  # IEP ID
            
            if not resource_id:
                return {"success": False, "error": "Missing resource_id"}
            
            if event_type == "APPROVAL_COMPLETED":
                return await self._handle_approval_completed(resource_id, approval_data)
            elif event_type == "APPROVAL_REJECTED":
                return await self._handle_approval_rejected(resource_id, approval_data)
            elif event_type == "APPROVAL_RECEIVED":
                return await self._handle_single_approval(resource_id, approval_data)
            else:
                logger.warning(f"Unknown approval event type: {event_type}")
                return {"success": True, "message": "Event ignored"}
                
        except Exception as e:
            logger.error(f"Error processing approval webhook: {e}")
            return {"success": False, "error": str(e)}
    
    async def _handle_approval_completed(self, iep_id: str, approval_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle completed dual approval."""
        from .crdt_manager import crdt_manager
        from .event_service import event_service
        
        # Get the IEP document
        iep_doc = crdt_manager.get_document(iep_id)
        if not iep_doc:
            return {"success": False, "error": f"IEP document {iep_id} not found"}
        
        # Update IEP status to approved
        iep_doc.status = "approved"
        iep_doc.updated_at = datetime.utcnow()
        
        # Add approval records
        approvals = approval_data.get("approvals", [])
        for approval in approvals:
            approval_record = ApprovalRecord(
                id=str(uuid4()),
                iep_id=iep_id,
                approver_id=approval.get("approver_id"),
                approver_role=approval.get("role", "unknown"),
                status=ApprovalStatus.APPROVED,
                approved_at=datetime.fromisoformat(approval.get("approved_at")),
                comments=approval.get("comments"),
                created_at=datetime.utcnow()
            )
            iep_doc.approval_records.append(approval_record)
        
        # Update approval counts
        iep_doc.pending_approval_count = 0
        
        # Emit IEP_UPDATED event
        await event_service.publish_iep_updated(
            iep_id=iep_id,
            student_id=iep_doc.student_id,
            status=iep_doc.status,
            updated_by=approval_data.get("completed_by", "system"),
            changes=["status", "approval_records"]
        )
        
        logger.info(f"IEP {iep_id} fully approved")
        return {"success": True, "message": "IEP approved and activated"}
    
    async def _handle_approval_rejected(self, iep_id: str, approval_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle approval rejection."""
        from .crdt_manager import crdt_manager
        from .event_service import event_service
        
        # Get the IEP document
        iep_doc = crdt_manager.get_document(iep_id)
        if not iep_doc:
            return {"success": False, "error": f"IEP document {iep_id} not found"}
        
        # Update IEP status to rejected
        iep_doc.status = "rejected"
        iep_doc.updated_at = datetime.utcnow()
        
        # Add rejection record
        rejection_data = approval_data.get("rejection", {})
        approval_record = ApprovalRecord(
            id=str(uuid4()),
            iep_id=iep_id,
            approver_id=rejection_data.get("rejected_by"),
            approver_role=rejection_data.get("role", "unknown"),
            status=ApprovalStatus.REJECTED,
            rejected_at=datetime.fromisoformat(rejection_data.get("rejected_at")),
            rejection_reason=rejection_data.get("reason"),
            comments=rejection_data.get("comments"),
            created_at=datetime.utcnow()
        )
        iep_doc.approval_records.append(approval_record)
        
        # Reset approval counts
        iep_doc.pending_approval_count = 0
        
        # Emit IEP_REJECTED event
        await event_service.publish_event(
            event_type=EventType.IEP_REJECTED,
            resource_id=iep_id,
            data={
                "student_id": iep_doc.student_id,
                "rejection_reason": rejection_data.get("reason"),
                "rejected_by": rejection_data.get("rejected_by")
            }
        )
        
        logger.info(f"IEP {iep_id} rejected")
        return {"success": True, "message": "IEP rejection processed"}
    
    async def _handle_single_approval(self, iep_id: str, approval_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle a single approval (part of dual approval)."""
        from .crdt_manager import crdt_manager
        
        # Get the IEP document
        iep_doc = crdt_manager.get_document(iep_id)
        if not iep_doc:
            return {"success": False, "error": f"IEP document {iep_id} not found"}
        
        # Add approval record
        approval_record = ApprovalRecord(
            id=str(uuid4()),
            iep_id=iep_id,
            approver_id=approval_data.get("approver_id"),
            approver_role=approval_data.get("role", "unknown"),
            status=ApprovalStatus.APPROVED,
            approved_at=datetime.fromisoformat(approval_data.get("approved_at")),
            comments=approval_data.get("comments"),
            created_at=datetime.utcnow()
        )
        iep_doc.approval_records.append(approval_record)
        
        # Update pending count
        approved_count = sum(
            1 for record in iep_doc.approval_records
            if record.status == ApprovalStatus.APPROVED
        )
        iep_doc.pending_approval_count = max(0, iep_doc.required_approval_count - approved_count)
        
        logger.info(f"Received approval {approved_count}/{iep_doc.required_approval_count} for IEP {iep_id}")
        return {"success": True, "message": f"Approval {approved_count}/{iep_doc.required_approval_count} received"}
    
    def create_approval_record(
        self,
        iep_id: str,
        approver_id: str,
        approver_role: str,
        status: ApprovalStatus = ApprovalStatus.PENDING
    ) -> ApprovalRecord:
        """Create a new approval record."""
        return ApprovalRecord(
            id=str(uuid4()),
            iep_id=iep_id,
            approver_id=approver_id,
            approver_role=approver_role,
            status=status,
            created_at=datetime.utcnow()
        )


# Global approval service instance
approval_service = ApprovalService()
