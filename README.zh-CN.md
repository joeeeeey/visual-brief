# Visual Brief

把查资料和走网页流程的结果，整理成别人一看就能照着做的图文说明。Visual Brief 会截下真正关键的句子、按钮、设置或成功状态，保留原始链接，并把图片放在对应文字旁边。

![Visual Brief 生成的英文合成员工指南](https://joeeeeey.github.io/visual-brief/assets/08-employee-guide-preview-en.webp)

## 安装

本机有 Node.js/npm 后，在项目根目录执行：

```bash
npx skills add joeeeeey/visual-brief --skill visual-brief --agent '*' --yes
```

只会安装轻量的 [`skills/visual-brief`](skills/visual-brief) 目录。安装后在这个项目里重新打开助手。

## 怎么用

直接粘贴这样的自然语言任务：

> 根据 `<安装页面 URL 或资料路径>`，帮我做一份给第一次操作的人看的 macOS 软件安装图文指南。你自己走一遍网页流程，只截真正需要点击的按钮和状态，把图片紧跟在对应步骤下面，保留原始帮助页面链接，并在最后写清楚看到什么才算成功。先生成草稿，不要上传、发送或提交。

## 适用场景

- “帮我在 Slack 里解释为什么现在不能用这个方案，把官网最关键的那句话截出来并标清楚。”
- “把这个后台操作流程整理成新手也能照着完成的图文指南。”
- “把这次研究整理成 V2EX、博客或 X 的图文草稿，事实截图和解释图要明确区分。”

默认只做草稿：未经确认不发送、上传或发布，浏览器登录状态和私有数据不进入仓库。

[英文案例](https://joeeeeey.github.io/visual-brief/case-study/en.html) · [阅读 Skill](skills/visual-brief/SKILL.md) · [English README](README.md) · [MIT](LICENSE)
