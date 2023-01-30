from email.message import EmailMessage
import ssl
import smtplib


class SendEmail:
    def __init__(self, **kwargs):
        self.sender = kwargs.get("sender")
        self.receiver = "chincho2022@yahoo.com"
        self.password = "gvnncbyknjhngelk"
        self.subject = kwargs.get("subject")
        self.body = kwargs.get("body")

    def send_mail(self):
        letter = EmailMessage()
        letter["From"] = self.sender
        letter["To"] = self.receiver
        letter["Subject"] = self.subject
        letter.set_content(self.body)

        actual_context = ssl.create_default_context()
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=actual_context) as smtp_message:
            smtp_message.login(self.sender, self.password)
            smtp_message.sendmail(self.sender, self.receiver, letter.as_string())
            smtp_message.close()
