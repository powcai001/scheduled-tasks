# encoding:utf-8
"""
PushPlus 推送通知脚本
使用 PushPlus (https://www.pushplus.plus/) 发送消息到微信

使用方法:
  1. 在 https://www.pushplus.plus/ 注册并获取 token
  2. 将 token 设置为环境变量 PUSHPLUS_TOKEN 或 GitHub Secrets
  3. 运行脚本: python scripts/pushplus_notify.py
"""

import os
import sys
import json
import requests
from datetime import datetime, timezone, timedelta


# PushPlus API 地址
PUSHPLUS_API = "http://www.pushplus.plus/send"

# 北京时间
BEIJING_TZ = timezone(timedelta(hours=8))


def send_notification(token: str, title: str, content: str, template: str = "html") -> dict:
    """
    通过 PushPlus 发送推送通知

    Args:
        token:    PushPlus token
        title:    消息标题
        content:  消息内容
        template: 消息模板 (html / markdown / txt / json)

    Returns:
        API 响应 JSON
    """
    data = {
        "token": token,
        "title": title,
        "content": content,
        "template": template,
    }
    headers = {"Content-Type": "application/json"}
    body = json.dumps(data).encode("utf-8")

    response = requests.post(PUSHPLUS_API, data=body, headers=headers, timeout=30)
    response.raise_for_status()
    result = response.json()

    if result.get("code") == 200:
        print(f"✅ 推送成功: {title}")
    else:
        print(f"❌ 推送失败: {result.get('msg', '未知错误')}")

    return result


def build_daily_report() -> tuple[str, str]:
    """
    构建每日报告内容 (Markdown 格式)

    Returns:
        (title, content)
    """
    now = datetime.now(BEIJING_TZ)
    title = f"📋 每日定时通知 - {now.strftime('%m月%d日')}"

    content = f"""## 🕐 定时任务执行报告

**执行时间**: {now.strftime('%Y-%m-%d %H:%M:%S')} (北京时间)

**任务状态**: ✅ 正常运行

---

### 📌 任务信息

| 项目 | 详情 |
|------|------|
| 触发方式 | GitHub Actions 定时任务 |
| 执行环境 | ubuntu-latest |
| Python 版本 | {sys.version.split()[0]} |

---

> 💡 此消息由 GitHub Actions 自动发送，如需修改请编辑 `scripts/pushplus_notify.py`
"""
    return title, content


def build_custom_message(title: str, content: str) -> tuple[str, str]:
    """
    构建自定义消息

    Returns:
        (title, content)
    """
    now = datetime.now(BEIJING_TZ)
    formatted_content = f"""## {title}

{content}

---

⏰ 发送时间: {now.strftime('%Y-%m-%d %H:%M:%S')} (北京时间)
"""
    return title, formatted_content


def main():
    # 从环境变量获取 token
    token = os.environ.get("PUSHPLUS_TOKEN")
    if not token:
        print("❌ 错误: 未设置 PUSHPLUS_TOKEN 环境变量")
        print("请在 GitHub 仓库 Settings > Secrets 中添加 PUSHPLUS_TOKEN")
        sys.exit(1)

    # 从环境变量获取自定义标题和内容（可选）
    custom_title = os.environ.get("NOTIFY_TITLE", "")
    custom_content = os.environ.get("NOTIFY_CONTENT", "")
    template = os.environ.get("NOTIFY_TEMPLATE", "markdown")

    if custom_title and custom_content:
        title, content = build_custom_message(custom_title, custom_content)
    else:
        title, content = build_daily_report()

    result = send_notification(token, title, content, template=template)
    print(f"API 响应: {json.dumps(result, ensure_ascii=False, indent=2)}")


if __name__ == "__main__":
    main()
