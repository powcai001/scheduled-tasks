# encoding:utf-8
"""
PushPlus 推送通知脚本
读取 data/reminders.json，筛选 status=pending 且 startTime<=当前时间 的任务，
通过 PushPlus 发送微信通知，并将状态回写为 sent / failed。

环境变量:
  PUSHPLUS_TOKEN           — PushPlus token（必填）
  REMINDER_FILE_PATH       — reminders.json 路径，默认 data/reminders.json
  REMINDER_TIMEZONE_OFFSET — 时区偏移（小时），默认 8（北京时间 UTC+8）
"""

import os
import sys
import json
import requests
from datetime import datetime, timezone, timedelta

# PushPlus API 地址
PUSHPLUS_API = "http://www.pushplus.plus/send"


def get_tz(offset_hours: int):
    """根据偏移小时数返回 timezone 对象"""
    return timezone(timedelta(hours=offset_hours))


def send_notification(token: str, title: str, content: str, template: str = "markdown") -> dict:
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


def build_reminder_message(reminder: dict, now: datetime) -> tuple[str, str]:
    """
    根据 reminder 构建推送消息

    Returns:
        (title, content)  —— Markdown 格式
    """
    title = f"⏰ {reminder.get('title', '提醒事项')}"

    task_items = reminder.get("taskItems", [])
    task_list = "\n".join(f"- {item}" for item in task_items) if task_items else "- (无具体事项)"

    content = f"""## {reminder.get('title', '提醒事项')}

{reminder.get('content', '')}

---

### 📋 任务清单

{task_list}

---

| 项目 | 详情 |
|------|------|
| 提醒 ID | `{reminder.get('id', '-')}` |
| 计划时间 | {reminder.get('startTime', '-')} |
| 发送时间 | {now.strftime('%Y-%m-%d %H:%M:%S')} |

> 💡 此消息由 GitHub Actions 自动发送
"""
    return title, content


def load_reminders(file_path: str) -> list:
    """读取 reminders.json，返回列表"""
    if not os.path.exists(file_path):
        print(f"⚠️ 文件不存在: {file_path}，返回空列表")
        return []
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        print(f"⚠️ 文件内容不是数组，返回空列表")
        return []
    return data


def save_reminders(file_path: str, reminders: list):
    """将 reminders 列表写回 JSON 文件"""
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(reminders, f, ensure_ascii=False, indent=2)
    print(f"💾 已回写 {file_path}（共 {len(reminders)} 条记录）")


def parse_start_time(start_time_str: str, tz) -> datetime | None:
    """
    解析 startTime 字符串，支持 'YYYY-MM-DD HH:MM' 格式
    返回带时区的 datetime，解析失败返回 None
    """
    for fmt in ("%Y-%m-%d %H:%M", "%Y-%m-%d %H:%M:%S"):
        try:
            dt = datetime.strptime(start_time_str, fmt)
            return dt.replace(tzinfo=tz)
        except ValueError:
            continue
    return None


def main():
    # ── 读取环境变量 ──
    token = os.environ.get("PUSHPLUS_TOKEN")
    if not token:
        print("❌ 错误: 未设置 PUSHPLUS_TOKEN 环境变量")
        sys.exit(1)

    file_path = os.environ.get("REMINDER_FILE_PATH", "data/reminders.json")
    tz_offset = int(os.environ.get("REMINDER_TIMEZONE_OFFSET", "8"))
    tz = get_tz(tz_offset)

    # ── 加载任务 ──
    reminders = load_reminders(file_path)
    if not reminders:
        print("📭 无任务，退出")
        return

    now = datetime.now(tz)
    print(f"🕐 当前时间: {now.strftime('%Y-%m-%d %H:%M:%S')} (UTC{tz_offset:+d})")

    sent_count = 0
    fail_count = 0
    skip_count = 0

    for reminder in reminders:
        # 只处理 pending 状态
        if reminder.get("status") != "pending":
            continue

        start_time_str = reminder.get("startTime", "")
        start_dt = parse_start_time(start_time_str, tz)
        if start_dt is None:
            print(f"⚠️ 跳过: 无法解析 startTime '{start_time_str}'，id={reminder.get('id')}")
            skip_count += 1
            continue

        # startTime 必须 <= 当前时间
        if start_dt > now:
            skip_count += 1
            continue

        # ── 构建并发送 ──
        title, content = build_reminder_message(reminder, now)
        try:
            result = send_notification(token, title, content, template="markdown")
            if result.get("code") == 200:
                reminder["status"] = "sent"
                reminder["sentAt"] = now.isoformat()
                sent_count += 1
            else:
                reminder["status"] = "failed"
                reminder["failReason"] = result.get("msg", "未知错误")
                fail_count += 1
        except Exception as e:
            print(f"❌ 发送异常: {e}")
            reminder["status"] = "failed"
            reminder["failReason"] = str(e)
            fail_count += 1

    # ── 回写文件 ──
    save_reminders(file_path, reminders)

    print(f"\n📊 本轮统计: 发送成功 {sent_count} | 失败 {fail_count} | 跳过 {skip_count}")

    if fail_count > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
