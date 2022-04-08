from enum import Enum


class GcodeStates(Enum):
    VALID = 1
    INVALID = 2


class ClassKeyStates(Enum):
    VALID = 1
    INVALID = 2


class JiraTransitionCodes(Enum):
    START_PROGRESS = 11
    """Start Progress: 11 (From Open to In Progress)"""
    READY_FOR_REVIEW = 21
    """Ready for review: 21 (From In Progress to UNDER REVIEW)"""
    STOP_PROGRESS = 111
    """Stop Progress: 111 (From In Progress to CANCELLED)"""
    APPROVE = 31
    """Approve : 31 (From Under Review to APPROVED)"""
    REJECT = 131
    """Reject: 131 (From Under Review to REJECTED)"""
    DONE = 41
    """Done: 41  (From APPROVED to DONE)"""
    REOPEN = 121
    """Reopen: 121  (From Cancelled to OPEN)"""
    RESTART_PROGRESS = 141
    """Restart progress : 141  (From REJECTED to IN PROGRESS) # Renamed from "Start progress" to "Restart progress" when changing these to enums"""
