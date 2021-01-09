import imghdr
import logging
import os
import re
import smtplib
from email.message import EmailMessage

logger = logging.getLogger('FxStock')


class Email:
    def __init__(self):
        self.sender = 'EMAIL_ADDRESS'
        self.app_pwd = 'APP_PASSWORD'
        self.add_file = False
        self.file_path = 'res/'
        
    def send_email(self, subject='NA', content='NA'):
        try:
            receivers = [self.sender]
            
            msg = EmailMessage()
            msg['Subject'] = subject
            msg['From'] = self.sender
            msg['To'] = ', '.join(receivers)

            # msg.set_content(content)
            msg.add_alternative("""\
                                <!DOCTYPE html>
                                <html>
                                    <body>
                                        <h1 style="color:SlateGray;">{}</h1>
                                    </body>
                                </html>
                                """.format(content), subtype='html')
            
            if self.add_file:
                self.add_attachment(msg)
                
            with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
                smtp.login(self.sender, self.app_pwd)
                smtp.send_message(msg)
                
        except Exception as e:
            logger.exception('myemail send_email Exception: ', str(e))
    
    def is_email_valid(self, email):
        regex = '^\w+([\.-]?\w+)*@\w+([\.-]?\w+)*(\.\w{2,3})+$'
        return re.search(regex, email)
    
    def add_attachment(self, msg):
        files = ['test.pdf', 'test.jpg', 'test.png']

        for file in files:
            try:
                with open(self.file_path+file, 'rb') as f:
                    file_data = f.read()
                    file_name = os.path.basename(f.name)
                    if file_name.lower().endswith(('.jpg', '.jpeg', '.png')):
                        main_type = 'image'
                        file_type = imghdr.what(f.name)
                    elif file_name.lower().endswith('.pdf'):
                        main_type = 'application'
                        file_type = 'octet-sream'
                    msg.add_attachment(file_data, maintype=main_type, subtype=file_type, filename=file_name)
            except FileNotFoundError as e:
                logger.exception('myemail add_attachment FileNotFoundError', str(e))
