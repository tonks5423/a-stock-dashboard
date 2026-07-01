# 公开部署说明

这个项目可以部署成给别人看的 Streamlit 网站。公开部署时请开启公开展示模式，网站会读取 `data/public_holdings.csv` 中你选择公开展示的持仓。

## 推荐环境变量

```bash
A_STOCK_PUBLIC_MODE=1
A_STOCK_USE_LIVE_DATA=0
A_STOCK_USE_CACHED_DATA=1
A_STOCK_REFRESH_ON_OPEN=1
```

- `A_STOCK_PUBLIC_MODE=1`：使用 `data/public_holdings.csv`，不读取本地私人文件 `data/holdings.csv`。
- `A_STOCK_USE_LIVE_DATA=0`：页面正常读取缓存，不在普通数据读取路径里直接请求 AKShare。
- `A_STOCK_USE_CACHED_DATA=1`：优先读取 `data/live_cache/`。
- `A_STOCK_REFRESH_ON_OPEN=1`：打开网页时检查北京时间 11:30/14:30 刷新点，若本时段未成功刷新，会现场运行刷新脚本并写入缓存。
- 如果你确认服务器网络稳定，可以把 `A_STOCK_USE_LIVE_DATA` 改成 `1`。

## Streamlit Community Cloud

1. 新建一个 GitHub 仓库，只上传本项目目录。
2. 不要上传 `data/holdings.csv`，仓库里保留 `data/public_holdings.csv` 作为公开展示持仓。
3. 在 Streamlit Cloud 选择仓库，入口文件填 `app.py`。
4. 在 App settings 的 Secrets 或环境变量里加入：

```toml
A_STOCK_PUBLIC_MODE = "1"
A_STOCK_USE_LIVE_DATA = "0"
A_STOCK_USE_CACHED_DATA = "1"
A_STOCK_REFRESH_ON_OPEN = "1"
```

5. 打开公网地址时，应用会检查 11:30/14:30 是否已经到点且本时段是否已刷新。若需要刷新，会运行 `scripts/update_live_cache.py` 并更新 `data/live_cache/`。GitHub Actions 仍作为补充兜底。左侧菜单可以访问市场总览、外围市场、持仓诊断、今日行动等页面。

## 本地私人模式

本地自己使用时不用设置 `A_STOCK_PUBLIC_MODE`，应用会读取 `data/holdings.csv`。

```bash
streamlit run app.py
```

## 风险提示

公开网站可以展示你选择公开的持仓，但不要放真实账户、客户号、券商截图或任何登录信息。
