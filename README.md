# xia0ya.top - Amazon 评论与退货分析系统

基于 FastAPI 的 Amazon 评论爬虫与退货分析平台，支持评论分析、退货分析、数据可视化等功能。

## 功能模块

### 1. 评论分析 (Reviews)
- 亚马逊商品评论数据爬取
- 评论列表展示与筛选
- 词云生成与关键词分析
- 评分统计与趋势分析

### 2. 退货分析 (Return Analysis)
- 退货数据上传与管理
- 多版本历史数据对比
- AI 智能洞察分析（基于 Kimi API）
- 可视化图表：
  - 按日期统计趋势
  - 退货类型分布（仅退款/退货退款）
  - 退货原因分析
  - SKU 退货金额排名
  - 月度退货率统计

## 技术栈

| 层级 | 技术 |
|------|------|
| 后端框架 | FastAPI + Jinja2 |
| 数据库 | SQLite |
| 前端 | Tailwind CSS + Chart.js |
| 爬虫 | Playwright |
| AI 集成 | Kimi API (Moonshot) |
| Web 服务器 | Nginx |

## 目录结构

```
xia0ya.top/
├── web/                          # Web 应用主目录
│   ├── main.py                   # FastAPI 应用入口
│   ├── routes/                   # 路由模块
│   │   ├── auth.py              # 认证相关
│   │   ├── reviews.py           # 评论列表
│   │   ├── analytics.py         # 数据分析
│   │   ├── return_analysis.py   # 退货分析
│   │   ├── dashboard.py         # 首页
│   │   ├── users.py             # 用户管理
│   │   └── help.py              # 帮助页面
│   ├── services/                # 业务逻辑层
│   │   ├── scraper_service.py   # 爬虫服务
│   │   ├── analytics_service.py # 分析服务
│   │   └── wordcloud_service.py # 词云服务
│   ├── models/                  # 数据模型
│   ├── templates/               # HTML 模板
│   │   ├── base.html           # 基础模板
│   │   ├── return_analysis.html # 退货分析页（独立模板）
│   │   └── ...
│   └── static/                  # 静态资源
├── database/                     # 数据库目录
├── return_data/                  # 退货分析数据存储
├── scraper/                      # 爬虫核心模块
├── core/                         # 核心工具
├── proxy/                        # 代理管理
├── stealth/                      # 反检测脚本
├── gui/                          # 桌面 GUI（可选）
├── return_analyzer.py            # 退货分析核心脚本
├── return_analysis.py            # 退货分析 API 路由
└── main.py                       # CLI 入口
```

## 部署指南

### 服务器环境要求

- Python 3.8+
- Nginx
- Git

### 安装步骤

#### 1. 克隆代码

```bash
git clone https://github.com/xia0ya/xia0ya.top.git
cd xia0ya.top
```

#### 2. 创建虚拟环境

```bash
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows
```

#### 3. 安装依赖

```bash
pip install -r requirements.txt
playwright install chromium
```

#### 4. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 填入必要配置
```

#### 5. 配置 Nginx

```nginx
server {
    listen 80;
    server_name xia0ya.top;

    client_max_body_size 50M;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

#### 6. 启动服务

```bash
# 开发环境
python run_web.py

# 生产环境（使用 systemd）
sudo systemctl start xia0ya
```

### 数据目录

- `database/products.db` - 评论数据
- `return_data/` - 退货分析数据（按版本组织）
- `web/static/uploads/` - 上传文件

## API 接口

### 退货分析 API

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/return/` | 退货分析主页 |
| GET | `/return/api/versions` | 获取版本列表 |
| POST | `/return/api/upload` | 上传数据文件 |
| POST | `/return/api/analyze` | 触发分析 |
| GET | `/return/api/data/{version}` | 获取分析结果 |
| GET | `/return/api/download/{version}/excel` | 下载 Excel |
| DELETE | `/return/api/version/{version}` | 删除版本 |
| POST | `/return/api/insights` | 获取 AI 洞察 |

### 评论相关 API

| 方法 | 路径 | 说明 |
|------|------|
| GET | `/reviews` | 评论列表 |
| GET | `/analytics` | 数据分析主页 |
| GET | `/dashboard` | 首页仪表盘 |

## 退货分析使用说明

### 上传数据格式

支持 CSV 和 Excel 格式，必要字段：

| 字段名 | 说明 |
|--------|------|
| Order ID | 订单号 |
| Order Amount | 订单金额 |
| Seller SKU | SKU |
| Return Type | 退货类型（Refund only / Return and refund） |
| Return Reason | 退货原因 |
| Return unit price | 退款金额 |
| Return Quantity | 退货数量 |
| Time Requested | 申请时间 |
| Refund Time | 退款时间 |
| Buyer Note | 买家备注 |

### AI 洞察功能

系统集成 Kimi AI（Moonshot）进行智能分析，需要配置 API Key：

```python
# web/routes/return_analysis.py
KIMI_API_KEY = "your-api-key"
```

洞察分析包括：
- 健康度诊断
- 核心问题识别
- 趋势预警
- 行动建议

## 开发指南

### 添加新页面

1. 在 `web/templates/` 创建 HTML 模板
2. 在 `web/routes/` 添加路由
3. 注册路由到 `web/main.py`

### 修改导航栏

编辑 `web/templates/base.html` 的 `<nav>` 部分

## 安全注意事项

- 切勿提交 `.env` 或 `credentials.json` 到 Git
- 生产环境务必配置 HTTPS
- 定期备份数据库

## License

MIT License
