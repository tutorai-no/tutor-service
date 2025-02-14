from enum import Enum

class Topic(Enum):
    """
    All message broker topics shall be defined in this enum
    """
    ACCOUNT_CREATED = "account_created"
    ACTIVITY_CREATED = "activity_created"