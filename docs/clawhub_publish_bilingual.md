# ClawHub Publish Copy (EN + 中文)

## Display Name

`X Growth Operator / X 增长运营助手`

## Short Description (EN + 中文)

Review-first X growth operations skill that turns a brief into a mission, finds opportunities, drafts actions, and executes only after explicit approval / 一个“先审核后执行”的 X 增长运营 Skill：把 brief 转成 mission，发现机会、起草动作，并仅在明确批准后执行。

## Full Description (EN)

X Growth Operator is a review-first skill for running mission-driven X operations.

It can:
- parse structured or freeform briefs into a mission
- infer watch focus from goals, topics, audience, and constraints
- import opportunities from local files, manual surf notes, or live Desearch search
- score and rank opportunities with rationale
- draft post / reply / quote_post actions
- run interaction preflight checks before sensitive actions
- execute approved actions through official X OAuth credentials
- persist local audit logs and memory signals

Safety model:
- default mode is review-first
- live execution requires explicit approval and x-api mode
- high-risk or low-fit opportunities can be routed to observe

## 详细描述（中文）

X Growth Operator 是一个基于 mission 的 X 运营 Skill，默认“先审核后执行”。

它可以：
- 将结构化或自由文本 brief 解析为 mission
- 从目标、话题、受众和约束自动推导关注范围
- 从本地文件、手动冲浪笔记或 Desearch 实时搜索导入机会
- 给机会打分、排序并给出理由
- 生成 post / reply / quote_post 草稿
- 在互动动作前执行 preflight 预检查
- 通过官方 X OAuth 凭证执行已批准动作
- 持久化本地执行日志与记忆信号

安全模型：
- 默认 review-first
- 真实执行要求显式批准并使用 x-api 模式
- 高风险或低匹配机会会降级为 observe

## Required Environment Variables

- `X_API_KEY`
- `X_API_SECRET`
- `X_ACCESS_TOKEN`
- `X_ACCESS_TOKEN_SECRET`
- `DESEARCH_API_KEY` (optional; only needed for live Desearch search/import)

## Install / Runtime Declaration

- Install step: `cd scripts && npm install`
- Network targets:
  - `https://api.twitter.com`
  - `https://api.x.com`
- Local state paths:
  - `data/`
  - `scripts/.env`

## Changelog (v1.0.2) EN

- Added explicit runtime/security declarations to reduce registry scan ambiguity.
- Declared required OAuth environment variables and optional Desearch key.
- Declared install step and network targets.
- Disabled implicit invocation in metadata.
- Removed unused `twitter-api-v2` dependency and aligned env checks to current runtime.

## 更新说明（v1.0.2）中文

- 补充了运行与安全声明，降低平台扫描误判。
- 明确声明了必需 OAuth 环境变量和可选 Desearch Key。
- 明确声明安装步骤与外部网络目标。
- 在元数据中关闭了隐式自动调用。
- 移除未使用的 `twitter-api-v2` 依赖，并同步更新环境检查逻辑。
