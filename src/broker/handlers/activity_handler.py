from uuid import UUID
from pydantic import BaseModel
from datetime import datetime

from accounts.models import Activity, Streak, CustomUser


class ActivityMessage(BaseModel):
    user_id: UUID
    activity_type: str
    timestamp: str
    metadata: dict


def handle_activity_streak(raw_message: str):
    message = ActivityMessage.model_validate_json(raw_message)
    user = CustomUser.objects.get(id=message.user_id)
    Activity.objects.create(
        user=user,
        activity_type=message.activity_type,
        timestamp=datetime.fromisoformat(message.timestamp),
        metadata=message.metadata,
    )
    streak = Streak.objects.get(user=user)
    streak.check_if_broken_streak()
    streak.increment_streak()
