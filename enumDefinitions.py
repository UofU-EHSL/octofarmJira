from enum import Enum, auto


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


class GcodeCheckActions(Enum):
    ADD_COMMAND_AT_END = auto()
    """Add this command at the end of the file if it is not already the last command."""
    REMOVE_COMMAND_ALL = auto()
    """Remove all instances of this command. Will occur BEFORE ADD_COMMAND_AT_END"""
    COMMAND_MUST_EXIST = auto()
    """Ensure the command is present. For example, check for comment with a specific string such as nozzle diameter = 0.4"""
    COMMAND_PARAM_MAX = auto()
    """First parameter of command must be UNDER this value."""
    COMMAND_PARAM_MIN = auto()
    """First parameter of command must be OVER this value."""
    COMMAND_PARAM_RANGE = auto()
    """First parameter of command must be BETWEEN two values provided as comma separated string: 'x,x' """

