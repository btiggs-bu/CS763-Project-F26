from enum import Enum


class RoleName(str, Enum):
    STUDENT = "student"
    FACULTY = "faculty"
    ADMIN = "admin"


class ThreadType(str, Enum):
    LAB = "lab"
    COURSE = "course"
    PROJECT = "project"


class ThreadRestrictionLevel(str, Enum):
    OPEN = "open"
    RESTRICTED = "restricted"
    CLOSED = "closed"


class PostType(str, Enum):
    ANNOUNCEMENT = "announcement"
    DISCUSSION = "discussion"


class PostRestrictionLevel(str, Enum):
    INHERITED = "inherited"
    OPEN = "open"
    RESTRICTED = "restricted"
    CLOSED = "closed"


class CommentRestrictionLevel(str, Enum):
    INHERITED = "inherited"
    OPEN = "open"
    RESTRICTED = "restricted"
    CLOSED = "closed"


class ModerationStatus(str, Enum):
    ACTIVE = "active"
    REPORTED = "reported"
    HIDDEN_BY_MODERATOR = "hidden_by_moderator"
