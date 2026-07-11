# Visual Brief

> 让 AI 不只告诉别人“点哪里”，还把真正要看的按钮和成功状态截图贴好。

Visual Brief 是给 Codex、Claude Code、Cursor 等 AI agent 使用的小 Skill。
AI 查完资料或走完一个网页流程以后，它会截下别人真正需要看的那一小块画面，把图片放在对应说明的下面，再生成可以发到 Slack、放进操作指南或公开教程的草稿。

比如公司要求同事在 Mac 上安装一个设备检查助手。只发一大段文字时，对方常常还会问：“下载哪个？”“权限开对了吗？”“现在算完成了吗？”Visual Brief 会把下载按钮、要打开的权限和最终绿色成功状态排成一页图文说明。

![Visual Brief 生成的合成员工指南](https://joeeeeey.github.io/visual-brief/assets/06-employee-guide-preview.webp)

[查看完整合成案例](https://joeeeeey.github.io/visual-brief/case-study/)。案例不包含真实公司、账号、员工或设备数据。

每一步仍然可以保留原始帮助页面链接：想快速完成的人直接看图，想核对细节的人可以点回原文。

## 安装

```bash
npx skills add joeeeeey/visual-brief --skill visual-brief --agent '*' --yes
```

上面的命令只安装轻量的 `skills/visual-brief` payload，不会把展示站图片、README 图片、示例或评估工作区塞进 agent 环境。

## 三种模式

- `evidence-reply`：用结论、决定性视觉证据、来源和边界回答决策问题。
- `visual-procedure`：把操作步骤、紧邻图片、预期状态和可见成功条件写成指南。
- `public-explainer`：把研究和经验整理成博客、V2EX、X/Twitter 等渠道的图文草稿。

## 安全边界

默认只生成本地草稿、预览和素材。上传、发送、发帖、提交表单或创建公开仓库都需要当前会话中的明确批准。浏览器 storage state、cookie、token、authorization header、真实账号数据和客户数据必须放在仓库外。

英文完整文档请见 [README.md](README.md)，展示页请见 <https://joeeeeey.github.io/visual-brief/>。
