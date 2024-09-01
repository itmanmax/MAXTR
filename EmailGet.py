# -*- coding: utf-8 -*-
import imaplib
import email
from email.header import decode_header
from email.utils import parsedate_to_datetime
import requests
import time
import re

imap_server = ''
username = ''
password = ''
qmsg_key = ''
qq_number = ''

# 数字到指纹汉字的映射
digit_to_chinese = {
    '0': '零',
    '1': '一',
    '2': '二',
    '3': '三',
    '4': '四',
    '5': '五',
    '6': '六',
    '7': '七',
    '8': '八',
    '9': '九'
}

def convert_digits_to_chinese(name):
    # 统计名称中阿拉伯数字的数量
    digits_count = sum(c.isdigit() for c in name)
    if digits_count >= 2:
        # 替换阿拉伯数字为指纹汉字
        name = ''.join(digit_to_chinese.get(c, c) for c in name)
    return name

# 连接到IMAP服务器
mail = imaplib.IMAP4_SSL(imap_server)

# 登录邮箱
mail.login(username, password)

# 选择收件箱
mail.select('inbox')

# 检查是否有未读邮件
status, email_data = mail.search(None, 'UNSEEN')

# 如果有未读邮件，发送Qmsg通知
if email_data[0]:
    print("您有新邮件！")
    for e_id in email_data[0].split():
        # 获取邮件内容
        status, data = mail.fetch(e_id, '(RFC822)')
        raw_email = data[0][1]
        email_message = email.message_from_bytes(raw_email)

        # 获取发件人
        sender, encoding = decode_header(email_message['From'])[0]
        if isinstance(sender, bytes):
            sender = sender.decode(encoding if encoding else 'utf-8', errors='replace')

        # 如果发件人名称中包含两个以上的阿拉伯数字，则将其转换为指纹汉字
        sender = convert_digits_to_chinese(sender)

        # 获取邮件主题
        subject, encoding = decode_header(email_message['Subject'])[0]
        if isinstance(subject, bytes):
            subject = subject.decode(encoding if encoding else 'utf-8', errors='replace')

        # 获取邮件纯文本内容
        text_content = ''
        for part in email_message.walk():
            if part.get_content_type() == 'text/plain':
                text_content = part.get_payload(decode=True).decode(part.get_content_charset() or 'utf-8', errors='replace')
                break

        # 获取邮件时间
        date_str = email_message['Date']
        email_date = parsedate_to_datetime(date_str).strftime('%Y-%m-%d %H:%M:%S') if parsedate_to_datetime(date_str) else '未知时间'

        # 构建推送消息内容
        msg = f"你有新邮件：发件人[{sender}], 邮件主题是[{subject}], 邮件文本内容是[{text_content}], 邮件发送时间是[{email_date}]"

        # 发送消息到Qmsg酱
        postdata = {
            'msg': msg,
            'qq': qq_number
        }
        response = requests.post(f'https://qmsg.zendee.cn/send/{qmsg_key}', data=postdata)
        if response.status_code == 200:
            print("通知已发送到QQ。")
        else:
            print(f"通知发送失败，错误码：{response.status_code}，响应内容：{response.text}")

        # 添加延时，避免推送过快
        time.sleep(5)

else:
    print("没有新邮件。")

# 退出登录
mail.logout()
