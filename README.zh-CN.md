# Visual Brief

> 让 AI 不只告诉别人“点哪里”，还把真正要看的按钮、原始链接和成功状态准备好。

Visual Brief 是给 Codex、Claude Code、Cursor 等 AI agent 使用的一套可复用工作流。AI 查完资料或走完网页流程以后，它会截下真正有用的区域，把图片放在对应说明旁边，并生成可以发到 Slack、放进操作指南或整理成公开文章的草稿。

![Visual Brief 生成的合成员工指南](https://joeeeeey.github.io/visual-brief/assets/06-employee-guide-preview.webp)

## 安装

在你平时运行 agent 的项目根目录执行，需要本机已有 Node.js 和 `npx`。

```bash
npx skills add joeeeeey/visual-brief --skill visual-brief --agent '*' --yes
```

这条命令只会为当前项目检测到的 agent 安装轻量的 [`skills/visual-brief`](skills/visual-brief) 目录。安装后重新打开 agent 会话。

## 怎么用

安装以后，直接在 Codex CLI、Claude Code 或其他 agent 里用自然语言描述任务，不需要记特殊命令。

例如：

> 根据 `<安装页面 URL 或资料路径>`，帮我做一份给第一次操作的人看的 macOS 软件安装图文指南。你自己走一遍网页流程，只截真正需要点击的按钮和状态，把图片紧跟在对应步骤下面，保留原始帮助页面链接，并在最后写清楚看到什么才算成功。先生成草稿，不要上传、发送或提交。

## 适用场景

- “帮我在 Slack 里解释为什么现在不能用这个方案，把官网最关键的那句话截出来并标清楚。”
- “把这个后台操作流程整理成新手也能照着完成的图文指南。”
- “把这次研究整理成 V2EX、博客或 X 的图文草稿，事实截图和解释图要明确区分。”

## 默认规则

- 截图放在它所证明或解释的文字旁边。
- 保留原始来源链接，让读者可以自己核对。
- 生成图和关系图只能帮助解释，不能冒充事实证据。
- 默认先生成草稿和预览；发送、上传或发布需要明确批准。
- cookie、token、浏览器登录状态、私有链接和个人数据不能进入仓库。

## 链接

- [查看完整合成案例](https://joeeeeey.github.io/visual-brief/case-study/)
- [阅读 Skill](skills/visual-brief/SKILL.md)
- [English README](README.md)
- [MIT License](LICENSE)
