import os
from email import message_from_bytes
from email.header import decode_header
from email.parser import Parser

from imapclient import IMAPClient
from datetime import date
from loguru import logger

import utils

IMAP_SERVER, MAIL_USER, MAIL_PASS, WHITE_LIST = utils.load_settings(
    ['IMAP_SERVER', 'MAIL_USER', 'MAIL_PASS', 'WHITE_LIST'])

DATE_SINCE, = utils.load_settings(['DATE_SINCE'])


def safe_filename(filename: str) -> str:
    """
    获取可以用于保存文件的文件名
    """
    banned_chars = ['/', '\\', '?', ':', '*',
                    '?', '"', '<', '>', '|', '\n', '\r',]
    for char in banned_chars:
        filename = filename.replace(char, ' ')
    return filename


def login(folder='INBOX'):
    """
    登录邮箱
    返回一个连接至邮箱的 IMAPClient 实例
    """
    client = IMAPClient(IMAP_SERVER, ssl=True)

    client.login(MAIL_USER, MAIL_PASS)
    client.id_({"name": "WY CEO", 'version': "2.1.0"})  # name不知道做甚得

    logger.success("登陆服务器成功")
    logger.debug("\n邮箱文件夹:\n\t{0}" .format('\n\t'.join((str(i)
                 for i in client.list_folders()))))

    client.select_folder(folder, readonly=True)
    logger.info(f"已选中 {folder} 文件夹")

    return client

# 未使用
# def get_email_list(client: IMAPClient):
#     """
#     获取全部邮件
#     """
#     messages = client.search()

#     logger.debug(messages)


def get_email_content(client: IMAPClient, messages):
    """
        下载邮件的附件
        :param client: IMAPClient对象
        :param messages: 需获取邮件的uid, 必须为可迭代对象
    """
    logger.debug(f"开始获取 {len(messages)} 封邮件")
    emails = {}
    # time_zone = pytz.timezone("Asia/Shanghai")

    # logger.debug(client.fetch(messages, 'RFC822'))
    for email_id in messages:

        # 获取 envelope(信封)
        # 估计是 类似于 header 的 东西

        resp = client.fetch(email_id, ['ENVELOPE'])
        envelope = resp[email_id][b'ENVELOPE']

        logger.info(f"获取 {email_id} 邮件的信息成功")

        subject = envelope.subject
        subject, decode = decode_header(subject.decode())[0]
        subject = subject.decode(decode) if decode else str(subject)

        sender = envelope.sender[0]
        # logger.info(f'{sender.mailbox}@{sender.host}')
        sender = sender.mailbox.decode() + '@' + sender.host.decode()
        sender = sender.lower()

        logger.info(f"\t邮件标题: {subject}")

        emails[email_id] = (subject, sender)
        if sender not in WHITE_LIST:
            logger.critical(f"发现位于白名单外用户 {sender} ，跳过")
            continue

        # 获取附件
        resp = client.fetch(email_id, ['RFC822'])
        email_message = message_from_bytes(resp[email_id][b'RFC822'])
        msg = Parser().parsestr(email_message.as_string())

        # 如果你来研读代码的话
        # 载荷似乎其实就是所含有的内容
        # 也不知道为什么要生造新名词出来用（
        for part in msg.walk():
            # 疑似第一段 载荷 与 msg 的 载荷 相同 为总载荷
            # 第二段为纯文本形式
            # 第三段为html代码
            # 往后是附件

            if (file_name := part.get_filename()) is None:
                # logger.info(part.get_payload().decode() if 'decode' in dir(

                # 寄吧东西套这么多层娃
                # 疑似是树形结构
                # 第一个是总的后面是分段
                # 但对每一个非叶子结点 的 分段载荷都包含了整个子树的内容

                #     part.get_payload(decode=True)) else part.get_payload(decode=True))
                # logger.info(f'分段载荷:  {part.get_payload()}')
                # if type(part.get_payload()) == list:
                #     for miniPart in part.get_payload():
                #         logger.info(f'\t段中载荷: {miniPart.get_payload()}')
                #         if type(miniPart.get_payload()) == list:
                #             for microPart in miniPart.get_payload():
                #                 logger.info(
                #                     f'\t\t双层递归载荷： {microPart.get_payload()}')

                continue

            # 可获取文件名的段载荷 就是 附件内容
            # logger.info(f'可获取文件名的段载荷: {part.get_payload()}')

            # 此处为首次解析的文件名
            # 一般若包含中文需要再次解析
            # logger.info(f'文件名: {file_name}')

            # decode_header 应该就是专门解析这种的 （ 指包含编码以及编码后文本信息的字符串 ）
            filename, decode = decode_header(file_name)[0]
            filename = filename.decode(decode) if decode else str(filename)
            filename = safe_filename(filename)

            # 第二次解析后即为正确文件名
            logger.info('成功读取到附件，文件名: %s' % filename)

            save_dir = f'./emails/{email_id}'
            if not os.path.exists(save_dir):
                os.makedirs(save_dir)

            if os.path.exists(f'{save_dir}/{filename}'):
                continue

            with open(f'{save_dir}/{filename}', 'wb+') as file:
                file.write(part.get_payload(decode=True))

            logger.success(f"成功下载附件: {filename}")
        logger.success(f"{email_id} 处理完成")
    return emails


if __name__ == '__main__':
    client = login()

    get_email_content(client, client.search([u"SINCE", date(*DATE_SINCE)]))
