# 🎾 AI 网球教练 — 方案 A 设计文档

> **版本**: v1.0  
> **日期**: 2026-06-16  
> **方案**: LLM 驱动的轻量级 MVP  
> **目标平台**: Android 手机 App（React Native，iOS 后续扩展）  
> **目标用户**: 个人网球爱好者（NTRP 1.0–5.0），拥有 OPPO Watch  
> **输入**: 手机拍摄打球视频 + OPPO Watch 网球模式数据  
> **输出**: NTRP 等级评定 + 技术/体能分析报告 + 4 周个性化训练方案

---

## 一、设计原则

与原方案（自研 CV 模型 + GPU 集群 + 9 微服务）相比，方案 A 的核心决策：

- **用 LLM 多模态能力替代自研 CV 模型**：Claude API 分析视频关键帧，不做姿态估计/球追踪/动作分割
- **单体替代微服务**：FastAPI 单服务 + Redis 队列，降低运维复杂度
- **聚焦 OPPO Watch**：作为唯一手表数据源，利用其网球模式的专业数据
- **极简 MVP**：砍掉战术评估、视频标注回放、训练打卡、社区分享等 Phase 2+ 功能
- **快速验证**：目标 10 周内上线内测，验证核心价值假设

---

## 二、系统架构

```
┌─────────────────────────────────────────────┐
│                 客户端 (React Native)         │
│  · 视频上传                                   │
│  · OPPO Health SDK 数据读取                   │
│  · 报告查看 / 训练计划                         │
└──────────────────┬──────────────────────────┘
                   │ HTTPS
                   ▼
┌─────────────────────────────────────────────┐
│            API 服务 (FastAPI 单体)            │
│  · 用户认证 · 视频管理 · 分析任务调度          │
│  · OPPO Health 数据解析 · WebSocket 推送      │
└──────┬────────────────────┬─────────────────┘
       │                    │
       ▼                    ▼
┌──────────────┐   ┌──────────────────────────┐
│ PostgreSQL   │   │      分析 Worker           │
│ + pgvector   │   │  · ffmpeg 关键帧抽取       │
│ + Redis      │   │  · Claude API 多模态分析   │
│              │   │  · RAG 检索 + 报告生成      │
└──────────────┘   └──────────────────────────┘
```

### 与原方案的关键差异

| 组件 | 原方案 | 方案 A |
|------|--------|--------|
| 后端架构 | 9 个微服务 | 1 个单体 FastAPI |
| 视频分析 | 5 个自研 CV 模型 + GPU | ffmpeg 抽帧 + Claude API |
| 手套支持 | Apple Watch + OPPO + 华为 | OPPO Watch（唯一） |
| 向量数据库 | Milvus | pgvector |
| 任务队列 | RabbitMQ + Celery | Redis + Celery |
| 对象存储 | MinIO 自建 | 云存储 / 本地文件 |

---

## 三、核心用户流程

```
① 首次使用（3 分钟）
├─ 注册/登录（手机号/微信）
├─ 填写基本信息：年龄、性别、球龄、自评等级、目标等级
├─ 授权 OPPO Health 读取网球运动数据
└─ 选择/拍摄一段打球视频（10-30 分钟）
    ├─ 客户端自动压缩（720p, 4 Mbps）→ 预估 200-800 MB
    ├─ TUS 分片上传，进度条显示，支持断点续传
    └─ 超过 30 分钟的视频提示用户截取关键片段

② AI 分析（异步，约 2-4 分钟）
├─ 视频关键帧抽取出 30-60 张图
├─ Claude API 多模态分析：击球类型、动作质量、站位、失误
├─ OPPO 手表网球模式数据：击球统计 + 挥拍速度 + 心率/跑动
├─ pgvector RAG 检索 NTRP 手册相关内容
└─ 生成报告 → 推送通知

③ 查看报告 + 执行训练
├─ 首页：综合 NTRP 等级（基于历史上传所有视频的加权）
├─ 首页：8 种击球类型最新分项得分 + 历史趋势
├─ 首页：综合分析（跨多次评估的强弱项变化、进步速度）
├─ 教练报告：独立 Tab，按时间列出所有历史视频
│   ├─ 自动标签：发球训练/正手训练/反手训练/截击训练/综合训练
│   ├─ 📥 下载报告（Markdown）
│   └─ 🗑 删除评估
├─ 点击单个视频 → 完整四段式教练报告（评分→评价→调整→训练）
└─ 复评（建议每 4 周一次）
```

### 相比原方案砍掉的功能（后续迭代）

- 战术维度评估
- 视频标注回放（慢动作 + 关键帧对比）
- 多段视频合并上传、拍摄引导叠加层
- 训练打卡 + 成就徽章
- 社区分享
- 排行榜

---

## 四、视频分析方案（LLM 替代 CV）

### 客户端预处理

为解决大视频上传问题（1 小时 1080p = ~10 GB 不可行），客户端在上传前进行预处理：

```
原始视频 (4K/1080p, 高码率)
    │
    ▼ 客户端 ffmpeg-kit-react-native
压缩后 (720p 短边, 30fps, H.264, 4 Mbps)
    │  10 分钟 → ~300 MB
    │  30 分钟 → ~900 MB
    ▼
TUS 分片上传
    ├── 每片 20 MB
    ├── 3 路并发
    ├── 断点续传（网络中断后可从断点继续）
    └── 进度条：已上传百分比 + 预估剩余时间
```

**硬性约束**：
| 约束 | 值 | 说明 |
|------|-----|------|
| 视频时长上限 | 30 分钟 | 超出提示"建议上传 15-30 分钟的关键片段" |
| 压缩分辨率 | 720p（短边） | 保留足够细节供 Claude 分析动作 |
| 压缩码率 | 4 Mbps | 运动场景足够，文字/线条清晰 |
| 帧率 | 保持原帧率或降至 30fps | 不丢时序信息 |
| 服务端处理上限 | 30 分钟 | 超出部分截断 |

**用户体验**：
- 选择视频后先显示原始大小 + 压缩后预估大小
- 压缩期间显示进度条（"正在优化视频..."）
- 压缩完成后自动进入 TUS 上传（"正在上传..."）
- 上传失败可从断点续传，无需重新压缩

### 处理流程

```
用户上传视频 (1080p, ≥10秒)
    │
    ▼
[0] 视频内容检测 (Claude API，单次轻量调用)
    ├── 从所有关键帧中均匀采样 8-12 张
    ├── Claude 判断视频覆盖了哪些技术模块：
    │    正手 / 反手 / 发球 / 截击 / 脚步 / 接发
    ├── 统计每类击球的大致占比
    └── 输出：covered_modules[] + 粗略击球类型分布
    │
    ▼
[1] 关键帧抽取 (服务端 ffmpeg)
    ├── 每 15-20 秒抽取 1 帧
    ├── 30 分钟视频 → ~90-120 帧
    └── 压缩为 512px 宽度的 JPEG
    │
    ▼
[2] 分批发送给 Claude API (每批 20-30 帧)
    ├── 仅对步骤 [0] 检测到的 covered_modules 进行详细分析
    ├── Batch 1: 识别击球类型分布、站位习惯、球场覆盖
    ├── Batch 2: 分析动作质量、常见问题
    ├── Batch 3: 评估稳定性、失误模式
    │
    ▼
[3] 汇总分析结果
    ├── 统计击球类型分布（与 OPPO 手表数据交叉验证）
    ├── 动作质量评分（基于 NTRP 手册标准）
    ├── covered_modules 正常评分，uncovered_modules 标注"未检测到模块内容，数据不足"
    └── 综合 NTRP 等级仅基于有数据的模块推算，置信度相应降低
    ├── 识别 3-5 个关键问题帧
    └── 输出结构化数据
```

### Claude 能做 vs 不能做

| 能做到（从静态帧） | 不能做到（需要降级或放弃） |
|---|---|
| 识别正手/反手/发球/截击姿势 | 精确球速（km/h）→ 改为定性描述 |
| 判断击球点位置（靠前/合适/靠后） | 3D 轨迹重建 → 放弃 |
| 评估身体姿态（转体/屈膝/随挥） | 旋转类型精确识别 → 基于动作推测 |
| 识别明显动作问题（如"侧身绕正手"） | 实时帧级追踪 → 抽样统计推断 |
| 与 NTRP 标准对比定级 | |

### 与 OPPO 手表数据的分工

```
OPPO 网球模式（定量统计）          视频关键帧（定性分析）
─────────────────────────         ─────────────────────
✅ 总击球数                        ✅ 动作姿势质量
✅ 正手：上旋 / 削球               ✅ 击球点位置
✅ 反手：上旋 / 削球               ✅ 步法站位（开放/关闭式）
✅ 发球数（不分一发二发）           ✅ 身体姿态问题
✅ 挥拍速度                        ✅ 与 NTRP 标准的对标
✅ 心率 / 跑动 / 卡路里            ✅ 关键问题帧标注

  手表 = 精确的"是什么"            视频 = 解释"为什么 / 怎么改进"
```

### v2.0 技术升级：MediaPipe 本地计算 + JSON 数据 + 关键帧

> **版本**: v2.0 | **日期**: 2026-06-22 | **状态**: 设计中

v2.0 将视频分析从"全帧送 LLM 看图"改为"本地 CV 计算 + 结构化数据 + 3 关键帧"。核心变化：

**旧架构（v1.0）**：
```
视频 → ffmpeg 盲抽 56 帧 → 全送 Claude 看图目测 → 定性报告
```

**新架构（v2.0）**：
```
视频 → OpenCV 逐帧读取 → MediaPipe Pose (33 点 × 1800 帧)
                                    │
                          ┌─────────┼─────────┐
                          ▼         ▼         ▼
                      关节角度   躯干扭转   击球点位置
                      (atan2)   (肩-髋夹)  (手腕坐标)
                          │         │         │
                          └─────────┼─────────┘
                                    ▼
                          biomechanical extremum
                          自动选取 3 张关键帧
                                    │
                          ┌─────────┼─────────┐
                          ▼                   ▼
                    结构化 JSON (5KB)    3 张关键帧 (JPEG)
                          │                   │
                          └─────────┬─────────┘
                                    ▼
                              Claude 生成五段式报告
```

**新增模块**：

| 模块 | 文件 | 职责 |
|------|------|------|
| 帧抽取 | `server/worker/frames.py` | OpenCV `cv2.VideoCapture` 替代 ffmpeg |
| 姿态估计 | `server/worker/pose.py` | MediaPipe Pose 33 点关键点推理 |
| 运动学计算 | `server/worker/biomechanics.py` | 关节角度、扭转角、速度、关键帧选取 |
| 结构化报告 | `server/worker/structured_report.py` | 生成 5KB JSON + 选取 3 张峰值帧 |

**删除的旧模块**：
- `detect_video_modules()` — 击球类型由 MediaPipe 轨迹分析替代
- `analyze_frames_batch()` — 逐帧看图由结构化 JSON 替代
- `CONTENT_DETECTION_PROMPT` / `ANALYSIS_SYSTEM_PROMPT` — 不再需要

**Token 优化**：

| | v1.0 | v2.0 | 节省 |
|---|------|------|:--:|
| 输入 token | ~28,000 | ~3,000 | 90% |
| 图片数量 | 56 张 | 3 张 | 95% |
| 角度精度 | ±15°（目测） | ±2°（数学） | — |
| 离线计算占比 | 0% | 70% | — |

### 成本估算

- 120 帧 × ~500 token/帧 ≈ 60,000 input tokens
- 输出 ~4,000 tokens
- 单次分析 API 成本：约 $0.25-0.40

### 部分视频/片段视频处理

用户可能只上传某个技术模块的练习视频（如单独的发球练习、正手多球练习等），而非完整对抗视频。系统需要正确处理这种情况：

**Step 0 视频内容检测规则**：
- 先采样少量帧（8-12 张），由 Claude 判断视频覆盖了哪些技术模块
- 检测结果记录在 `covered_modules[]` 中

**评分策略**：

| 场景 | 示例 | 行为 |
|------|------|------|
| 全覆盖 | 完整比赛视频 | 所有 6 模块正常评分，综合 NTRP 正常 |
| 部分覆盖 | 只上传了发球练习 | 发球 → 正常评分；正手/反手/截击/脚步/接发 → 标注"未检测到模块内容，数据不足" |
| 极少内容 | 10 秒短视频，只有 2-3 次击球 | 置信度大幅降低（≤0.3），提示用户上传更长的视频 |

**综合 NTRP 推算**：
- 仅基于有数据的模块加权推算
- 缺失模块 ≥3 个时，不输出综合 NTRP，仅输出各模块独立评分
- 报告中明确标注"以下模块因视频中未检测到相关内容，无法评估：xxx"

### 无手表数据场景

手表数据为可选项。用户可能只上传视频而不连接 OPPO 手表，系统需正确处理：

**数据可用性差异**：

| 评估维度 | 有手表数据 | 无手表数据 |
|---------|----------|----------|
| 技术评分（6 模块） | ✅ 正常（视频帧分析） | ✅ 正常（仅依赖视频） |
| 击球类型统计 | ✅ 手表精确计数 | ⚠️ Claude 从视频帧粗略估算 |
| 挥拍速度 | ✅ 手表测量值 | ❌ 不可用 |
| 体能评分（心肺/移动/负荷） | ✅ 正常计算 | ❌ 标注"未上传手表数据，无法评估体能" |
| 综合 NTRP 等级 | 技术 + 体能加权 | 仅技术维度推算，置信度降低 0.1-0.2 |
| 训练计划 | 技术训练 + 体能训练 | 仅技术训练，无体能专项 |

**前端交互**：
- 上传页中 OPPO 数据选择标注为"可选"（非必填）
- 提示文案："连接手表数据可获得体能评估和更精准的击球统计"
- 报告页：体能模块无数据时，显示"未上传手表数据"占位，而非假数据

**后端处理**：
- `POST /analysis/start` 的 `health_workout_id` 参数为 optional
- 分析流水线中：无 `health_workout_id` 时跳过 OPPO 数据解析和体能计算
- `generate_final_report` prompt 中告知 Claude 是否有手表数据，无数据时要求跳过体能评分

### OPPO 手表截图替代方案

在 OPPO Health SDK 原生模块完成之前，用户可以直接上传 OPPO 手表网球模式的**截图**作为替代：

```
OPPO 手表网球模式截图
    │
    ▼
Claude 多模态提取截图中的数字
    ├── 总击球数、发球数
    ├── 正手上旋/削球、反手上旋/削球
    ├── 挥拍速度
    ├── 心率、跑动距离、卡路里
    └── → 结构化 JSON → 同 SDK 数据流
```

**实现方式**：
- 上传页增加"手表截图（可选）"按钮，选择照片
- 截图和视频一起提交到分析流水线
- 分析第 0 步（`detect_video_modules`）同时提取截图中的统计数据
- 提取成功的数据和视频帧分析结果一起进入后续评估

**优势**：零原生开发、零 SDK 集成、当天可用、覆盖所有关键数据字段

---

---

## 五、OPPO 手表数据接入

### OPPO 网球模式数据字段

通过 OPPO Health SDK（Android Content Provider）读取以下数据：

| 字段 | 说明 | 用途 |
|------|------|------|
| total_shots | 总击球数 | 评估运动量 |
| serve_count | 发球数（不区分一发二发） | 发球成功率计算 |
| forehand_topspin | 正手上旋球数 | 打法风格判断 |
| forehand_slice | 正手削球数 | 打法风格判断 |
| backhand_topspin | 反手上旋球数 | 打法风格判断 |
| backhand_slice | 反手削球数 | 打法风格判断 |
| avg_swing_speed | 平均挥拍速度 | 力量评估 |
| avg_heart_rate | 平均心率 | 心肺耐力 |
| max_heart_rate | 最大心率 | 运动强度 |
| total_distance | 总跑动距离 | 移动能力 |
| total_calories | 总卡路里 | 运动负荷 |

### 接入要点

| 项目 | 说明 |
|------|------|
| SDK | OPPO Health SDK (Android) |
| 授权方式 | App 内唤起 OPPO Health 授权页 |
| 数据获取 | Content Provider 查询，返回结构化数据 |
| 开发前提 | 需注册 OPPO 开发者账号 |

### 体能分析输出

```
体能评估:
├── 心肺耐力: 平均心率 / 最大心率 / 心率区间分布
├── 移动能力: 总跑动距离 / 每分钟跑动距离
├── 运动负荷: 总卡路里 / 训练冲量(TRIMP)
└── 体能衰减: 前半段 vs 后半段指标对比 → 疲劳程度
```

**注意**：OPPO Watch 不提供原始 IMU 数据，以下指标暂不支持：
- 急停次数 / 变向次数
- 反应时间
- 加速度峰值

---

## 六、技术评估体系

### 6 大评估模块

```
技术评分:

1. 正手
   ├── 动作质量（转体/引拍/随挥）
   ├── 击球深度控制 — 视频帧判断落点深度分布
   └── 稳定性（非受迫失误倾向）

2. 反手
   ├── 动作质量
   ├── 击球深度控制
   ├── 是否习惯性侧身绕正手
   └── 稳定性

3. 发球
   ├── 动作完整性（抛球/挥拍/随挥）
   ├── 发球成功率 — 手表总发球数 vs 视频判断入界/失误
   └── 落点控制

4. 截击/网前
   └── 动作质量 + 上网意识

5. 脚步
   ├── 移动到位率 — 击球时是否站稳、是否被球挤压
   ├── 脚步调整频率 — 小碎步/分腿垫步是否到位
   ├── 回位意识 — 击球后是否回到准备位置
   └── 数据来源：视频关键帧为主，手表跑动距离辅助

6. 接发
   └── 稳定性 + 回球质量
```

### 各指标数据来源

| 指标 | 手表数据 | 视频帧 |
|------|:---:|:---:|
| 动作质量 | — | ✅ |
| 击球深度控制 | — | ✅ |
| 发球成功率 | ✅ 总数 | ✅ 判断入界 |
| 脚步调整频率 | — | ✅ |
| 移动到位率 | ✅ 跑动距离 | ✅ |

### NTRP 等级推算

基于知识库中的技术量化基准表和 NTRP 手册标准，Claude 将用户指标与对应等级基准对比：
- 综合等级 = 各模块等级的加权中位数
- 低于综合等级 0.5+ 的模块 → ⚠️ 短板
- 高于综合等级 0.5+ 的模块 → ✅ 优势

体能等级推算基于知识库中的体能对照表，结合 OPPO 手表数据（心率/跑动/卡路里）和 NTRP 等级体能基准进行对标。

---

## 七、RAG 知识库与报告生成

### 知识库

- **源材料**：
  - `USTA NTRP全等级手册.md` — 评级标准 1.0–7.0 + 教学指南 2.0/2.5/3.0/4.0/4.5（含教学要点、错误纠正、训练方案）
  - `ntrp-knowledge-supplement.md` — 补充：3.0 错误纠正、3.5 完整教学指南、体能对照表、技术量化基准表
- **覆盖范围**：NTRP 2.0–4.5 全等级 × 6 技术模块（正手/反手/发球/接发/网前/脚步） × 3 类别（标准/错误/纠正/训练方案）
- **存储方案**：PostgreSQL + pgvector（不需要 Milvus）
- **分块策略**：按等级(2.0-4.5) × 模块 × 类别拆分，每块 300-500 tokens，块重叠率 10-15%
- **总量估算**：~250-300 个 chunk
- **Embedding 模型**：BGE-M3 或 voyage-2

### 评估流程

```
OPPO 手表数据 + 视频帧分析结果
            │
            ▼
    ┌──────────────┐
    │  pgvector 检索 │  ← 按弱项+等级+目标检索 NTRP 手册
    └──────┬───────┘
           ▼
    ┌──────────────┐
    │  Claude 推理  │  ← 输入：用户数据 + NTRP 标准 + 手表统计
    │  生成完整报告  │
    └──────┬───────┘
           ▼
    ┌──────────────────────────┐
    │       结构化输出          │
    ├──────────────────────────┤
    │ 综合 NTRP 等级            │
    │ 置信度                   │
    │ 技术评分（6 模块）         │
    │ 体能评分（4 维度）         │
    │ 强弱项 + 关键问题帧        │
    │ 4 周训练计划              │
    │ 居家辅助练习              │
    └──────────────────────────┘
```

### 训练计划生成

- 基于评估结果 + NTRP 手册教学建议
- 4 周周期，每周 2 次训练（匹配业余球友实际频率）
- 每次训练结构：热身 → 技术练习 → 体能 → 放松
- 附带居家辅助练习（无球场时可做）

---

## 八、后端设计

### 技术栈

| 组件 | 选型 |
|------|------|
| API 框架 | FastAPI (Python 3.12) |
| 任务队列 | Celery + Redis |
| 数据库 | PostgreSQL 16 + pgvector |
| 缓存/状态 | Redis 7 |
| 视频存储 | 云对象存储 / 本地文件 |
| LLM | Claude Sonnet API |
| Embedding | BGE-M3 / voyage-2 |

### 项目结构

```
├── api/
│   ├── auth.py           # 注册/登录 (手机号+微信)
│   ├── users.py          # 个人信息管理
│   ├── videos.py         # 视频上传 + 管理
│   ├── health.py         # OPPO Health 数据拉取+解析
│   ├── analysis.py       # 分析任务创建+状态查询+WebSocket
│   ├── assessments.py    # 评估报告查询
│   └── training.py       # 训练计划查看
├── worker/
│   ├── analyze.py        # 核心分析任务
│   │   ├── extract_frames()     # ffmpeg 抽帧
│   │   ├── analyze_frames()     # Claude API 调用
│   │   ├── parse_watch_data()   # OPPO 网球模式数据解析
│   │   ├── retrieve_ntrp()      # pgvector RAG 检索
│   │   └── generate_report()    # Claude 汇总 + 生成报告
│   └── notify.py         # 推送通知
├── models/               # SQLAlchemy 数据模型
└── config.py
```

### API 端点（精简版）

```
认证:
  POST   /auth/register
  POST   /auth/login
  POST   /auth/wechat

用户:
  GET    /users/me
  PATCH  /users/me

视频:
  POST   /videos/upload
  GET    /videos/{id}/status

OPPO 健康数据:
  POST   /health/authorize
  GET    /health/workouts
  GET    /health/workouts/{id}

分析:
  POST   /analysis/start
  GET    /analysis/tasks/{id}
  WS     /analysis/tasks/{id}/stream
  GET    /analysis/assessments
  GET    /analysis/assessments/{id}
  GET    /analysis/assessments/{id}/report

训练:
  GET    /training/plans
  GET    /training/plans/{id}
```

---

## 九、数据库设计

### 5 张核心表

```sql
-- 1. 用户表
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    phone VARCHAR(20) UNIQUE,
    wechat_union_id VARCHAR(64) UNIQUE,
    nickname VARCHAR(64),
    gender VARCHAR(10),
    birth_year INTEGER,
    playing_years FLOAT,
    self_rated_ntrp FLOAT,
    target_ntrp FLOAT,
    handedness VARCHAR(10),
    injury_history TEXT[],
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2. OPPO 运动记录表（含网球模式专属字段）
CREATE TABLE health_workouts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    workout_type VARCHAR(30),
    start_time TIMESTAMPTZ,
    end_time TIMESTAMPTZ,
    duration_seconds FLOAT,
    -- OPPO 网球模式数据
    total_shots INTEGER,
    serve_count INTEGER,
    forehand_topspin INTEGER,
    forehand_slice INTEGER,
    backhand_topspin INTEGER,
    backhand_slice INTEGER,
    avg_swing_speed FLOAT,
    -- 体能数据
    avg_heart_rate FLOAT,
    max_heart_rate FLOAT,
    total_distance FLOAT,
    total_calories FLOAT,
    raw_data JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 3. 视频表
CREATE TABLE videos (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    duration_seconds FLOAT,
    file_size_bytes BIGINT,
    storage_path TEXT,
    thumbnail_path TEXT,
    upload_status VARCHAR(20) DEFAULT 'uploading',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 4. 评估报告表
CREATE TABLE assessments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    video_id UUID REFERENCES videos(id),
    health_workout_id UUID REFERENCES health_workouts(id),
    overall_ntrp FLOAT,
    ntrp_confidence FLOAT,
    technique_breakdown JSONB,     -- 6 模块技术评分
    fitness_breakdown JSONB,       -- 4 维度体能评分
    strengths TEXT[],
    weaknesses TEXT[],
    key_frames JSONB,              -- 关键问题帧
    report_markdown TEXT,
    status VARCHAR(20) DEFAULT 'processing',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 5. 训练计划表
CREATE TABLE training_plans (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    assessment_id UUID REFERENCES assessments(id),
    duration_weeks INTEGER DEFAULT 4,
    sessions_per_week INTEGER DEFAULT 2,
    primary_goals JSONB,
    weekly_plans JSONB,
    home_exercises JSONB,
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

### pgvector 知识库表

```sql
CREATE TABLE ntrp_chunks (
    id SERIAL PRIMARY KEY,
    ntrp_level FLOAT,
    module VARCHAR(50),            -- forehand/backhand/serve/volley/footwork
    category VARCHAR(50),          -- standard/error/correction
    content TEXT,
    embedding vector(1024)          -- BGE-M3 1024 维
);

CREATE INDEX ON ntrp_chunks USING ivfflat (embedding vector_cosine_ops);
```

### 相比原方案去掉的表

| 去掉 | 原因 |
|------|------|
| health_auths | 合并到 health_workouts |
| training_checkins | Phase 2 再加打卡 |
| analysis_tasks | Redis 管理任务状态 |
| Milvus 向量集合 | pgvector 替代 |

---

## 十、移动端设计

### 技术栈

| 组件 | 选型 |
|------|------|
| 框架 | React Native (Expo) |
| 状态管理 | Zustand + MMKV |
| 网络 | React Query |
| 图表 | react-native-skia + d3 |
| OPPO SDK | 原生模块桥接 (Android) |

### 页面结构（8 页核心）

```
├── 登录/注册页
├── 首页
│   ├── 上次评估概要（NTRP 等级 + 雷达图）
│   └── 本周训练计划摘要
├── 上传页
│   ├── 视频选择/拍摄
│   └── OPPO 手表数据选择（自动关联最近网球记录）
├── 分析中页面（WebSocket 实时进度）
├── 评估报告页（核心页面，分段展示）
│   ├── NTRP 等级 + 雷达图
│   ├── 技术分项详情（6 模块）
│   ├── 体能详情
│   └── 关键问题帧（图片 + 标注）
├── 训练计划页（4 周 × 每次训练内容）
├── 历史评估列表页
└── 个人中心/设置
```

### 砍掉的页面（后续迭代）

- 拍摄引导叠加层
- 视频标注回放播放器
- 训练打卡 + 日历
- 等级变化趋势图
- 社区分享

---

## 十一、开发路线图（10 周）

```
Week 1-2: 项目搭建
├── FastAPI 脚手架 + PostgreSQL + Redis
├── React Native 初始化 (Expo)
├── 用户认证（手机号 + 微信登录）
└── CI/CD 基础

Week 3-4: 数据层
├── OPPO Health SDK 集成（Android 原生模块）
├── 网球模式数据解析（击球统计 + 体能）
├── 视频上传（TUS 断点续传）
└── 用户个人信息管理

Week 5-6: 分析引擎核心
├── ffmpeg 服务端抽帧
├── Claude API 多模态分析 Prompt 调优
├── NTRP 手册 → pgvector RAG 入库 + 检索
├── 评估报告生成（结构化输出）
└── 训练计划生成

Week 7: 移动端核心页面
├── 首页 + 上传页 + OPPO 数据选择
├── 分析进度页（WebSocket）
├── 评估报告页（分段展示 + 雷达图）
└── 训练计划页

Week 8: 联调 + 通知
├── 端到端集成联调
├── 推送通知（分析完成）
└── 错误处理 + 边界情况

Week 9: 测试 + 优化
├── 端到端测试（真实打球视频）
├── Prompt 调优（提升准确度）
├── 分析时间优化（目标 < 3 分钟）
└── Bug 修复

Week 10: 发布
├── Android APK 打包（OPPO 应用商店测试通道）
├── 服务器部署
└── 内测用户招募
```

### 团队配置

- 2-3 人：1 后端 + 1 移动端（+ 可选 1 全栈辅助）

### 月度运营成本估算

| 项目 | 月成本 |
|------|--------|
| 云服务器（2C4G） | ~¥100-200 |
| PostgreSQL + Redis 托管 | ~¥200-400 |
| Claude API（100 次分析） | ~¥150-300 |
| 对象存储 | ~¥50-100 |
| **合计** | **~¥500-1000** |

---

## 十二、后续迭代方向

### Phase 2（确认产品价值后）

- 战术维度评估
- 视频标注回放
- 训练打卡 + 进度追踪
- 历史趋势对比 + 等级变化图
- iOS 端支持 + Apple Watch 接入

### Phase 3（规模化后）

- 自研 CV 模型（逐步替代 LLM 部分分析，降低成本）
- 实时训练辅助（AR）
- 多人社区 + 排行榜
- 教练端（教练查看学员报告）

---

> **下一步**：确认此设计文档后，进入写作实施计划阶段。
