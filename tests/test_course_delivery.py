from datetime import date

from edtech.course_delivery import LearnerProgress, decide_course_access, educator_report


def test_deadline_passed_learner_needs_follow_up() -> None:
    learner = LearnerProgress("learner-9", "Geometry", date(2026, 9, 12), 3, 6)

    access = decide_course_access(learner, date(2026, 9, 15))

    assert access.state == "deadline_passed"
    assert access.remaining_lessons == 3
    assert access.educator_note == "Follow up with learner"


def test_educator_report_counts_current_course_states() -> None:
    learners = [
        LearnerProgress("a", "Geometry", date(2026, 9, 20), 2, 6),
        LearnerProgress("b", "Geometry", date(2026, 9, 12), 1, 6),
        LearnerProgress("c", "Geometry", date(2026, 9, 12), 6, 6),
    ]

    assert educator_report(learners, date(2026, 9, 15)) == {"active": 1, "deadline_passed": 1, "complete": 1}
