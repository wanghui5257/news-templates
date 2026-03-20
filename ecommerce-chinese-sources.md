# 跨境电商中文数据源配置

## 当前数据源状态

### ✅ 已配置（正常）
| 数据源 | 类型 | 状态 | 说明 |
|--------|------|------|------|
| 亿邦动力 (ebrun.com) | 行业媒体 | ✅ | 跨境电商主流媒体 |
| 雨果网 (cifnews.com) | 行业媒体 | ✅ | 跨境电商服务平台 |

### ⚠️ 已配置（数据少）
| 数据源 | 类型 | 状态 | 说明 |
|--------|------|------|------|
| 卖家之家 (maijiazhijia.com) | 教程分析 | ⚠️ 数据较少 |
| 跨境知道 (kjzhidao.com) | 教程分析 | ⚠️ 数据较少 |

### ❌ 需要增加
| 数据源 | 类型 | 说明 |
|--------|------|------|
| AMZ123 | 行业媒体 | 跨境电商头部媒体 |
| 白鲸出海 | 行业媒体 | 出海开发者媒体 |
| 跨境电商赢商荟 | 行业媒体 | 跨境电商资讯 |
| 跨境眼 | 行业媒体 | 跨境电商观察 |
| 知无不言 | 社区讨论 | 跨境电商社区 |
| 创蓝论坛 | 社区讨论 | 亚马逊卖家论坛 |

---

## 新增中文数据源配置

### 1. 行业媒体（增加 4 个）

```python
'AMZ123': {
    'domain': 'amz123.com',
    'keywords': ['跨境电商', '亚马逊运营', '独立站出海'],
    'category': '行业媒体',
    'max_results': 5
},
'白鲸出海': {
    'domain': 'baijing.cn',
    'keywords': ['出海', '跨境电商', '泛娱乐出海'],
    'category': '行业媒体',
    'max_results': 5
},
'跨境电商赢商荟': {
    'domain': 'yingshanghui.com',
    'keywords': ['跨境电商', '亚马逊', 'TikTok Shop'],
    'category': '行业媒体',
    'max_results': 5
},
'跨境眼': {
    'domain': 'kjyan.com',
    'keywords': ['跨境电商', '亚马逊运营', '品牌出海'],
    'category': '行业媒体',
    'max_results': 5
},
```

### 2. 社区讨论（增加 2 个）

```python
'知无不言': {
    'domain': 'wearesellers.com',
    'keywords': ['亚马逊运营', '跨境电商', 'FBA'],
    'category': '社区讨论',
    'max_results': 5
},
'创蓝论坛': {
    'domain': 'chuanglan.com',
    'keywords': ['亚马逊', '跨境电商卖家', '运营技巧'],
    'category': '社区讨论',
    'max_results': 5
},
```

### 3. 教程分析（增加 2 个）

```python
'跨境学术派': {
    'domain': 'kuajingxueshu.com',
    'keywords': ['跨境电商运营', '亚马逊教程', '独立站运营'],
    'category': '教程分析',
    'max_results': 5
},
'卖家成长': {
    'domain': 'maijiachengzhang.com',
    'keywords': ['亚马逊运营教程', '跨境电商培训', '卖家成长'],
    'category': '教程分析',
    'max_results': 5
},
```

---

## 完整数据源列表（更新后）

### 官方发布（2 个）
- AWS Blog
- GitHub Blog

### 行业媒体（6 个）⭐ 新增 4 个
- ✅ 亿邦动力
- ✅ 雨果网
- ⭐ AMZ123 (新增)
- ⭐ 白鲸出海 (新增)
- ⭐ 跨境电商赢商荟 (新增)
- ⭐ 跨境眼 (新增)

### 社区讨论（4 个）⭐ 新增 2 个
- ✅ Hacker News
- ✅ Reddit FBA
- ⭐ 知无不言 (新增)
- ⭐ 创蓝论坛 (新增)

### 教程分析（4 个）⭐ 新增 2 个
- ✅ Jungle Scout
- ⭐ 跨境学术派 (新增)
- ⭐ 卖家成长 (新增)
- ⚠️ 卖家之家 (保留)

---

## 预期效果

**抓取数量提升**:
- 行业媒体：2 → 6 个源，预计 10 → 30 条/天
- 社区讨论：2 → 4 个源，预计 4 → 10 条/天
- 教程分析：2 → 4 个源，预计 2 → 10 条/天

**总计**: 预计 16 → 50 条中文内容/天

---

## 实施步骤

1. 更新 `fetch-chinese-news.py` 的 `CHINESE_SOURCES` 配置
2. 测试新增数据源有效性
3. 验证抓取结果
4. 推送到 GitHub

---

## 验证命令

```bash
# 测试单个数据源
python3 fetch-chinese-news.py --test-source "AMZ123"

# 完整测试
python3 fetch-chinese-news.py --output /tmp/test-ecommerce.md

# 验证中文内容比例
grep -c "来源" /tmp/test-ecommerce.md
```
