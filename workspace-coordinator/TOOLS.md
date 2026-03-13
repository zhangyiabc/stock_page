# TOOLS.md - 盘古 · 协调者

## 可用工具

### Session 工具（核心）
- `sessions_list`：列出所有活跃 Agent 会话
- `sessions_history`：查看指定 Agent 的对话历史
- `sessions_send`：向其他 Agent 发送消息并等待回复
- `sessions_spawn`：生成子 Agent 任务

### 消息工具
- `message`：向飞书群发送消息

## Agent 通信约定

向其他 Agent 发消息时，使用以下前缀标识任务类型：

- `[ANALYZE:{股票代码}]` → researcher：分析指定股票
- `[SCREEN]` → researcher：选股筛选
- `[SENTIMENT_CHECK:{股票列表}]` → researcher：舆情检查
- `[STRATEGY:{分析数据}]` → strategist：策略评估
- `[REGISTER:{open_id}:{name}]` → portfolio-mgr：注册投资者
- `[ADD_WATCHLIST:{open_id}:{ticker}]` → portfolio-mgr：添加自选
- `[TRADE:{open_id}:{action}:{ticker}:{qty}]` → portfolio-mgr：模拟交易
- `[POSITIONS:{open_id}]` → portfolio-mgr：查询持仓
- `[ALL_POSITIONS]` → portfolio-mgr：查询全体持仓
- `[DAILY_RANKING:{date}]` → portfolio-mgr：生成收益排行

## 飞书群信息

- 群 ID：待配置（格式 oc_xxx）
- Bot 名称：盘古
- 投资者 @提及格式：使用飞书 open_id
