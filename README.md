# HTML 模板仓库 v1.0.8

## 模板说明

本仓库存储标准 HTML 页面模板，包含：

### 1. news-template.html
- **用途**: 晚间新闻摘要页面
- **标准 4 类主题**: 国际新闻/中国新闻/AI 新闻/科技趋势
- **页脚**: `HTML 页面由 Walt Wang 的 ai 机器人生成 | 每日早 8 点自动更新`

### 2. ecommerce-template.html
- **用途**: 跨境电商新闻页面
- **标准 4 类信源**: 官方发布/社区讨论/行业媒体/教程分析
- **页脚**: `HTML 页面由 Walt Wang 的 ai 机器人生成 | 每日早 8 点自动更新`

## 模板变量

### News 模板变量
- `{{DATE}}`: 日期 (格式：2026 年 3 月 9 日)
- `{{TIME}}`: 时间 (格式：14:06)
- `{{NEWS_WORLD}}`: 国际新闻 HTML 内容
- `{{NEWS_CHINA}}`: 中国新闻 HTML 内容
- `{{NEWS_AI}}`: AI 新闻 HTML 内容
- `{{NEWS_TECH}}`: 科技趋势 HTML 内容

### Ecommerce 模板变量
- `{{DATE}}`: 日期
- `{{TIME}}`: 时间
- `{{NEWS_OFFICIAL}}`: 官方发布 HTML 内容
- `{{NEWS_COMMUNITY}}`: 社区讨论 HTML 内容
- `{{NEWS_MEDIA}}`: 行业媒体 HTML 内容
- `{{NEWS_KNOWLEDGE}}`: 教程分析 HTML 内容

## 使用流程

1. **ai-collection** 抓取新闻数据 → 标准分类 → MinIO 存储
2. **Alice** 读取数据 → 验证分类 → 使用模板生成 HTML → 部署
3. **验证**: 页脚必须显示 `HTML 页面由 Walt Wang 的 ai 机器人生成`

## 版本历史

| 版本 | 日期 | 说明 |
|------|------|------|
| v1.0.8 | 2026-03-09 | 初始版本 - 标准 4 类分类模板 |

## 注意事项

- ❌ 不要修改页脚内容
- ❌ 不要修改标准分类体系
- ✅ 只更新动态数据部分（通过模板变量）
- ✅ 每次修改后 commit 并标注版本号
