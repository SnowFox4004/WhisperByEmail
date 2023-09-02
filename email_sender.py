import smtplib
import utils

SMTP_HOST, MAIL_USER, MAIL_PASS = utils.load_settings(
    ['SMTP_HOST', 'MAIL_USER', 'MAIL_PASS'])


def send(message, sender: str, receiver: str):
    try:
        smtpObj = smtplib.SMTP_SSL(SMTP_HOST)
        # smtpObj.set_debuglevel(1)
        # smtpObj.connect(MAIL_HOST, MAIL_PORT)
        smtpObj.login(MAIL_USER, MAIL_PASS)

        smtpObj.sendmail(
            sender,
            receiver,
            message.as_string()
        )

        smtpObj.quit()

        print("邮件发送成功")
        return 0
    except Exception as err:
        print("Error: ", err)
        return -1
