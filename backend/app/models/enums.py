import enum


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    MANAGER = "manager"


class RequestStatus(str, enum.Enum):
    NEW = "NEW"
    IN_PROGRESS = "IN_PROGRESS"
    CONFIRMED = "CONFIRMED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class Intent(str, enum.Enum):
    BOOKING = "booking"
    QUESTION = "question"
    COMPLAINT = "complaint"
    PRICE_REQUEST = "price_request"
    CANCEL_BOOKING = "cancel_booking"
    RESCHEDULE = "reschedule"
    OTHER = "other"


class MessageSource(str, enum.Enum):
    TELEGRAM = "telegram"
    WEB = "web"
    MANUAL = "manual"


class MessageDirection(str, enum.Enum):
    IN = "in"
    OUT = "out"
