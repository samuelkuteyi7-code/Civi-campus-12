from pydantic import BaseModel


class NotificationItem(BaseModel):
    type: str
    title: str
    message: str
    timestamp: str
