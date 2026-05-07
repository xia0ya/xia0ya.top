# 亚马逊差评采集爬虫设计

## 目标

从亚马逊 Best Sellers 电动牙刷页面采集前50个商品的差评（三星及以下），按品牌分组存储，用于退货/投诉分析。

## 技术栈

- Python 3.10+
- Playwright（浏览器自动化）
- 住宅代理池（Residential Proxy）
- SQLite（数据存储）

## 架构

```
main.py
├── ProductListScraper    # 一级页面：采集50个商品链接和品牌
├── ReviewPageController # 二级页面：访问商品详情，触发懒加载
├── ReviewExtractor       # 提取差评数据
├── ProxyManager          # 代理池轮换
├── RateLimiter           # 请求间隔控制
└── DataStore             # SQLite存储
```

## 采集流程

1. **一级页面采集**
   - 访问 Best Sellers 页面
   - 提取前50个商品链接、品牌名称、ASIN

2. **二级页面访问**
   - 每个商品使用不同代理IP
   - 随机间隔 8-15 秒
   - 等待懒加载完成

3. **差评采集**
   - 点击 "See all reviews" 进入评论页
   - 筛选三星及以下评论
   - 滚动加载更多（懒加载）
   - 提取：评分、日期、内容、Vine认证状态

4. **数据存储**
   - 按品牌分组
   - 存入 SQLite

## 防封策略

| 策略 | 实现方式 |
|------|----------|
| IP轮换 | 每商品换一次住宅代理 |
| 请求间隔 | 随机 8-15 秒 |
| 行为模拟 | 随机鼠标移动、滚动 |
| 浏览器特征 | undetected-playwright 隐藏自动化特征 |
| 上下文复用 | 定期新建浏览器上下文 |

## 数据模型

**Table: reviews**
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 主键 |
| asin | TEXT | 商品ASIN |
| brand | TEXT | 品牌名称 |
| rating | INTEGER | 评分 1-3 |
| date | TEXT | 评论日期 |
| content | TEXT | 评论内容 |
| is_vine | BOOLEAN | 是否Vine评论 |
| collected_at | TEXT | 采集时间 |

## 输出

- `amazon_reviews.db` — SQLite数据库
- 每个品牌一个结果文件（CSV备份）

## 待确认

- [ ] 代理服务提供商选择（Oxylabs/Bright Data/其他）
- [ ] 是否需要代理健康检查
- [ ] 断点续采机制

## 风险提示

1. 亚马逊可能触发验证码，需人工介入
2. 代理成本预估：$50-100/月
3. 完整采集50商品可能需要 6-12 小时