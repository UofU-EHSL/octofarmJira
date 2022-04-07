from enum import Enum


class GcodeStates(Enum):
    VALID = 1
    INVALID = 2


class ClassKeyStates(Enum):
    VALID = 1
    INVALID = 2


class JiraTransitionCodes(Enum):
    """
    Start Progress: 11 (From Open to In Progress)
    Ready for review: 21 (From In Progress to UNDER REVIEW)
    Stop Progress: 111 (From In Progress to CANCELLED)
    Approve : 31 (From Under Review to APPROVED)
    Reject: 131 (From Under Review to REJECTED)
    Done: 41  (From APPROVED to DONE)
    Reopen: 121  (From Cancelled to OPEN)
    Restart progress : 141  (From REJECTED to IN PROGRESS) # Renamed from "Start progress" to "Restart progress" when changing these to enums
    """

    START_PROGRESS = 11
    READY_FOR_REVIEW = 21
    STOP_PROGRESS = 111
    APPROVE = 31
    REJECT = 131
    DONE = 41
    REOPEN = 121
    RESTART_PROGRESS = 141