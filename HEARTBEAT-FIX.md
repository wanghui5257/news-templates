# HEARTBEAT 响应修复方案

## 问题描述

**现象**: Cron 定时任务显示 `lastStatus: ok`，但 news-worker 未执行任务。

**影响任务**:
- 09:30 morning-digest ❌
- 12:00 noon-update ❌
- 18:30 evening-digest ✅ (手动测试覆盖)
- 22:00 night-update ❌

**根因**: Cron 触发 HEARTBEAT 消息后，news-worker 未响应（可能容器休眠或 Matrix 消息未送达）。

---

## 解决方案 A: 主动轮询（推荐）⭐⭐⭐

### 原理

news-worker 每 5 分钟主动检查一次 HEARTBEAT 触发文件，确保及时响应定时任务。

### 组件

1. **heartbeat-poller.py** - 轮询脚本
   - 位置：`/root/projects/news-templates/scripts/heartbeat-poller.py`
   - 功能：每 5 分钟检查 MinIO 中的 HEARTBEAT 文件
   - 触发：发现新任务时自动执行 `scheduled-task-trigger.py`

2. **heartbeat-poller.service** - systemd 服务配置
   - 位置：`/root/projects/news-templates/scripts/heartbeat-poller.service`
   - 功能：后台持续运行轮询脚本
   - 重启：失败后自动重启

### 部署步骤

```bash
# 1. 安装 systemd 服务
cp /root/projects/news-templates/scripts/heartbeat-poller.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable news-worker-heartbeat
systemctl start news-worker-heartbeat

# 2. 验证状态
systemctl status news-worker-heartbeat
journalctl -u news-worker-heartbeat -f
```

### 测试

```bash
# 单次测试
python3 /root/projects/news-templates/scripts/heartbeat-poller.py --once

# 查看日志
journalctl -u news-worker-heartbeat --since "5 minutes ago"
```

---

## 解决方案 B: 修改 Cron 直接触发

### 原理

修改 Cron 配置，直接 @news-worker 而不是通过 HEARTBEAT 机制。

### 步骤

1. 编辑 Cron 任务配置
2. 将触发方式从 `HEARTBEAT` 改为 `MESSAGE`
3. 添加明确的 @mention

---

## 解决方案 C: 保持容器常醒

### 原理

配置 news-worker 容器不休眠，持续监听 Matrix 消息。

### 步骤

1. 修改容器配置，禁用自动休眠
2. 或配置健康检查，定期唤醒

---

## 推荐方案

**选择方案 A** - 主动轮询

**理由**:
1. ✅ 不依赖外部触发机制
2. ✅ 容错性强（即使 Matrix 消息丢失也能执行）
3. ✅ 实现简单，易于调试
4. ✅ 可配置轮询间隔

---

## 监控

### 日志位置

```bash
# systemd 日志
journalctl -u news-worker-heartbeat -f

# MinIO 状态报告
mc ls hiclaw/hiclaw-storage/shared/heartbeat/reports/
```

### 健康检查

```bash
# 检查服务状态
systemctl is-active news-worker-heartbeat

# 检查最近任务执行
mc ls hiclaw/hiclaw-storage/shared/heartbeat/reports/ | tail -5
```

---

## 故障排除

### 问题 1: 服务未启动

```bash
systemctl start news-worker-heartbeat
systemctl enable news-worker-heartbeat
```

### 问题 2: MinIO 访问失败

```bash
# 检查 MinIO 配置
mc alias list | grep hiclaw

# 测试访问
mc ls hiclaw/hiclaw-storage/shared/
```

### 问题 3: 任务未触发

```bash
# 手动测试
python3 /root/projects/news-templates/scripts/heartbeat-poller.py --once

# 检查 scheduled-task-trigger.py
python3 /root/projects/news-templates/scheduled-task-trigger.py --type all --check-only
```

---

## 版本历史

| 日期 | 版本 | 说明 |
|------|------|------|
| 2026-03-20 | v1.0 | 初始版本 - 主动轮询方案 |
