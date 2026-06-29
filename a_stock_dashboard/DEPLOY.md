# 公开部署说明

这个项目可以部署成给别人看的 Streamlit 网站。公开部署时请开启公开展示模式，避免读取本地真实持仓。

## 推荐环境变量

```bash
A_STOCK_PUBLIC_MODE=1
A_STOCK_USE_LIVE_DATA=0
```

- `A_STOCK_PUBLIC_MODE=1`：使用公开演示持仓，不读取 `data/holdings.csv`。
- `A_STOCK_USE_LIVE_DATA=0`：使用示例行情，避免免费云环境中 AKShare 接口慢或失败。
- 如果你确认服务器网络稳定，可以把 `A_STOCK_USE_LIVE_DATA` 改成 `1`。

## Streamlit Community Cloud

1. 新建一个 GitHub 仓库，只上传本项目目录。
2. 不要上传 `data/holdings.csv`，仓库里保留 `data/holdings.example.csv` 即可。
3. 在 Streamlit Cloud 选择仓库，入口文件填 `app.py`。
4. 在 App settings 的 Secrets 或环境变量里加入：

```toml
A_STOCK_PUBLIC_MODE = "1"
A_STOCK_USE_LIVE_DATA = "0"
```

5. 部署后打开公网地址，左侧菜单可以访问市场总览、外围市场、持仓诊断、今日行动等页面。

## 本地私人模式

本地自己使用时不用设置 `A_STOCK_PUBLIC_MODE`，应用会读取 `data/holdings.csv`。

```bash
streamlit run app.py
```

## 风险提示

公开网站只适合展示分析框架和示例，不应展示真实账户、客户号、持仓数量、成本、市值或任何券商截图。
