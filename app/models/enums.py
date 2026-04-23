from enum import StrEnum


class UserRole(StrEnum):
    CONSUMER = "consumer"
    DELIVERY = "delivery"
    HOTEL_MANAGER = "hotel_manager"
    ADMIN = "admin"


class OrderStatus(StrEnum):
    CREATED = "created"
    BIDDING = "bidding"
    BID_ACCEPTED = "bid_accepted"
    PREPARING = "preparing"
    OUT_FOR_DELIVERY = "out_for_delivery"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


class BidStatus(StrEnum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    ORDER_CANCELLED = "order_cancelled"


class ReportStatus(StrEnum):
    OPEN = "open"
    REVIEWED = "reviewed"
    DISMISSED = "dismissed"


class Departments(StrEnum):
    CSE = "CSE"
    IT = "IT"
    IOT = "IOT"
    ECE = "ECE"
    MECH = "MECH"
    CIVIL = "CIVIL"
    CHEMICAL = "CHEMICAL"
    AIML = "AIML"
    AIDS = "AIDS"
    CYBER = "CYBER"
    EEE = "EEE"
    EIE = "EIE"
    BME = "BME"
    MBA = "MBA"
    OTHERS = "OTHERS"
