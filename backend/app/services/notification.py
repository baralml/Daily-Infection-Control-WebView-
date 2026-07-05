import logging
import uuid
from sqlalchemy.orm import Session
from app.models.capa import NotifyChannelEnum, Notification
from app.schemas.capa import NotificationCreate
from app.crud.crud_capa import create_notification

logger = logging.getLogger("infection_control_notifications")
logging.basicConfig(level=logging.INFO)

def send_in_app_notification(db: Session, user_id: uuid.UUID, title: str, message: str) -> Notification:
    """Dispatches and writes an In-App notification alert."""
    notify_in = NotificationCreate(
        user_id=user_id,
        title=title,
        message=message,
        channel=NotifyChannelEnum.IN_APP
    )
    return create_notification(db, notify_in)

def send_email_notification(db: Session, user_id: uuid.UUID, email: str, title: str, message: str):
    """Mocks sending email notifications. Logs details for development."""
    logger.info(f"[EMAIL NOTIFICATION SENT] To: {email} | Subject: {title} | Message: {message}")
    
    # Store standard record as system log/notification history
    notify_in = NotificationCreate(
        user_id=user_id,
        title=f"Email sent: {title}",
        message=message,
        channel=NotifyChannelEnum.EMAIL
    )
    create_notification(db, notify_in)

def send_whatsapp_notification(db: Session, user_id: uuid.UUID, phone: str, title: str, message: str):
    """Mocks sending WhatsApp notifications. Prepared for Twilio/Meta API integration."""
    logger.info(f"[WHATSAPP NOTIFICATION SENT] To: {phone} | Title: {title} | Body: {message}")
    
    notify_in = NotificationCreate(
        user_id=user_id,
        title=f"WhatsApp sent: {title}",
        message=message,
        channel=NotifyChannelEnum.WHATSAPP
    )
    create_notification(db, notify_in)

def dispatch_notification_to_user(db: Session, user_id: uuid.UUID, title: str, message: str, channels: list[NotifyChannelEnum] = None):
    """Dispatches a notification to multiple communication channels for a user."""
    from app.crud.crud_user import get_user
    user = get_user(db, user_id)
    if not user:
        return
        
    if not channels:
        channels = [NotifyChannelEnum.IN_APP]
        
    for channel in channels:
        if channel == NotifyChannelEnum.IN_APP:
            send_in_app_notification(db, user.id, title, message)
        elif channel == NotifyChannelEnum.EMAIL:
            send_email_notification(db, user.id, user.email, title, message)
        elif channel == NotifyChannelEnum.WHATSAPP and user.phone_number:
            send_whatsapp_notification(db, user.id, user.phone_number, title, message)
