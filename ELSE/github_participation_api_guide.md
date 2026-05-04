# GitHub 公开仓库参与链数据：可行性、API 与字段说明

可以，而且对 **公开 repo** 来说，数据总体上是 **足够做“参与链”** 的；但要先把“链里的时间”定义清楚。因为 GitHub 里至少有两种时间：一种是 **Git 提交时间**，来自 commit 对象里的 `author.date` / `committer.date`；另一种是 **GitHub 平台上发生事件的时间**，来自事件流里的 `created_at`。如果你想研究“代码实际何时被写/提交”，看 commit 时间；如果你想研究“平台上的协作先后顺序”，例如谁先 push、谁后开 PR、谁再 review，就要看事件时间。([GitHub REST API: Commits](https://docs.github.com/en/rest/commits/commits))

## 结论

**能拿到** 你举的这种链，例如“创建者 A → 贡献者 B commit → 贡献者 C 提 PR → D review → E comment ……”。

但 **最好不要只靠一个 API**。对于每个选定 repo，最稳的做法是把这几类源拼起来：

1. repo 元数据拿仓库创建时间；
2. commit 接口拿完整历史提交；
3. PR 接口和 PR timeline 拿 `opened` / `closed` / `merged` / `review` / `comment` 等；
4. 如果要“谁在 GitHub 上何时触发了哪个事件”的统一事件流，就加 **GH Archive**，因为它从 2011 年开始按小时归档公开 GitHub timeline，而且每条事件本身就有 `actor`、`repo`、`payload`、`created_at`。([GH Archive](https://www.gharchive.org/), [GH Archive GitHub Repo](https://github.com/igrigorik/gharchive.org))

最重要的一个限制是：**GitHub 原生 Events API 不适合回溯长期历史。** 官方写明了，事件时间线 **最多 300 条**，而且 **只包含最近 30 天**，并且还有 30 秒到 6 小时不等的延迟。所以如果你的研究是 2025、2024 甚至更早的全球开源协作链，不能只靠 `/events`；历史部分应优先用 **GH Archive**，再按需用 REST API 回填细节。([GitHub REST API: Events](https://docs.github.com/v3/activity/events))

---

## 1. repo 创建：能拿到什么

如果你只需要“这个 repo 什么时候创建”，直接用：

```http
GET /repos/{owner}/{repo}
```

字段看：`created_at`。仓库对象里还会给 `pushed_at`、`updated_at`。公开仓库可以不登录访问。([GitHub REST API: Repos](https://docs.github.com/en/rest/repos/repos?apiVersion=2026-03-10))

但如果你要的是你例子里那种 **“创建者 A，某日，操作类型：创建”**，这里要小心：

`GET /repos/{owner}/{repo}` 能稳定给你 `created_at`，但 **不一定可靠告诉你历史上的“创建者”是谁**，因为仓库可能后来转移 owner。要更稳地恢复“最初是谁触发创建”，更适合找历史 **CreateEvent**，其中 `payload.ref_type` 可以是 `repository`；GH Archive 保存的就是这类公开历史事件。([GitHub Event Types](https://docs.github.com/en/rest/using-the-rest-api/github-event-types))

所以这一行建议这样取：

- `operation_type = "create"`
- `operation_time = repo.created_at` 或 `CreateEvent.created_at`
- `actor = CreateEvent.actor.login`

如果没有历史事件，再退化为当前 `owner.login`，但要标注“可能不是原始创建者”。

---

## 2. commit：能不能拿完整历史，字段是什么

可以。完整提交历史应主要用：

```http
GET /repos/{owner}/{repo}/commits
```

这个接口支持按 `sha`、`author`、`committer`、`since`、`until` 过滤，并支持分页。公开仓库也能直接读。([GitHub REST API: Commits](https://docs.github.com/en/rest/commits/commits))

这里最关键的字段是 commit 对象里的：

- `commit.author.date`
- `commit.committer.date`
- 以及 author / committer 的身份信息

GitHub 的 Git commit 文档明确说明，`author.date` 和 `committer.date` 都是 ISO 8601 时间戳。([GitHub REST API: Git Commits](https://docs.github.com/rest/git/commits))

但研究时要分清：

- `author.date` 更像“作者声称写下这次提交的时间”；
- `committer.date` 更像“这个提交对象最终被提交的时间”；
- 如果你研究的是“什么时候进入 GitHub 平台并被别人看到”，那还不够，你还要看 **PushEvent** 的 `created_at`，因为 PushEvent 表示“一个或多个 commit 被推送到某个分支或 tag”，并给出 `ref`、`head`、`before` 等字段。([GitHub Event Types](https://docs.github.com/en/rest/using-the-rest-api/github-event-types))

因此你可以有两种链：

- **Git 链**：`actor = commit author/committer`，`time = commit.author.date` 或 `commit.committer.date`
- **平台链**：`actor = PushEvent.actor.login`，`time = PushEvent.created_at`，再从 `payload.head` / `before` / `ref` 或提交列表把 push 和 commit 连起来

---

## 3. PR：opened / closed / merged 能不能拿到

可以，PR 相关的主入口是：

```http
GET /repos/{owner}/{repo}/pulls
GET /repos/{owner}/{repo}/pulls/{pull_number}
```

GitHub 还明确说明，PR 有链接关系指向它的 issue comments、review comments、commits、statuses，这很适合把一条 PR 链继续展开。([GitHub REST API: Pull Requests](https://docs.github.com/rest/pulls/pulls))

如果你要的是“统一事件链”的视角，那么 **PullRequestEvent** 更直接：

- 事件顶层有 `created_at`，表示这个事件何时触发；
- `payload.action` 可取 `opened`、`closed`、`merged`、`reopened`、`assigned`、`unassigned`、`labeled`、`unlabeled`；
- `payload.number` 是 PR 编号；
- `payload.pull_request` 是对应 PR 对象。([GitHub Event Types](https://docs.github.com/en/rest/using-the-rest-api/github-event-types))

所以你要的这一行可以直接落成：

- `actor = event.actor.login`
- `operation_time = event.created_at`
- `operation_type = "pr_opened"` 或 `"pr_closed"` / `"pr_merged"`
- `object_id = payload.number`
- `object_type = "pull_request"`

---

## 4. review：谁在什么时候 review 了 PR

这个非常适合你的“合作链”。用：

```http
GET /repos/{owner}/{repo}/pulls/{pull_number}/reviews
```

官方明确写了：返回结果 **按时间顺序** 排列。示例响应里直接有：

- `user.login`
- `state`，例如 `APPROVED`
- `submitted_at`
- `commit_id`

([GitHub REST API: Pull Request Reviews](https://docs.github.com/rest/pulls/reviews))

所以 review 行可以直接记成：

- `actor = review.user.login`
- `operation_time = review.submitted_at`
- `operation_type = "review_" + lower(state)`
- `pr_number = pull_number`
- `commit_sha = review.commit_id`

如果你想用统一事件流而不是单独 reviews 接口，也有 **PullRequestReviewEvent**，其中 `payload.action` 可为 `created`、`updated`、`dismissed`。([GitHub Event Types](https://docs.github.com/en/rest/using-the-rest-api/github-event-types))

---

## 5. comment：PR 评论、issue 评论、review comment

这一层建议分三种，不要混。

### 5.1 PR / issue 时间线评论

因为 GitHub 把 PR 视作一种 issue，所以很多“共享动作”都走 Issues / Timeline API。官方明确说，timeline events 可查看 issues 和 pull requests 的时间线活动：

```http
GET /repos/{owner}/{repo}/issues/{issue_number}/timeline
```

([GitHub REST API: Timeline](https://docs.github.com/en/rest/issues/timeline))

在 timeline / issue event 体系里，`commented` 事件会给：

- `user`
- `created_at`
- `body`
- `event = "commented"`

([GitHub Issue Event Types](https://docs.github.com/en/rest/using-the-rest-api/issue-event-types))

### 5.2 review

review 已在上一节说明，用 reviews 接口拿 `submitted_at` 和 `state`。([GitHub REST API: Pull Request Reviews](https://docs.github.com/rest/pulls/reviews))

### 5.3 review comment

GitHub 在 PR 文档里明确区分了普通 issue comments 和 review comments，PR 对象也有 `review_comments` 链接关系。事件流中对应的是 **PullRequestReviewCommentEvent**，其 `payload.action` 为 `created`，并带 `pull_request` 与 `comment` 对象。([GitHub REST API: Pull Requests](https://docs.github.com/rest/pulls/pulls), [GitHub Event Types](https://docs.github.com/en/rest/using-the-rest-api/github-event-types))

---

## 6. 还能拿到哪些“合作链”节点

如果你不仅要 `commit` / `PR` / `review` / `comment`，还想把协作链扩成更完整的治理链，Timeline API 其实很有用。官方列出的事件类型里，和 PR / issue 强相关的就包括：

- `assigned`
- `commented`
- `committed`
- `cross-referenced`
- `head_ref_force_pushed`
- `merged`
- `review_requested`
- `review_request_removed`
- `reopened`
- `closed`

这些事件基本都有 `actor` 和 `created_at`，有些还会给 `commit_id`、`source`、`review` 等扩展字段。([GitHub Issue Event Types](https://docs.github.com/en/rest/using-the-rest-api/issue-event-types))

例如：

- `committed`：表示“有 commit 被加到 PR 的 HEAD 分支”，会给 `sha`、`author`、`committer`、`message`
- `merged`：表示 PR 被 merge，会给 `created_at`，并说明 `commit_id` 是被 merge 的 HEAD commit 的 SHA
- `cross-referenced`：表示另一个 issue/PR 引用了它，会给 `source` 和 `created_at`

---

## 7. 你这个研究里，数据到底“够不够”

**够，但有边界。** 对公开 repo 来说，你完全可以构造一条比较完整的“参与链”，至少包括：

- repo 创建
- push
- commit
- PR opened / closed / merged
- review
- issue / PR comment
- review comment
- cross-reference
- force-push
- review request

GH Archive 给你跨全站的统一历史事件骨架；REST API 给你 repo / PR 级别的细粒度补全。([GH Archive](https://www.gharchive.org/))

但也有四个常见缺口：

1. **私有仓库拿不到**，这里讨论的是公开数据；
2. **创建者不总能从当前 repo 对象准确恢复**，仓库转移 owner 后尤其如此，因此最好保留历史 `CreateEvent`；
3. **commit 时间不等于 push 时间**，做时序因果时一定要选对时间定义；
4. **只靠 GitHub Events API 拿不到长历史**，因为它只有 30 天 / 300 条。([GitHub REST API: Events](https://docs.github.com/v3/activity/events))

---

## 8. 实际落库时建议至少保留这些字段

你可以统一做成一张 `repo_participation_chain`：

- `repo_id`, `repo_name`
- `actor_id`, `actor_login`
- `event_time`
- `event_type`
- `object_type`：`repository` / `commit` / `pull_request` / `review` / `comment`
- `object_id`：PR number、review id、comment id、commit sha
- `parent_object_id`：例如 review/comment 所属 PR
- `source_api`：`repo`, `commits`, `pulls`, `timeline`, `reviews`, `gharchive`
- `raw_action`：如 `opened`, `merged`, `approved`, `commented`
- `branch_ref`, `before_sha`, `after_sha`（对 push 很有用）
- `author_login`, `committer_login`（commit 时 author/committer 可能不同）

这些字段都能由上面那几组接口直接或间接支撑。([GitHub Event Types](https://docs.github.com/en/rest/using-the-rest-api/github-event-types))

---

## 9. 你的例子，推荐的取法

你给的例子：

1. 创建者 A，2025-10-01，创建  
2. 贡献者 B，2025-10-02，commit  
3. 贡献者 C，2025-10-03，PR

我建议对应成：

- **创建**：优先 `CreateEvent(actor.login, created_at, payload.ref_type=repository)`；没有时退化为 `GET /repos/{owner}/{repo}` 的 `created_at`
- **commit**：如果研究 Git 历史，用 `GET /repos/{owner}/{repo}/commits` 的 commit author / committer 与时间；如果研究 GitHub 平台协作时序，用 `PushEvent.actor.login + created_at`，再把 push 里的提交映射进去
- **PR**：用 `PullRequestEvent.actor.login + created_at + payload.action + payload.number`；如需补细节，再拉 pulls / timeline / reviews

---

## 10. 一句最实用的建议

如果你的目标是“**每个选定 repo 的完整参与链**”，最稳的工程方案不是“只用 GitHub API”，而是：

**GH Archive 拉历史公开事件骨架**  
+ **REST API 回填每个 repo 的 commits / pulls / timeline / reviews**。

([GH Archive](https://www.gharchive.org/))
