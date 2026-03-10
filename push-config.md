# 推送配置文档

**版本**: v1.0.0
**创建时间**: 2026-03-09
**最后更新**: 2026-03-09

---

## 📅 推送时间表（北京时间）

| 时间 | 说明 | Cron 表达式 |
|------|------|------------|
| **09:30** | 早间新闻 | `30 9 * * *` |
| **12:00** | 午间更新 | `0 12 * * *` |
| **18:30** | 晚间新闻 | `30 18 * * *` |
| **22:00** | 夜间更新 | `0 22 * * *` |

**时区**: Asia/Shanghai

---

## 📱 推送渠道

| 渠道 | 状态 | 配置 |
|------|------|------|
| **Telegram** | ✅ 已配置 | Bot Token + Chat ID |
| **钉钉** | ✅ 已配置 | Webhook + 签名密钥 |
| **飞书** | ✅ 已配置 | Webhook（无签名） |

---

## 🔧 推送脚本

**路径**: `/root/hiclaw-fs/agents/alice/scripts/send-notifications.py`

**功能**:
- 自动发送 Telegram 通知
- 自动发送钉钉通知（带签名）
- 自动发送飞书通知

**执行方式**:
```bash
python3 /root/hiclaw-fs/agents/alice/scripts/send-notifications.py
```

---

## 📋 推送消息格式

```
📰 每日新闻已更新！

🛒 跨境电商新闻：
http://ecommerce.shujuyunxiang.com

🌍 国际新闻：
https://news.shujuyunxiang.com

更新日期：YYYY-MM-DD HH:MM
```

---

## 🔄 完整工作流程

```
定时任务触发 (09:30/12:00/18:30/22:00)
      ↓
ai-collection 抓取新闻 → 标准分类 → MinIO
      ↓
Alice 读取数据 → 验证分类 → 加载 Git 模板
      ↓
生成 HTML → 部署到 ECS → 验证
      ↓
推送通知 (Telegram + 钉钉 + 飞书)
      ↓
Check in @manager
```

---

## 🛡️ 质量检查机制

**Alice 验证清单**:
- [ ] 数据文件存在且非空
- [ ] 分类是标准 4 类（news: 国际/中国/AI/科技）
- [ ] 分类是标准 4 类（ecommerce: 官方/社区/媒体/教程）
- [ ] 新闻条数>0
- [ ] 使用 Git 模板生成 HTML
- [ ] 页脚正确（Walt Wang 的 ai 机器人）
- [ ] 部署验证通过

**问题上报**:
- 分类不对 → 🛑 停止 → @ai-collection @manager
- 数据为空 → 🛑 停止 → @ai-collection @manager
- 部署失败 → 🛑 停止 → @manager

---

## 📊 版本历史

| 版本 | 日期 | 变更内容 |
|------|------|----------|
| v1.0.0 | 2026-03-09 | 初始版本（推送时间 + 渠道配置） |

---

**配置固化到 Git，修改需 commit！**

---

## 🚀 手动触发推送

### 触发方式

**方法 1: Manager 指令**
```
@manager: 手动推送新闻更新
```

**方法 2: 执行脚本**
```bash
bash /root/hiclaw-fs/agents/alice/scripts/manual-push.sh
```

### 手动触发流程

```
Manager 指令
      ↓
ai-collection 抓取数据 → MinIO
      ↓
Alice 验证 → HTML → 部署 → 推送
      ↓
Check in @manager
```

### 使用场景

- ✅ 临时新闻更新
- ✅ 测试推送功能
- ✅ 错过定时推送后的补发
- ✅ 紧急新闻发布

---

**版本**: v1.0.2 (添加手动触发功能)
