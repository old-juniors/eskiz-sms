from enum import Enum


class MessageStatus(str, Enum):
    WAITING = "waiting"
    NEW = "NEW"
    ACCEPTED = "ACCEPTED"
    PARTDELIVERED = "PARTDELIVERED"
    DELIVERED = "DELIVERED"
    REJECTED = "REJECTED"


class MessagePartStatus(str, Enum):
    WAITING = "waiting"
    NEW = "NEW"
    ACCEPTED = "ACCEPTED"
    DELIVRD = "DELIVRD"
    UNDELIV = "UNDELIV"
    UNDELIVERABLE = "UNDELIVERABLE"
    EXPIRED = "EXPIRED"
    REJECTD = "REJECTD"
    DELETED = "DELETED"
    UNKNOWN = "UNKNOWN"
    ENROUTE = "ENROUTE"
