# 交易策略库

本目录存放 YAML 格式的交易策略定义文件。策略师 agent（鬼谷）在分析股票时会加载对应策略。

## 策略列表

| 文件 | 名称 | 类型 | 适用场景 |
|------|------|------|---------|
| ma_golden_cross.yaml | 均线金叉 | 趋势 | 趋势启动初期，MA5 上穿 MA10 |
| bull_trend.yaml | 多头趋势 | 趋势 | 趋势持续阶段，多头排列加仓 |
| volume_breakout.yaml | 放量突破 | 趋势 | 突破关键阻力位 + 放量确认 |
| shrink_pullback.yaml | 缩量回调 | 趋势 | 上升趋势中缩量回踩均线低吸 |
| bottom_volume.yaml | 底部放量 | 反转 | 长期下跌后底部异常放量 |
| box_oscillation.yaml | 箱体震荡 | 框架 | 横盘震荡区间高抛低吸 |
| emotion_cycle.yaml | 情绪周期 | 框架 | 基于市场/个股情绪择时 |
| policy_driven.yaml | 政策驱动 | 事件 | 产业政策利好受益标的 |
| northbound_follow.yaml | 北向资金跟踪 | 资金流 | 跟踪外资动向择时择股 |

## 添加自定义策略

在此目录下创建新的 `.yaml` 文件即可，格式参考已有策略。

必填字段：
- `name`: 策略标识符（英文）
- `display_name`: 显示名称
- `description`: 一句话描述
- `category`: 分类（trend/reversal/framework/event/capital_flow）
- `required_tools`: 需要的数据工具列表
- `instructions`: 详细分析步骤（喂给 LLM）
