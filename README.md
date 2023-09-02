# WhisperByEmail
## ## 使用Whisper识别邮件中音频文件

---

1. ## 配置

   - 安装依赖

   ~~~bash
   pip install -r requirements.txt
   ~~~

   - 根据是否使用GPU 安装 [PyTorch](https://pytorch.org)

2. ## 使用

   1. 配置`SETTINGS.json`
   2. 编辑`SETTINGS.json.tmplate`, 补充配置文件
      - `IMAP_SERVER`: 邮箱 imap 服务器地址
      - `SMTP_HOST`: 邮箱 smtp 服务器地址
      - `MAIL_USER`: 接收并发送邮件的用户名 (如`114514@1919810.com`)
      - `MAIL_PASS`: 邮箱 **授权码** 
      - `WHITE_LIST`: 白名单列表 (目前仅支持使用白名单)
      - `ADMIN_ACCOUNT`: 管理员邮箱， 非管理员使用时会向管理员邮箱发送提示
      - `TOAST_ICON_PATH`(可选): 发送 win10 Toast通知时的图标，可不填， 默认为`terminal.ico`
   3. 启动`邮件日记.py`
   4. 自动下载并语音识别邮箱中 **白名单用户** 发送的邮件中的含音频流的附件，保存至`./emails/{email_id}/` 目录下，识别完成后自动向请求的用户发送识别结果邮件 
   5. (可选) 配置开机自启动，开机自动识别邮箱中邮件的附件