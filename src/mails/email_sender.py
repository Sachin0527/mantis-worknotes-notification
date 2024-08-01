import smtplib
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

class EmailSender:
    @staticmethod
    def email_send(subject, body, config, to_email=None, attachment_path=None):
        email_config = config['email']
        host = email_config['host']
        port = email_config['port']
        from_email = email_config['from_email']
        password = email_config['password']

        if not to_email:
            to_email = email_config['to_email']

        # Create a multipart message
        msg = MIMEMultipart()
        msg['From'] = from_email
        msg['To'] = to_email
        msg['Subject'] = subject

        # Attach the body of the email
        msg.attach(MIMEText(body, 'plain'))

        # Attach the file if an attachment path is provided
        if attachment_path:
            try:
                attachment_name = os.path.basename(attachment_path)
                attachment = open(attachment_path, "rb")

                part = MIMEBase('application', 'octet-stream')
                part.set_payload(attachment.read())
                encoders.encode_base64(part)
                part.add_header('Content-Disposition', f"attachment; filename= {attachment_name}")

                msg.attach(part)
                attachment.close()
            except Exception as e:
                print(f"[!] Failed to attach file: {e}")

        # Send the email
        try:
            with smtplib.SMTP(host, port) as smtp:
                smtp.ehlo()
                smtp.starttls()
                smtp.login(from_email, password)
                smtp.sendmail(from_email, to_email, msg.as_string())
                print(f"[*] Email sent successfully to {to_email}")
        except Exception as e:
            print(f"[!] An error occurred while sending email: {e}")