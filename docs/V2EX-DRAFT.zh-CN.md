# V2EX Draft: Visual Brief

> Status: draft only. No post has been published.

## Recommended title

我做了个小 Skill：让 AI 不只告诉你“点哪里”，还会把每一步截图贴好

## Post body

前阵子我碰到一个很小、但特别磨人的场景。

假设公司要求每个同事在 Mac 上装一个设备检查小助手。流程听起来不复杂：登录员工页面、下载安装包、装好以后去系统设置开权限、等它同步，最后确认页面显示成功。

但真的把说明发给同事时，问题就来了：

“下载哪个版本？”

“系统设置到底要点哪里？”

“权限已经开了，为什么页面还没变绿？”

“我现在这样算完成了吗？”

我以前的做法，通常是丢一个帮助链接，再补一大段文字。就算让 AI 来写，很多时候也只是把这段文字写得更完整。

内容可能没错，但第一次操作的人还是得自己打开网页、找按钮、对照设置，然后猜我说的“完成”到底长什么样。

所以我做了一个叫 **Visual Brief** 的小 Skill。

这里说的 Skill 不是一个新的 App，更像是装进 Codex、Claude Code 这类 AI 助手里的一套工作方法。

它解决的其实就是一个很具体的问题：AI 根据你指定或审核过的官方页面整理完资料以后，不要只把答案写成文字。它还会顺手打开相关页面，只截真正要看的按钮、开关和成功状态，再排成一份可以直接发给别人的图文说明。

下面这个例子是我专门做的完全合成演示，不是真实公司的后台，也没有任何员工、账号或设备信息。

第一步，AI 走到员工下载页面。它不会扔给读者一张塞满无关内容的超长截图，而是保留足够的页面背景，再把真正要点的 `Download for macOS` 按钮框出来。

![合成演示：AI 只保留员工真正需要点击的下载区域](https://joeeeeey.github.io/visual-brief/assets/05-employee-portal-download.webp)

但最后生成出来的也不是一个乱七八糟的截图文件夹。

它会把整套流程排成一页很简单的指南：一句话说清楚要做什么，图片紧跟在这句话下面；做完一步，再看下一步。

![合成演示：AI 生成的三步员工图文指南](https://joeeeeey.github.io/visual-brief/assets/06-employee-guide-preview.webp)

我觉得这里最容易被忽略的是最后一步。

很多教程写到“点了安装”或者“打开了权限”就结束了，但真正第一次操作的人需要知道：做到什么样才算完成？

所以指南最后会明确告诉他，回到员工页面，等到绿色的 `Device check complete` 出现，才是真的好了。

![合成演示：最后可见的成功状态](https://joeeeeey.github.io/visual-brief/assets/07-device-check-complete.webp)

真实使用时，每一步下面还会保留原始帮助页面的链接。想快速完成的人直接看图；想确认细节的人，可以点回原网页自己核对。

图里的 `Full Disk Access` 只是合成示例，不是让 AI 自己决定该给哪个软件权限。真实流程必须来自组织已经审核的软件和官方说明。

同样的做法也可以用在 Slack 里。比如有人问“为什么这个方案现在不能用”，AI 不只发一段结论，还会把官方网站上最关键的那句话截出来、标出来，并把原网页链接放在旁边。

它不会替员工偷偷安装软件，也不会自己把内容发出去。它自动做的是查资料、挑重点、截图、裁剪和排版，最后先生成一份草稿给人检查。

真实浏览器的登录状态、cookie 和个人信息也不会放进仓库。截图在分享前要先检查和脱敏，最终发送或发布仍然需要人确认。

项目已经开源：<https://github.com/joeeeeey/visual-brief>

完整合成案例：<https://joeeeeey.github.io/visual-brief/case-study/>

如果你的 AI 工具支持 Skills，可以先看看仓库里有哪些 Skill：

```bash
npx skills add joeeeeey/visual-brief --list
```

README 里放了 Codex、Claude Code 和其他 Agent 的具体安装命令。

我现在比较好奇的是，大家平时有没有遇到这种情况：AI 的答案其实是对的，但你把它发给同事以后，对方还是不知道下一步该点哪里？

## Publish gate

Before using this draft, verify the account, final title, complete text, three
images, and public URLs. Obtain explicit approval immediately before the final
publish action.
