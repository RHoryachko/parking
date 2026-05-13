import enum


class UserRole(str, enum.Enum):
    client = "client"
    worker = "worker"
    admin = "admin"


class WorkMode(str, enum.Enum):
    manual = "manual"
    ai = "ai"


class SpotStatus(str, enum.Enum):
    free = "free"
    reserved = "reserved"
    occupied = "occupied"
    inactive = "inactive"


class BookingStatus(str, enum.Enum):
    created = "created"
    paid = "paid"
    canceled = "canceled"
    expired = "expired"
    used = "used"


class SessionStatus(str, enum.Enum):
    active = "active"
    completed = "completed"


class PaymentStatus(str, enum.Enum):
    pending = "pending"
    paid = "paid"
    failed = "failed"
    refunded = "refunded"


class BarrierAction(str, enum.Enum):
    open = "open"
    close = "close"
