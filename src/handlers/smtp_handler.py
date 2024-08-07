import os, json, smtplib
from email import encoders
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart

from src.config import SmtpConfig


def setup_email_to_list(body, email_to_list):
    # Extract email-related fields
    for key, value in body.items():
        if 'email' in key:
            email_to_list.append(value)
    return email_to_list


def setup_email_body_and_attachments(body):
    keys = []
    attachments = []
    for key, value in body.items():
        if 'Attachments Path' in key:
            keys.append(key)
            for val in value:
                attachments.append(val)
    filtered_body = {k: v for k, v in body.items() if k not in keys}
    formatted_body = json.dumps(filtered_body, indent=4)
    return formatted_body, attachments


class SmtpHandler:
    def __init__(self, config):
        self.__smtp_config = SmtpConfig(config)

    def send_email(self, subject, body):
        try:
            body = json.loads(body)
            default_email_to = self.__smtp_config.to_email
            email_to_list = [default_email_to]
            email_to_list = setup_email_to_list(body, email_to_list)
            email_to_list = ['karangupta125@gmail.com' if item == 'root@localhost' else item for item in email_to_list]

            # Create an email message
            msg = MIMEMultipart()
            msg["Subject"] = subject
            msg["From"] = self.__smtp_config.from_email
            msg["To"] = ';'.join(email_to_list)

            formatted_body, attachments = setup_email_body_and_attachments(body)

            # Attach the body of the email
            msg.attach(MIMEText(formatted_body, 'plain'))

            if len(attachments) > 0:
                for attachment in attachments:
                    with open(attachment, "rb") as file:
                        part = MIMEBase("application", "octet-stream")
                        part.set_payload(file.read())
                        encoders.encode_base64(part)
                        part.add_header(
                            "Content-Disposition",
                            f"attachment; filename={os.path.basename(attachment)}",
                        )
                        msg.attach(part)

            # Send the email
            with smtplib.SMTP(self.__smtp_config.host, self.__smtp_config.port) as server:
                server.ehlo()
                server.starttls()
                server.login(self.__smtp_config.from_email, self.__smtp_config.password)
                server.sendmail(self.__smtp_config.from_email, email_to_list, msg.as_string())
        except Exception as e:
            msg = f"Failed to send email for the Messages in queue: {e}"
            raise Exception(msg)
