# A 股交易数据面板

用于辅助 A 股交易决策的 Streamlit MVP。第一版只做数据展示、评分、筛选和预警，不自动交易，不连接券商账户。

## 功能

- 市场总览：市场温度、市场状态、指数表现、成交额、涨跌家数、涨跌停家数
- 外围参考：纳指、标普、费半、A50、港股、美元离岸人民币、美债、黄金、原油等情绪映射
- 板块强弱：行业/概念板块排名、强度分、状态
- 个股筛选：按趋势、量能、板块、风险等规则筛选候选股
- 持仓诊断：读取 `data/holdings.csv`，计算盈亏、状态、辅助建议和风险提醒
- 风险预警：检测均线、放量下跌、板块转弱、接近止损等风险
- 今日行动：结合市场、外围、板块、候选股、持仓和风险，生成开盘三剧本、仓位建议、持仓处理方案和买卖纪律

## 安装

```bash
cd /Users/lanbao/Documents/股票/a_stock_dashboard
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 运行

```bash
streamlit run app.py
```

默认优先读取 `data/live_cache/` 中的定时真实行情缓存；如果缓存不存在，则使用快速示例数据，避免 AKShare 实时接口慢或不可用时页面一直加载。

如需请求 AKShare 实时/准实时接口：

```bash
A_STOCK_USE_LIVE_DATA=1 streamlit run app.py
```

如果 AKShare 或网络/接口不可用，应用会自动使用示例数据兜底，并在页面顶部显示提示。

## 更新真实数据

网页打开时会检查北京时间 11:30、14:30 两个刷新点。若当前时段还没有成功刷新，页面会直接运行 `scripts/update_live_cache.py` 抓取真实行情并写入 `data/live_cache/`，随后重新读取缓存。

刷新状态会写入 `data/live_cache/refresh_status.json` 并显示在首页，用来区分“没到刷新时间、已经刷新、刚尝试失败、数据源不可用”。

GitHub Actions 仍保留北京时间交易日 11:30、11:40、11:50、14:30、14:40、14:50 的补充抓取，但它只作为兜底，不作为唯一刷新机制。

## 公开给别人看

公开部署时请开启公开展示模式，网站会读取 `data/public_holdings.csv`：

```bash
A_STOCK_PUBLIC_MODE=1 streamlit run app.py
```

详细部署步骤见 `DEPLOY.md`。公开部署不要上传 `data/holdings.csv`，仓库里保留 `data/public_holdings.csv` 即可。

## 维护持仓

编辑 `data/holdings.csv`：

```csv
stock_code,stock_name,buy_price,shares,buy_date,stop_loss_price,target_price,current_price,current_market_value,note
000001,平安银行,10.50,1000,2026-06-01,9.80,12.00,10.80,10800,示例
```

## 调整交易画像

编辑 `data/trading_profile.json` 可以调整交易风格、总仓位上限、单票上限和复盘时间。页面刷新后会按新配置重新生成“今日行动”。

## 评分说明

个股最终评分：

```text
总分 = 市场分 * 25% + 板块分 * 30% + 个股趋势分 * 25% + 量能分 * 10% + 基本面分 * 10% - 风险扣分
```

评分只用于辅助观察，不构成投资建议。
