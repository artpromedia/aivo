"""Tests for search service models."""

from datetime import datetime

from app.models import (
    CourseworkDocument,
    LearnerDocument,
    LessonDocument,
    SearchRequest,
    SearchScope,
    UserContext,
    UserRole,
)


def test_search_request_creation():
    """Test creating a search request."""
    request = SearchRequest(q="test query", scope=SearchScope.ALL, size=10, from_=0)

    assert request.q == "test query"
    assert request.scope == SearchScope.ALL
    assert request.size == 10
    assert request.from_ == 0


def test_user_context_creation():
    """Test creating user context."""
    context = UserContext(
        user_id="user123",
        role=UserRole.TEACHER,
        district_id="district1",
        school_id="school1",
        class_ids=["class1", "class2"],
        learner_ids=["learner1", "learner2"],
    )

    assert context.user_id == "user123"
    assert context.role == UserRole.TEACHER
    assert context.district_id == "district1"
    assert len(context.class_ids) == 2


def test_lesson_document_creation():
    """Test creating a lesson document."""
    now = datetime.utcnow()
    lesson = LessonDocument(
        id="lesson123",
        title="Math Lesson",
        content="Learning about fractions",
        created_at=now,
        updated_at=now,
        subject="Mathematics",
        grade_level=5,
        district_id="district1",
        teacher_id="teacher1",
    )

    assert lesson.type == "lesson"
    assert lesson.title == "Math Lesson"
    assert lesson.subject == "Mathematics"


def test_coursework_document_creation():
    """Test creating a coursework document."""
    now = datetime.utcnow()
    coursework = CourseworkDocument(
        id="coursework123",
        title="Math Assignment",
        content="Solve these fraction problems",
        created_at=now,
        updated_at=now,
        assignment_type="homework",
        subject="Mathematics",
        grade_level=5,
        district_id="district1",
        school_id="school1",
        class_id="class1",
        teacher_id="teacher1",
    )

    assert coursework.type == "coursework"
    assert coursework.assignment_type == "homework"


def test_learner_document_creation():
    """Test creating a learner document."""
    now = datetime.utcnow()
    learner = LearnerDocument(
        id="learner123",
        title="Student Profile",
        content="Academic profile",
        created_at=now,
        updated_at=now,
        masked_name="Student ABC123",
        grade_level=5,
        district_id="district1",
        school_id="school1",
        class_ids=["class1"],
        teacher_ids=["teacher1"],
        guardian_ids=["guardian1"],
    )

    assert learner.type == "learner"
    assert learner.masked_name == "Student ABC123"
    assert len(learner.class_ids) == 1


def test_search_scope_enum():
    """Test search scope enumeration."""
    assert SearchScope.LESSONS == "lessons"
    assert SearchScope.COURSEWORK == "coursework"
    assert SearchScope.LEARNERS == "learners"
    assert SearchScope.ALL == "all"


def test_user_role_enum():
    """Test user role enumeration."""
    assert UserRole.LEARNER == "learner"
    assert UserRole.GUARDIAN == "guardian"
    assert UserRole.TEACHER == "teacher"
    assert UserRole.DISTRICT_ADMIN == "district_admin"
    assert UserRole.SYSTEM_ADMIN == "system_admin"
