# 📨 PushPlus 定时推送通知

基于 GitHub Actions 的定时任务，通过 [PushPlus](https://www.pushplus.plus/) 自动推送消息到微信。

## 项目结构

```
scheduled-tasks/
├── .github/
│   └── workflows/
│       └── pushplus-notify.yml   # 定时推送工作流
├── scripts/
│   └── pushplus_notify.py        # PushPlus 推送脚本
├── README.md
└── .gitignore
```

## 快速开始

### 1. 获取 PushPlus Token

1. 访问 [pushplus.plus](https://www.pushplus.plus/)，微信扫码登录
2. 复制页面上显示的 **Token**

### 2. 配置 GitHub Secrets

1. 进入仓库 → `Settings` → `Secrets and variables` → `Actions`
2. 点击 `New repository secret`
3. Name: `PUSHPLUS_TOKEN`，Value: 你的 token

### 3. 完成

推送代码后，工作流会按设定的时间自动发送通知到你的微信。

## 定时规则

默认每天**北京时间 08:00** 发送通知，可在 `pushplus-notify.yml` 中修改：

```yaml
on:
  schedule:
    - cron: '0 0 * * *'    # 每天北京 08:00（UTC 00:00）
    # - cron: '0 12 * * *'  # 每天北京 20:00（UTC 12:00）
    # - cron: '0 1 * * 1'   # 每周一北京 09:00（UTC 01:00）
```

### Cron 表达式速查

```
┌───────────── 分钟 (0 - 59)
│ ┌───────────── 小时 (0 - 23)
│ │ ┌───────────── 日 (1 - 31)
│ │ │ ┌───────────── 月 (1 - 12)
│ │ │ │ ┌───────────── 星期几 (0 - 6，0 是周日)
│ │ │ │ │
* * * * *
```

| Cron 表达式 | 北京时间 |
|------------|---------|
| `0 0 * * *` | 每天 08:00 |
| `0 12 * * *` | 每天 20:00 |
| `30 1 * * 1-5` | 工作日 09:30 |
| `0 1 * * 1` | 每周一 09:00 |
| `0 0 1 * *` | 每月 1 号 08:00 |

## 手动触发

支持在 GitHub Actions 页面手动触发，可自定义标题、内容和模板类型（markdown / html / txt）。

## 自定义通知内容

编辑 `scripts/pushplus_notify.py` 中的 `build_daily_report()` 函数，修改推送的标题和正文内容。

## 注意事项

1. **时区**：GitHub Actions 使用 UTC 时区，北京时间 = UTC + 8
2. **最短间隔**：cron 最短执行间隔为 5 分钟
3. **延迟**：高负载时可能有几分钟延迟
4. **仓库活跃度**：60 天无活动可能导致定时任务被自动禁用
5. **消息模板**：支持 `markdown`、`html`、`txt`、`json` 四种格式
