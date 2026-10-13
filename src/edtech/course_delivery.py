from __future__ import annotations

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class LearnerProgress:
    learner_id: str
    course_title: str
    deadline: date
    completed_lessons: int
    total_lessons: int


@dataclass(frozen=True)
class CourseAccess:
    learner_id: str
    course_title: str
    state: str
    remaining_lessons: int
    educator_note: str


def decide_course_access(progress: LearnerProgress, today: date) -> CourseAccess:
    remaining = max(progress.total_lessons - progress.completed_lessons, 0)
    if remaining == 0:
        return CourseAccess(progress.learner_id, progress.course_title, "complete", 0, "Ready to archive")
    if today > progress.deadline:
        return CourseAccess(progress.learner_id, progress.course_title, "deadline_passed", remaining, "Follow up with learner")
    return CourseAccess(progress.learner_id, progress.course_title, "active", remaining, "Keep course open")


def educator_report(progress_items: list[LearnerProgress], today: date) -> dict[str, int]:
    decisions = [decide_course_access(item, today) for item in progress_items]
    return {
        "active": sum(item.state == "active" for item in decisions),
        "complete": sum(item.state == "complete" for item in decisions),
        "deadline_passed": sum(item.state == "deadline_passed" for item in decisions),
    }
