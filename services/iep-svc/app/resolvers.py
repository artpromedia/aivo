"""
GraphQL resolvers for IEP Service.
"""

import logging
from datetime import datetime
from uuid import uuid4

import strawberry

from .approval_service import approval_service
from .crdt_manager import crdt_manager
from .enums import ApprovalStatus, IepStatus
from .event_service import event_service
from .schema import (
    Accommodation,
    AccommodationInput,
    ApprovalResult,
    CrdtOperation,
    Goal,
    GoalInput,
    IepDoc,
    IepDocInput,
    IepMutationResult,
)

logger = logging.getLogger(__name__)


@strawberry.type
class Query:
    """GraphQL queries for IEP service."""

    @strawberry.field
    async def iep(self, id: str) -> IepDoc | None:
        """Get an IEP document by ID."""
        return crdt_manager.get_document(id)

    @strawberry.field
    async def ieps(self, student_id: str | None = None) -> list[IepDoc]:
        """List IEP documents, optionally filtered by student."""
        return crdt_manager.list_documents(student_id)

    @strawberry.field
    async def student_ieps(self, student_id: str) -> list[IepDoc]:
        """Get all IEP documents for a specific student."""
        return crdt_manager.list_documents(student_id)

    @strawberry.field
    async def active_ieps(self) -> list[IepDoc]:
        """Get all active IEP documents."""
        all_docs = crdt_manager.list_documents()
        return [doc for doc in all_docs if doc.status == IepStatus.ACTIVE]

    @strawberry.field
    async def pending_approvals(self) -> list[IepDoc]:
        """Get all IEP documents pending approval."""
        all_docs = crdt_manager.list_documents()
        return [doc for doc in all_docs if doc.status == IepStatus.PENDING_APPROVAL]


@strawberry.type
class Mutation:
    """GraphQL mutations for IEP service."""

    @strawberry.mutation
    async def create_iep(self, input: IepDocInput, created_by: str) -> IepMutationResult:
        """Create a new IEP document."""
        try:
            # Prepare IEP data
            iep_data = {
                "student_id": input.student_id,
                "student_name": input.student_name,
                "school_year": input.school_year,
                "effective_date": input.effective_date,
                "expiry_date": input.expiry_date,
                "meeting_date": input.meeting_date,
                "present_levels": input.present_levels,
                "transition_services": input.transition_services,
                "special_factors": input.special_factors,
                "placement_details": input.placement_details,
            }

            # Create the document
            iep_doc = crdt_manager.create_document(iep_data, created_by)

            # Add goals if provided
            for goal_input in input.goals:
                await _add_goal_to_iep(iep_doc, goal_input, created_by)

            # Add accommodations if provided
            for acc_input in input.accommodations:
                await _add_accommodation_to_iep(iep_doc, acc_input, created_by)

            # Publish IEP created event
            await event_service.publish_iep_created(
                iep_id=iep_doc.id,
                student_id=iep_doc.student_id,
                created_by=created_by,
                student_name=iep_doc.student_name,
                school_year=iep_doc.school_year,
            )

            logger.info(f"Created IEP {iep_doc.id} for student {iep_doc.student_id}")

            return IepMutationResult(
                success=True, message="IEP document created successfully", iep=iep_doc
            )

        except Exception as e:
            logger.error(f"Error creating IEP: {e}")
            return IepMutationResult(
                success=False, message="Failed to create IEP document", errors=[str(e)]
            )

    @strawberry.mutation
    async def save_draft(
        self, iep_id: str, operations: list[CrdtOperation], updated_by: str
    ) -> IepMutationResult:
        """Save draft changes using CRDT operations."""
        try:
            iep_doc = crdt_manager.get_document(iep_id)
            if not iep_doc:
                return IepMutationResult(
                    success=False, message="IEP document not found", errors=["Document not found"]
                )

            if iep_doc.status not in [IepStatus.DRAFT, IepStatus.REJECTED]:
                return IepMutationResult(
                    success=False,
                    message="Can only edit draft or rejected IEP documents",
                    errors=["Invalid document status"],
                )

            # Apply CRDT operations
            applied_operations = []
            failed_operations = []

            for operation in operations:
                success, error = crdt_manager.apply_operation(iep_id, operation)
                if success:
                    applied_operations.append(operation.operation_type)
                else:
                    failed_operations.append(f"{operation.operation_type}: {error}")

            # Publish update event if any operations succeeded
            if applied_operations:
                await event_service.publish_iep_updated(
                    iep_id=iep_id,
                    student_id=iep_doc.student_id,
                    status=iep_doc.status.value,
                    updated_by=updated_by,
                    changes=applied_operations,
                )

                logger.info(f"Applied {len(applied_operations)} operations to IEP {iep_id}")

            return IepMutationResult(
                success=len(applied_operations) > 0,
                message=f"Applied {len(applied_operations)} of {len(operations)} operations",
                iep=iep_doc,
                errors=failed_operations,
            )

        except Exception as e:
            logger.error(f"Error saving draft: {e}")
            return IepMutationResult(success=False, message="Failed to save draft", errors=[str(e)])

    @strawberry.mutation
    async def submit_for_approval(self, iep_id: str, submitted_by: str) -> ApprovalResult:
        """Submit IEP document for dual approval."""
        try:
            iep_doc = crdt_manager.get_document(iep_id)
            if not iep_doc:
                return ApprovalResult(
                    success=False, message="IEP document not found", errors=["Document not found"]
                )

            if iep_doc.status != IepStatus.DRAFT:
                return ApprovalResult(
                    success=False,
                    message="Can only submit draft IEP documents for approval",
                    errors=["Invalid document status"],
                )

            # Validate IEP completeness
            validation_errors = _validate_iep_for_approval(iep_doc)
            if validation_errors:
                return ApprovalResult(
                    success=False, message="IEP document is incomplete", errors=validation_errors
                )

            # Submit to approval service
            approval_result = await approval_service.submit_for_approval(iep_doc, submitted_by)

            if approval_result["success"]:
                # Update IEP status
                iep_doc.status = IepStatus.PENDING_APPROVAL
                iep_doc.pending_approval_count = iep_doc.required_approval_count
                iep_doc.updated_at = datetime.utcnow()
                iep_doc.updated_by = submitted_by

                # Publish submission event
                await event_service.publish_iep_submitted(
                    iep_id=iep_id,
                    student_id=iep_doc.student_id,
                    submitted_by=submitted_by,
                    approval_request_id=approval_result["approval_request_id"],
                )

                logger.info(f"Submitted IEP {iep_id} for approval")

                return ApprovalResult(
                    success=True,
                    message="IEP submitted for dual approval",
                    approval_id=approval_result["approval_request_id"],
                    status=ApprovalStatus.PENDING,
                )
            else:
                return ApprovalResult(
                    success=False,
                    message=approval_result["message"],
                    errors=[approval_result.get("error", "Unknown error")],
                )

        except Exception as e:
            logger.error(f"Error submitting for approval: {e}")
            return ApprovalResult(
                success=False, message="Failed to submit for approval", errors=[str(e)]
            )

    @strawberry.mutation
    async def add_goal(self, iep_id: str, goal: GoalInput, added_by: str) -> IepMutationResult:
        """Add a goal to an IEP document."""
        try:
            iep_doc = crdt_manager.get_document(iep_id)
            if not iep_doc:
                return IepMutationResult(
                    success=False, message="IEP document not found", errors=["Document not found"]
                )

            if iep_doc.status not in [IepStatus.DRAFT, IepStatus.REJECTED]:
                return IepMutationResult(
                    success=False,
                    message="Can only add goals to draft or rejected IEP documents",
                    errors=["Invalid document status"],
                )

            # Add the goal
            goal_obj = await _add_goal_to_iep(iep_doc, goal, added_by)

            # Publish goal added event
            await event_service.publish_goal_added(
                iep_id=iep_id,
                goal_id=goal_obj.id,
                student_id=iep_doc.student_id,
                added_by=added_by,
                goal_type=goal.goal_type.value,
            )

            logger.info(f"Added goal {goal_obj.id} to IEP {iep_id}")

            return IepMutationResult(success=True, message="Goal added successfully", iep=iep_doc)

        except Exception as e:
            logger.error(f"Error adding goal: {e}")
            return IepMutationResult(success=False, message="Failed to add goal", errors=[str(e)])

    @strawberry.mutation
    async def add_accommodation(
        self, iep_id: str, accommodation: AccommodationInput, added_by: str
    ) -> IepMutationResult:
        """Add an accommodation to an IEP document."""
        try:
            iep_doc = crdt_manager.get_document(iep_id)
            if not iep_doc:
                return IepMutationResult(
                    success=False, message="IEP document not found", errors=["Document not found"]
                )

            if iep_doc.status not in [IepStatus.DRAFT, IepStatus.REJECTED]:
                return IepMutationResult(
                    success=False,
                    message="Can only add accommodations to draft or rejected IEP documents",
                    errors=["Invalid document status"],
                )

            # Add the accommodation
            acc_obj = await _add_accommodation_to_iep(iep_doc, accommodation, added_by)

            # Publish accommodation added event
            await event_service.publish_accommodation_added(
                iep_id=iep_id,
                accommodation_id=acc_obj.id,
                student_id=iep_doc.student_id,
                added_by=added_by,
                accommodation_type=accommodation.accommodation_type.value,
            )

            logger.info(f"Added accommodation {acc_obj.id} to IEP {iep_id}")

            return IepMutationResult(
                success=True, message="Accommodation added successfully", iep=iep_doc
            )

        except Exception as e:
            logger.error(f"Error adding accommodation: {e}")
            return IepMutationResult(
                success=False, message="Failed to add accommodation", errors=[str(e)]
            )


async def _add_goal_to_iep(iep_doc: IepDoc, goal_input: GoalInput, added_by: str) -> Goal:
    """Helper method to add a goal to an IEP document."""
    now = datetime.utcnow()
    goal = Goal(
        id=str(uuid4()),
        iep_id=iep_doc.id,
        goal_type=goal_input.goal_type,
        status="not_started",
        title=goal_input.title,
        description=goal_input.description,
        measurable_criteria=goal_input.measurable_criteria,
        target_date=goal_input.target_date,
        baseline_data=goal_input.baseline_data,
        progress_notes=[],
        responsible_staff=goal_input.responsible_staff,
        created_at=now,
        updated_at=now,
        created_by=added_by,
        updated_by=added_by,
        version=1,
        vector_clock={added_by: 1},
    )

    iep_doc.goals.append(goal)
    iep_doc.updated_at = now
    iep_doc.updated_by = added_by

    return goal


async def _add_accommodation_to_iep(
    iep_doc: IepDoc, acc_input: AccommodationInput, added_by: str
) -> Accommodation:
    """Helper method to add an accommodation to an IEP document."""
    now = datetime.utcnow()
    accommodation = Accommodation(
        id=str(uuid4()),
        iep_id=iep_doc.id,
        accommodation_type=acc_input.accommodation_type,
        title=acc_input.title,
        description=acc_input.description,
        implementation_notes=acc_input.implementation_notes,
        applicable_settings=acc_input.applicable_settings,
        frequency=acc_input.frequency,
        duration=acc_input.duration,
        responsible_staff=acc_input.responsible_staff,
        created_at=now,
        updated_at=now,
        created_by=added_by,
        updated_by=added_by,
        version=1,
        vector_clock={added_by: 1},
    )

    iep_doc.accommodations.append(accommodation)
    iep_doc.updated_at = now
    iep_doc.updated_by = added_by

    return accommodation


def _validate_iep_for_approval(iep_doc: IepDoc) -> list[str]:
    """Validate IEP document completeness for approval submission."""
    errors = []

    # Check required fields
    if not iep_doc.student_name.strip():
        errors.append("Student name is required")

    if not iep_doc.present_levels:
        errors.append("Present levels of performance is required")

    # Check for at least one goal
    if not iep_doc.goals:
        errors.append("At least one goal is required")

    # Validate goals
    for i, goal in enumerate(iep_doc.goals):
        if not goal.title.strip():
            errors.append(f"Goal {i + 1}: Title is required")
        if not goal.description.strip():
            errors.append(f"Goal {i + 1}: Description is required")
        if not goal.measurable_criteria.strip():
            errors.append(f"Goal {i + 1}: Measurable criteria is required")

    # Check for at least one accommodation
    if not iep_doc.accommodations:
        errors.append("At least one accommodation is required")

    # Validate accommodations
    for i, acc in enumerate(iep_doc.accommodations):
        if not acc.title.strip():
            errors.append(f"Accommodation {i + 1}: Title is required")
        if not acc.description.strip():
            errors.append(f"Accommodation {i + 1}: Description is required")

    return errors


# Create the GraphQL schema
schema = strawberry.Schema(query=Query, mutation=Mutation)
