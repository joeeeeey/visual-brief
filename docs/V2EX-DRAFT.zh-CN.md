# V2EX Draft: Visual Brief

> Status: draft only. No image has been uploaded and no post has been published.

## Recommended title

我做了一个给 AI 用的 Skill：让“我查过了”变成别人能快速核验的图文说明

## Post body

我最近越来越强烈地感觉到，AI 协作里很多卡住的地方，根本不是“信息不够”。

更常见的是：我已经看过一堆资料，脑子里有了结论；但另一个人只收到一句“我建议这么做”。他要么相信我，要么重新从十几个链接里翻一遍。两边的上下文根本不对称。

所以我做了一个叫 **Visual Brief** 的 Skill。

它不是让 AI 多截几张图，而是让 AI 把真正决定判断的那一小段截图或界面状态、对应的可追溯来源链接，以及一段面向读者写的短解释，按读者能看懂和核验的顺序放进同一个包里。

![图 1：协作真正的断层通常是上下文不对称，而不是资料数量](https://joeeeeey.github.io/visual-brief/assets/01-context-gap.webp)

我很在意两件看起来有点拧巴、但其实必须同时成立的事：

- 截图能让人很快看到“你到底在说哪一句、哪个按钮、哪个状态”，降低检查成本；
- 但截图不是来源。读者仍然应该能点开 canonical link，去核对、追问，甚至反驳这个结论。

生成图和关系图也很好用，不过它们只能帮助解释，不能伪装成事实证据。

![图 2：一句主张、决定性视觉素材和 canonical link 各自承担不同职责](https://joeeeeey.github.io/visual-brief/assets/02-claim-visual-source.webp)

现在这个 Skill 先支持三种我自己最常遇到的场景：

1. **evidence-reply**：比如有人问“为什么不采用这个方案？”。先给结论，再放最关键的证据图和来源，而不是甩一堆链接。
2. **visual-procedure**：比如员工要登录、下载、安装、授权、等待同步。每一步后面紧跟图片、预期会看到什么，以及最后怎样算成功。
3. **public-explainer**：把研究和经验整理成博客、V2EX、X/Twitter 这类图文说明。真实截图、图解和生成图会明确区分，事实主张保留来源和边界。

![图 3：三种模式，分别服务于决策回复、操作指南和公开讲解](https://joeeeeey.github.io/visual-brief/assets/03-three-modes.webp)

还有一个我觉得挺重要但不那么“炫”的设计：默认只生成本地草稿、图片和预览，不会自己上传、发 Slack、发帖或者创建公开仓库。浏览器登录状态、cookie、token 之类的东西也明确放在仓库外，当作凭据处理。

这个仓库把 Skill 的安装内容和展示内容分开：

```bash
npx skills add joeeeeey/visual-brief --skill visual-brief --agent '*'
```

安装时拿到的是轻量的 `visual-brief` Skill，不需要把 README 的展示图、网站素材或评估工作区都拉到 agent 环境里。README 里的图文展示放在 GitHub Pages 上。

![图 4：轻量安装 payload 和公开展示站分层](https://joeeeeey.github.io/visual-brief/assets/04-lightweight-install.webp)

仓库：<https://github.com/joeeeeey/visual-brief>

展示页：<https://joeeeeey.github.io/visual-brief/>

里面目前放的是合成、脱敏的示例，不含真实账号、客户数据或内部截图。

我比较想听听大家对这几个问题的看法：

- 截图和来源链接，怎样组合才既快又不失可审计性？
- 这种 `source -> claim -> asset -> output` 的 artifact contract 有没有更好的做法？
- 对操作型教程来说，“最后可见的成功状态”是不是比“最后点了哪个按钮”更重要？

## Publish gate

Before using this draft, verify the account, final title, complete text, four
images, and public URLs. Obtain explicit approval immediately before the final
publish action.
