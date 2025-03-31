import logging
from uuid import UUID
from pydantic import BaseModel
from datetime import datetime

from accounts.models import Activity, Streak, CustomUser

logger = logging.getLogger(__name__)


class ActivityMessage(BaseModel):
    user_id: UUID
    activity_type: str
    timestamp: str
    metadata: dict


def handle_activity_streak(raw_message: dict):
    logger.info("Handling activity streak")
    logger.info(raw_message)
    message = ActivityMessage.model_validate(raw_message)
    user = CustomUser.objects.get(id=message.user_id)
    streak = Streak.objects.get(user=user)
    streak.check_if_broken_streak()
    streak.increment_streak()


def handle_activity_save(raw_message: dict):
    logger.info("Handling activity save")
    logger.info(raw_message)
    message = ActivityMessage.model_validate(raw_message)
    user = CustomUser.objects.get(id=message.user_id)
    Activity.objects.create(
        user=user,
        activity_type=message.activity_type,
        timestamp=datetime.fromisoformat(message.timestamp),
        metadata=message.metadata,
    )
