import atexit
import datetime
import json
import os
import time
from email.mime.text import MIMEText

import stable_whisper as whisper
import win10toast
from loguru import logger

import email_receiver_imap
import email_sender
from reconized_result_process import plain_text_result
import utils

TOAST_ICON_PATH, = utils.load_settings(['TOAST_ICON_PATH'])


MAIL_USER, ADMIN_ACCOUNT = utils.load_settings(['MAIL_USER', 'ADMIN_ACCOUNT'])

Toast = win10toast.ToastNotifier()
Toast.show_toast(
    '邮件监测已启动', '邮件whisper启动成功，开始识别新邮件', icon_path=TOAST_ICON_PATH, duration=3)

logger.add(f'./logs/{datetime.datetime.now().strftime("%Y%m%d_%H-%M-%S")}.log')


model = whisper.load_model('medium')


def program_exit():
    save_info()
    Toast.show_toast(
        "邮件监测正在关闭", '邮件whisper即将关闭，新邮件将无法被识别', icon_path=TOAST_ICON_PATH)


def result_feedback(id, filename, receiver=ADMIN_ACCOUNT):
    """
    识别完成后向发送邮件者回复结果
    """
    subject = filename
    cur_time = datetime.datetime.now().strftime("%Y%m%d_%H-%M-%S")

    try:
        # 读取识别的纯文本结果
        reconize_result = open(
            f'./emails/{id}/{".".join(filename.split(".")[:-1])}.txt', 'r', encoding='utf-8').read()

        content = f'时间: {cur_time}\n{subject}识别完成\n识别结果:\n\n\t{reconize_result}'

    except Exception as err:
        content = f'时间: {cur_time}\n发送邮件过程报错:\n {err}'

    message = MIMEText(content, 'plain', 'utf-8')
    message['From'] = MAIL_USER
    message['To'] = receiver
    message['Subject'] = subject
    email_sender.send(message, MAIL_USER, receiver)

    if receiver != ADMIN_ACCOUNT:
        admin_msg = MIMEText(f"用户 {receiver} 使用了 语音识别服务", 'plain', 'utf-8')
        admin_msg['From'] = MAIL_USER
        admin_msg['To'] = ADMIN_ACCOUNT
        admin_msg['Subject'] = '非管理员用户使用提醒'

        email_sender.send(admin_msg, MAIL_USER, ADMIN_ACCOUNT)

    logger.info(f"发送 id:{id} 的 结果回复邮件 成功")


def is_exclude(file_name: str) -> bool:
    """
    判断文件格式是否不可以识别
    """
    ends = file_name.split('.')[-1]
    # 不识别的后缀名
    exclude_ends = {'jpg', 'png', 'zip', 'txt', 'rar', '7z', 'webp',
                    'docx', 'doc', 'ppt', 'pptx', 'xls', 'xlsx',
                    'exe', 'py', 'cpp', 'c', 'yml', 'toml', 'json', 'torrent',
                    'msi', 'appx', 'apk', 'pdf', 'mobi', 'epub', 'html', 'css', 'js',
                    'pyd', 'pyc', 'dll', 'ico', 'log', 'htm', 'asp', 'aspx', 'chm',
                    'bmp', 'svg', 'gif', 'cdr', 'ai', 'wmf', 'eps', 'java', 'bat', 'cmd',
                    'tar', 'gz', 'lnk', 'url', 'iso', 'bin', 'ctf', 'srt', 'vtt'}
    return ends.lower() in exclude_ends


def reconize_audio(id, subject):
    """
    识别邮件附件中的音频
    :param id 邮件的id
    :param subject 邮件标题
    """
    path_to = f'./emails/{id}/'
    if not os.path.exists(path_to):
        logger.warning(f"识别 id:{id} 时 找不到附件文件夹")
        return -1

    files = os.listdir(path_to)
    for file in files:
        # 读取邮件附件目录下所有文件

        if is_exclude(file):
            continue

        try:
            logger.info(f"正在识别: {id}-{subject}")

            result = model.transcribe(os.path.abspath(path_to+file))
            open(path_to+file.split('.')[0]+'.txt', 'w+',
                 encoding='utf-8').write(plain_text_result(result))

            result.to_srt_vtt(path_to+file.split('.')[0]+'.srt', 'w+')
            logger.success(f"邮件编号 {id} 语音识别 成功")
            result_feedback(id, file, Email_Info[id]['sender'])
            # open(path_to+subject+'.txt', 'w+', encoding='utf-8').write(subject)
        except RuntimeError as err:
            logger.error(err)
            logger.error(path_to+file)
            # logger.error(os.listdir('.'))
    return 0


def save_info():
    """保存邮件识别信息"""
    json.dump(Email_Info, open('./INFOS.json', 'w+',
              encoding='utf-8'), ensure_ascii=False, indent=2)
    logger.success("成功保存识别记录")


def load_info():
    """读取邮件识别信息"""
    try:
        Email_Info = json.load(open('./INFOS.json', 'r', encoding='utf-8'))
    except FileNotFoundError:
        Email_Info = {}
    return Email_Info


def check_emails():
    """
    检查是否有新邮件
    下载附件
    并识别
    """

    not_seen_messages = []
    # result = []

    # 若rec_cli 因挂起时间过长自动登出则重新登录
    try:
        rec_cli = email_receiver_imap.login()
        for msg in rec_cli.search():
            if Email_Info.get(str(msg)):
                continue

            else:
                not_seen_messages.append(msg)
    except Exception as err:
        logger.warning(err)
        logger.warning("无法获取邮件列表")

    try:
        # 下载邮件的附件
        mails = email_receiver_imap.get_email_content(
            rec_cli, not_seen_messages)

        # 标记邮件
        for id in not_seen_messages:
            Email_Info[id] = {
                'downloaded': True,
                'reconized': False,
                'title':  mails[id][0],
                'sender': mails[id][1],
            }
            # result.append((id, subject[id]))
            # print(result)
        logger.success(f"成功获取 {len(not_seen_messages)} 个 邮件的附件")
        return not_seen_messages
    except Exception as err:
        logger.error(err)

    # return result


Email_Info = load_info()
logger.info(f"成功导入记录: {Email_Info}")


atexit.register(program_exit)

if __name__ == '__main__':
    # 先检查已下载未识别的邮件
    for k, v in Email_Info.items():
        if v['reconized']:
            continue
        else:
            reconize_audio(k, v['title'])
            Email_Info[k]['reconized'] = True

            logger.success(f"补充识别邮件 {k} 成功")
            save_info()

    # 每20分钟检测一次新邮件
    while True:
        new_email = check_emails()
        # print(new_email)
        for em in new_email:
            # print(em)
            reconize_audio(em, Email_Info[em]['title'])

            logger.success(f"识别邮件 {em} 成功")

            Email_Info[em]['reconized'] = True
            save_info()
            Email_Info = load_info()

        time.sleep(1200)
