from enum import Enum as PyEnum

class UserRole(PyEnum):
    USER = "user"
    ADMIN = "admin"
    MODERATOR = "moderator"