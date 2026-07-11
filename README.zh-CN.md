# Visual Brief

> 把你已经理解的上下文，变成别人可以快速检查的说明。

Visual Brief 是给 Codex、Claude Code、Cursor 等 AI agent 使用的证据驱动视觉沟通 skill。它把来源、关键截图或图解、以及面向读者的解释组织成一个可审阅的包。

截图降低检查成本；canonical link 保留核对和反驳的路径。两者缺一不可。

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
