from fastapi import Depends
import aiosmtplib
from email.message import EmailMessage
import datetime
from sqlalchemy.ext.asyncio import AsyncSession
import traceback

from ..database import get_db
from ..core import ConfigService, get_config_service
from ..schemas import EmailToSend
from ..models import EmailLog

class EmailSenderService:
    def __init__(self, config_service: ConfigService, db: AsyncSession):
        self.smtp_host = config_service.get("SMTP_SERVER")
        self.smtp_port = config_service.get("SMTP_PORT")
        self.username = config_service.get("SMTP_USERNAME")
        self.password = config_service.get("SMTP_PASSWORD")
        self.db = db

    async def send_email(self, email_data: EmailToSend):
        msg = EmailMessage()
        msg["From"] = self.username
        msg["To"] = email_data.email
        msg["Subject"] = email_data.subject
        msg.set_content(email_data.body)
        recipients = [email_data.email]

        if email_data.cc:
            msg["Cc"] = ", ".join(email_data.cc)
        if email_data.bcc:
            msg["Bcc"] = ", ".join(email_data.bcc)

        status = "sent"
        error_message = None
        traceback_str = None

        try:
            await aiosmtplib.send(
                msg,
                hostname=self.smtp_host,
                port=int(self.smtp_port),
                username=self.username,
                password=self.password,
                start_tls=True,
                recipients=recipients,
            )
            print(f"✅ Email sent to {email_data.email}")
        except Exception as e:
            print(f"❌ Failed to send email to {email_data.email}: {e}")
            status = "failed"
            error_message = str(e)
            traceback_str = traceback.format_exc()
        # Сохраняем лог отправки
        email_log = EmailLog(
            email=email_data.email,
            subject=email_data.subject,
            body=email_data.body,
            cc=email_data.cc,
            bcc=email_data.bcc,
            attachments=email_data.attachments,
            status=status,            
            error=error_message,
            traceback=traceback_str,
            created_at=datetime.datetime.utcnow(),
        )

        self.db.add(email_log)
        await self.db.commit()

# Dependency for FastAPI
def get_email_sender_service(config_service: ConfigService = Depends(get_config_service),
                             db: AsyncSession = Depends(get_db)) -> EmailSenderService:
    return EmailSenderService(config_service=config_service, db=db)
