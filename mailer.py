# -*- coding: utf-8 -*-
"""SMTP mailer. Credentials come from config (env vars). Sends the HTML report
and attaches the annotated chart SVGs (feature b)."""
import os, smtplib
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart


def send_email(html_body, subject, email_cfg, attachments=None):
    attachments = attachments or []
    host = email_cfg.get("smtp_host")
    user = email_cfg.get("smtp_user")
    pwd = email_cfg.get("smtp_pass")
    sender = email_cfg.get("from_addr") or user
    recipients = email_cfg.get("to_addrs") or []
    if not (host and user and pwd and sender and recipients):
        raise RuntimeError("Email not configured: set CAH_SMTP_* / CAH_EMAIL_* env vars (see config.py).")

    msg = MIMEMultipart("related")
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = ", ".join(recipients)
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    for path in attachments:
        if not os.path.exists(path):
            continue
        try:
            with open(path, "rb") as fh:
                img = MIMEImage(fh.read(), "svg+xml")
            img.add_header("Content-Disposition", "attachment",
                           filename=os.path.basename(path))
            msg.attach(img)
        except Exception as e:
            print("  attachment failed for", path, ":", e)

    port = email_cfg.get("smtp_port", 587)
    with smtplib.SMTP(host, port, timeout=30) as s:
        if email_cfg.get("use_tls", True):
            s.starttls()
        s.login(user, pwd)
        s.sendmail(sender, recipients, msg.as_string())
    return True
