# 🎾 网球教练 Agent — 完整技术设计文档

> **版本**: v1.0  
> **日期**: 2026-06-15  
> **目标平台**: iOS / Android 手机 App  
> **目标用户**: 个人网球爱好者（NTRP 1.0–5.0）  
> **输入**: 打球视频（手机拍摄）+ 运动手表数据（Apple Watch / OPPO Watch / 华为 Watch）+ 用户基本信息  
> **输出**: NTRP 等级评定 + 技术/体能/战术三维度分析报告 + 个性化训练方案

---

## 目录

1. [产品概览](#一产品概览)
2. [系统架构总览](#二系统架构总览)
3. [移动端设计](#三移动端设计)
4. [视频理解引擎](#四视频理解引擎)
5. [手表数据引擎](#五手表数据引擎)
6. [多模态对齐引擎](#六多模态对齐引擎)
7. [三维度评估引擎](#七三维度评估引擎)
8. [RAG 知识库与建议生成](#八rag-知识库与建议生成)
9. [后端服务设计](#九后端服务设计)
10. [数据库设计](#十数据库设计)
11. [API 设计](#十一api-设计)
12. [模型训练与数据标注](#十二模型训练与数据标注)
13. [开发路线图](#十三开发路线图)
14. [附录：NTRP 等级评估矩阵](#十四附录ntrp-等级评估矩阵)

---

## 一、产品概览

### 1.1 核心用户流程

```
┌─────────────────────────────────────────────────────────────────────┐
│                        用户完整体验流程                               │
│                                                                     │
│  ① 首次使用                                                         │
│  ├─ 注册/登录（手机号/微信/Apple ID）                                 │
│  ├─ 填写个人信息：年龄、性别、球龄、自评等级、目标等级、伤病史           │
│  ├─ 授权 Apple Health / OPPO Health / 华为健康 读取运动数据            │
│  └─ 上传一段最近的打球视频（≥15分钟，建议底线后方拍摄）                  │
│                                                                     │
│  ② AI 分析（云端异步处理，约 3-8 分钟）                               │
│  ├─ 视频上传 → 队列 → AI引擎处理                                     │
│  ├─ 手表数据自动拉取 → 时间窗口匹配                                    │
│  └─ 生成分析报告 + 推送通知                                          │
│                                                                     │
│  ③ 查看报告                                                         │
│  ├─ NTRP 综合等级 + 各分项评分                                        │
│  ├─ 三维度雷达图（技术/体能/战术）                                     │
│  ├─ AI 逐项诊断（正手/反手/发球/网前/脚步…）                           │
│  ├─ 视频标注回放（关键帧标注 + 慢动作对比）                             │
│  └─ 与上次评估的对比趋势                                              │
│                                                                     │
│  ④ 训练执行                                                         │
│  ├─ 每周个性化训练计划（技术+体能+战术）                                │
│  ├─ 训练打卡 + 手表数据自动记录                                       │
│  ├─ 阶段性复评（建议每 4 周一次）                                      │
│  └─ 等级进阶提示 + 成就徽章                                          │
└─────────────────────────────────────────────────────────────────────┘
```

### 1.2 产品功能矩阵

| 功能模块 | 功能点 | Phase 1 MVP | Phase 2 | Phase 3 |
|----------|--------|:-----------:|:-------:|:-------:|
| **视频上传** | 本地视频选择 / 直接拍摄 | ✅ | | |
| | 多段视频合并上传 | ✅ | | |
| | 拍摄引导（角度/光线提示） | ✅ | | |
| **手表连接** | Apple Health 授权读取 | ✅ | | |
| | OPPO Health 授权读取 | ✅ | | |
| | 华为健康授权读取 | ✅ | | |
| | FIT/TCX 文件手动导入 | ✅ | | |
| **AI 分析** | 视频自动分析（击球分类+动作评估） | ✅ | | |
| | NTRP 自动定级 | ✅ | | |
| | 技术维度深度分析 | ✅ | | |
| | 体能维度分析 | ✅ | | |
| | 战术维度分析 | | ✅ | |
| | 与职业选手动作对比 | | | ✅ |
| **训练计划** | 基于弱项的个性化训练方案 | ✅ | | |
| | 训练日历 + 打卡 | | ✅ | |
| | 训练过程实时纠错（AR 叠加） | | | ✅ |
| **报告** | 单次分析报告 | ✅ | | |
| | 历史趋势对比 | | ✅ | |
| | 社区分享（匿名） | | ✅ | |

---

## 二、系统架构总览

### 2.1 整体架构图

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                              客户端层 (Mobile Client)                         │
│                                                                              │
│  ┌─────────────────────┐  ┌──────────────────────┐  ┌───────────────────┐   │
│  │  React Native App   │  │  Apple HealthKit SDK  │  │  视频预处理引擎     │   │
│  │  (iOS + Android)    │  │  OPPO Health SDK      │  │  (本地压缩+分段)   │   │
│  │                     │  │  华为 Health Kit SDK   │  │                   │   │
│  └─────────┬───────────┘  └──────────┬───────────┘  └────────┬──────────┘   │
└────────────┼──────────────────────────┼──────────────────────┼──────────────┘
             │                          │                      │
             │  HTTPS (REST + WebSocket)│                      │
             │  ／ 视频分片上传 (TUS)   │                      │
             ▼                          ▼                      ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                              网关层 (API Gateway)                             │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │               Kong / Traefik API Gateway                              │   │
│  │    认证鉴权 │ 限流 │ 路由 │ 请求/响应转换 │ WebSocket 升级             │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────────────────┘
             │
             ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                              服务层 (Microservices)                           │
│                                                                              │
│  ┌─────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────────┐   │
│  │ 用户服务     │ │ 视频处理服务  │ │ 分析编排服务  │ │ 训练计划服务      │   │
│  │ - 注册/登录  │ │ - 上传管理   │ │ - 任务调度    │ │ - 计划生成       │   │
│  │ - 个人信息   │ │ - 视频预处理  │ │ - 流水线编排  │ │ - 进度追踪       │   │
│  │ - 等级管理   │ │ - 存储管理   │ │ - 结果聚合    │ │ - 打卡记录       │   │
│  └──────┬──────┘ └──────┬───────┘ └──────┬───────┘ └────────┬─────────┘   │
│         │               │               │                   │              │
└─────────┼───────────────┼───────────────┼───────────────────┼──────────────┘
          │               │               │                   │
          ▼               ▼               ▼                   ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                               AI 引擎层 (AI Engine)                           │
│                                                                              │
│  ┌──────────────────┐  ┌──────────────────┐  ┌─────────────────────────┐   │
│  │  视频理解引擎     │  │  手表数据引擎     │  │  多模态对齐引擎          │   │
│  │                  │  │                  │  │                         │   │
│  │ ┌──────────────┐ │  │ ┌──────────────┐ │  │ ┌─────────────────────┐ │   │
│  │ │ 姿态估计     │ │  │ │ HR时序分析   │ │  │ │ 时间戳同步           │ │   │
│  │ │ 球追踪       │ │  │ │ 运动负荷计算 │ │  │ │ 事件对齐             │ │   │
│  │ │ 动作分割     │ │  │ │ 移动热力图   │ │  │ │ 特征融合             │ │   │
│  │ │ 击球分类     │ │  │ │ 体能指标提取 │ │  │ └─────────────────────┘ │   │
│  │ │ 球场标定     │ │  │ └──────────────┘ │  │                         │   │
│  │ └──────────────┘ │  └──────────────────┘  └─────────────────────────┘   │
│  └────────┬─────────┘                                                       │
│           │                                                                  │
│           ▼                                                                  │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                     三维度评估引擎 (Assessment Engine)                 │   │
│  │                                                                       │   │
│  │  ┌───────────────┐  ┌───────────────┐  ┌───────────────────────────┐ │   │
│  │  │ 🔧 技术评估    │  │ 💪 体能评估    │  │ 🎯 战术评估                │ │   │
│  │  │               │  │               │  │                           │ │   │
│  │  │ · 动作质量    │  │ · 心肺耐力    │  │ · 打法风格识别            │ │   │
│  │  │ · 击球稳定性  │  │ · 爆发力      │  │ · 得分模式分析            │ │   │
│  │  │ · 深度/线路   │  │ · 移动效率    │  │ · 决策质量评估            │ │   │
│  │  │ · NTRP 对标   │  │ · 恢复能力    │  │ · 关键分表现              │ │   │
│  │  └───────┬───────┘  └───────┬───────┘  └─────────────┬─────────────┘ │   │
│  └──────────┼──────────────────┼────────────────────────┼──────────────┘   │
│             └──────────────────┼────────────────────────┘                   │
│                                ▼                                            │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                 RAG 建议生成引擎 (Prescription Engine)                 │   │
│  │                                                                       │   │
│  │  向量数据库 (Milvus) ⟷ NTRP教学指南 ⟷ Claude Sonnet 4.6 推理          │   │
│  │       ↓                                                               │   │
│  │  分析报告 + 训练计划 + 纠错指导                                        │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
          │
          ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                           基础设施层 (Infrastructure)                         │
│                                                                              │
│  ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐    │
│  │  PostgreSQL │ │  Redis    │ │  MinIO    │ │  Milvus   │ │  RabbitMQ │    │
│  │  用户数据   │ │  缓存+队列│ │  视频/图片│ │  向量存储  │ │  任务队列  │    │
│  └───────────┘ └───────────┘ └───────────┘ └───────────┘ └───────────┘    │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │  GPU 集群 (NVIDIA A10G / L40S × 4)                                   │   │
│  │  · 姿态估计: ONNX Runtime + TensorRT                                 │   │
│  │  · 球追踪: PyTorch + CUDA                                            │   │
│  │  · 动作识别: VideoMAE 推理                                            │   │
│  │  · LLM 推理: vLLM (Claude API 作为主推理，开源模型做预筛选)            │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 关键技术选型

| 层级 | 组件 | 技术选型 | 选型理由 |
|------|------|----------|----------|
| **移动端** | 框架 | React Native 0.76+ (Expo) | 跨平台、热更新、社区生态好 |
| | 视频采集 | react-native-vision-camera | 高性能、支持帧提取 |
| | 视频预处理 | ffmpeg-kit-react-native | 本地压缩、分段、关键帧抽取 |
| | 健康数据 | react-native-health (iOS) + Health Connect API (Android) | 统一健康数据读取接口 |
| | 图表渲染 | react-native-skia + d3 | 高性能雷达图、趋势图 |
| | 视频播放 | expo-av + 自定义标注叠加层 | 支持慢放、帧标注、对比播放 |
| **网关** | API Gateway | Kong / Traefik | 统一认证、限流、路由 |
| **后端** | API 框架 | FastAPI (Python 3.12) | 异步、类型安全、生态好 |
| | 任务队列 | Celery + RabbitMQ | GPU 任务调度、重试、优先级 |
| | 实时通知 | WebSocket (FastAPI) | 分析进度推送 |
| **AI 引擎** | 姿态估计 | MediaPipe Pose (BlazePose GHUM 3D) | 轻量、33 个 3D 关键点、移动端可跑 |
| | 球追踪 | TrackNet V3 + DeepBall (fine-tune) | 网球专用、3D 轨迹重建 |
| | 动作识别 | VideoMAE V2 (fine-tune) | 自监督预训练、少样本微调 |
| | 球场标定 | 传统 CV (Canny + HoughLinesP + 单应性) | 无需深度学习、速度快 |
| | LLM 推理 | Claude Sonnet 4.6 (主) + Qwen3 (辅助分类) | 多模态推理能力强 |
| | RAG Embedding | BGE-M3 / voyage-2 | 多语言、8192 token 上下文 |
| **存储** | 对象存储 | MinIO (自建) / S3 | 视频文件、分析产物 |
| | 关系数据库 | PostgreSQL 16 + pgvector | 用户数据、评估记录 |
| | 向量数据库 | Milvus 2.4 | NTRP 知识库检索 |
| | 缓存 | Redis 7 | Session、排行榜、任务状态 |
| **部署** | 容器编排 | Kubernetes (K3s) | GPU 节点管理、自动扩缩容 |
| | GPU 调度 | NVIDIA GPU Operator | GPU 资源分配 |
| | CI/CD | GitHub Actions + ArgoCD | 自动构建、灰度发布 |
| | 监控 | Prometheus + Grafana + Sentry | 性能监控、错误追踪 |

---

## 三、移动端设计

### 3.1 技术架构

```
┌─────────────────────────────────────────────┐
│              React Native Shell              │
│                                             │
│  ┌──────────┐ ┌──────────┐ ┌─────────────┐ │
│  │ Navigation│ │  State   │ │  Networking │ │
│  │ (Expo     │ │ (Zustand │ │  (React     │ │
│  │  Router)  │ │  + MMKV) │ │   Query)    │ │
│  └──────────┘ └──────────┘ └─────────────┘ │
│                                             │
│  ┌──────────────────────────────────────┐   │
│  │         业务模块 (Business Modules)    │   │
│  │                                      │   │
│  │  Auth    Video    Assessment  Training│   │
│  │  Module  Module   Module      Module  │   │
│  └──────────────────────────────────────┘   │
│                                             │
│  ┌──────────────────────────────────────┐   │
│  │        原生模块 (Native Modules)       │   │
│  │                                      │   │
│  │  ┌──────────┐ ┌────────────────────┐ │   │
│  │  │ 视频预处理 │ │ 健康数据桥接       │ │   │
│  │  │ FFmpeg   │ │ HealthKit/OPPO/   │ │   │
│  │  │ 帧提取   │ │ 华为 Health Kit    │ │   │
│  │  └──────────┘ └────────────────────┘ │   │
│  └──────────────────────────────────────┘   │
└─────────────────────────────────────────────┘
```

### 3.2 核心页面结构

```
App 页面树
├── Onboarding (首次引导)
│   ├── WelcomeScreen           — 欢迎页 + 功能简介
│   ├── ProfileSetupScreen      — 个人信息填写
│   ├── HealthAuthScreen        — 健康数据授权引导（分品牌）
│   └── FirstVideoUploadScreen  — 首次视频上传引导
│
├── Auth
│   ├── LoginScreen             — 登录页
│   └── RegisterScreen          — 注册页
│
├── Main (Tab Navigator)
│   ├── HomeTab
│   │   ├── HomeScreen          — 首页：上次评估概要 + 今日训练
│   │   └── QuickUploadScreen   — 快捷上传
│   │
│   ├── AssessmentTab
│   │   ├── AssessmentListScreen    — 历史评估列表
│   │   ├── AssessmentDetailScreen  — 评估报告详情（核心页面）
│   │   │   ├── OverviewSection     — NTRP 等级 + 雷达图
│   │   │   ├── TechniqueSection    — 技术分项详情
│   │   │   ├── FitnessSection      — 体能详情
│   │   │   ├── TacticsSection      — 战术详情
│   │   │   └── TrainingPlanSection — 训练计划
│   │   └── VideoReviewScreen       — 视频标注回放（关键帧+对比）
│   │
│   ├── TrainingTab
│   │   ├── WeeklyPlanScreen    — 本周训练计划
│   │   ├── TrainingDetailScreen— 单次训练详情
│   │   └── ProgressScreen      — 训练进度 + 打卡记录
│   │
│   └── ProfileTab
│       ├── ProfileScreen       — 个人中心
│       ├── SettingsScreen      — 设置
│       └── LevelHistoryScreen  — 等级变化趋势
│
└── Modals
    ├── UploadModal              — 上传流程（视频+手表选择）
    ├── CameraModal              — 拍摄视频（含引导线）
    └── ShareModal               — 报告分享
```

### 3.3 拍摄引导 UI

为帮助用户拍摄出可用于 CV 分析的视频，需要在拍摄/上传界面提供视觉引导：

```
┌──────────────────────────────┐
│      拍摄引导叠加层           │
│                              │
│   ┌──────────────────────┐   │
│   │  ═══════════════════ │ ← 球网参考线
│   │                      │   │
│   │    ·  底线后方        │   │
│   │    ↕ 约2m            │   │
│   │                      │   │
│   │  ┌────────────────┐ │   │
│   │  │ ⚠️ 球员应在此   │ │   │  ← 人物站位提示框
│   │  │   区域内移动    │ │   │
│   │  └────────────────┘ │   │
│   │                      │   │
│   └──────────────────────┘   │
│                              │
│  📐 请保持手机横屏拍摄        │
│  🔆 避免逆光拍摄              │
│  📍 建议位置：底线正后方 2m    │
│  ⏱️ 建议拍摄 ≥15 分钟对抗    │
│                              │
│      [ 开始拍摄 ]            │
└──────────────────────────────┘
```

### 3.4 健康数据桥接层

针对三种手表品牌，需要通过不同 SDK 读取数据。设计统一的数据抽象层：

```typescript
// 统一健康数据接口
interface TennisHealthData {
  // 基础运动数据
  startTime: Date;
  endTime: Date;
  totalDuration: number;          // 秒

  // 心率数据（1Hz 时间序列）
  heartRate: {
    timestamps: number[];         // Unix ms
    values: number[];             // bpm
    zones: HeartRateZone[];       // Zone 1-5 分布
  };

  // 运动数据
  movement: {
    totalDistance: number;        // 米
    avgSpeed: number;             // m/s
    maxSpeed: number;             // m/s
    steps: number;                // 总步数
    cadence: number[];            // 步频序列 (steps/min)
  };

  // 位置数据（如果手表支持 GPS）
  gps?: {
    timestamps: number[];
    latitudes: number[];
    longitudes: number[];
    accuracies: number[];         // 精度半径（米）
  };

  // 加速度计数据（如果可获取原始数据）
  imu?: {
    timestamps: number[];
    accelX: number[];
    accelY: number[];
    accelZ: number[];
  };

  // 能量消耗
  energy: {
    activeCalories: number;       // kcal
    totalCalories: number;
    avgMETs: number;
  };

  // 数据来源
  source: 'apple_watch' | 'oppo_watch' | 'huawei_watch' | 'fit_file';
  sourceDeviceModel: string;
}

// 各品牌 SDK 适配器
interface HealthDataAdapter {
  readonly brand: string;
  authorize(): Promise<boolean>;
  queryWorkouts(from: Date, to: Date): Promise<WorkoutSummary[]>;
  getWorkoutDetail(workoutId: string): Promise<TennisHealthData>;
  subscribeToWorkouts(callback: (workout: WorkoutSummary) => void): void;
}
```

**品牌适配详情：**

| 品牌 | SDK / API | 读取方式 | 数据类型 | 限制 |
|------|-----------|----------|----------|------|
| **Apple Watch** | HealthKit (iOS) | 应用内授权 → 读取 HKWorkout | HR(1Hz) + GPS(1Hz) + IMU(100Hz) | GPS 精度 3-5m；IMU 需 Watch 6+ |
| **OPPO Watch** | OPPO Health SDK (Android) | 应用内授权 → Content Provider | HR(1Hz) + GPS(1Hz) + 步频 | GPS 取决于手表型号；IMU 不可导出 |
| **华为 Watch** | Huawei Health Kit (Android) | HMS Core 集成 → 授权读取 | HR(1Hz) + GPS(1Hz) + 步频 + 部分 IMU | 需注册华为开发者账号 |
| **通用兜底** | FIT / TCX / GPX 文件导入 | 手动导出 → App内上传 | HR + GPS + 步频 | 依赖用户手动导出 |

### 3.5 视频预处理（客户端）

为减少上传带宽消耗和云端处理压力，在客户端进行预处理：

```
客户端视频预处理流水线：

原始视频 (4K/1080p, 60fps, HEVC)
    │
    ├──→ [1] 视频压缩
    │       ├── 分辨率: 1080p (短边)
    │       ├── 帧率: 30fps (保留足够时序信息)
    │       ├── 编码: H.264 (兼容性好)
    │       ├── 码率: 8 Mbps (运动场景足够)
    │       └── 工具: ffmpeg-kit, GPU 加速 (VideoToolbox/MediaCodec)
    │
    ├──→ [2] 关键帧抽取
    │       ├── 每 2 秒抽取 1 帧 (作为快速预览/校验)
    │       ├── 上传到服务端做初步场景检测
    │       └── 用于球场标定的候选帧筛选
    │
    ├──→ [3] 分段上传
    │       ├── TUS 协议 (断点续传)
    │       ├── 每段 10-20MB (网络容错)
    │       └── 并发 3 段上传
    │
    └──→ [4] 元数据上报
            ├── 视频时长、分辨率、帧率、编码格式
            ├── 设备型号、OS 版本
            ├── 拍摄位置描述（底线后方 / 侧方 45°）
            └── 上传时间戳（与服务端对时）
```

---

## 四、视频理解引擎

这是整个系统最核心的技术模块。**从视频到结构化技术指标**需要经过多级处理流水线。

### 4.1 视频处理流水线

```
                   原始视频 (1080p, 30fps, ~15-60 min)
                               │
              ┌────────────────┼────────────────┐
              ▼                ▼                ▼
        ┌──────────┐   ┌──────────────┐   ┌──────────┐
        │ 场景检测 │   │  球场标定     │   │ 音轨分离 │
        └────┬─────┘   └──────┬───────┘   └────┬─────┘
             │                │                │
             ▼                ▼                ▼
    ┌────────────────┐ ┌──────────────┐ ┌──────────────┐
    │ 有效片段提取    │ │ 单应性矩阵   │ │ 击球声检测    │
    │ - 丢分/回合分割│ │ - 球场坐标系  │ │ - 击球事件标记│
    │ - 死球时间剔除 │ │ - 像素→米映射│ │ - 非受迫失误  │
    └───────┬────────┘ └──────┬───────┘ └──────┬───────┘
            │                 │                │
            └────────┬────────┼────────┬───────┘
                     │        │        │
                     ▼        ▼        ▼
              ┌─────────────────────────────────────┐
              │        时序对齐 & 事件融合            │
              │  · 每个 point 的开始/结束时间          │
              │  · 每个击球事件的时间戳 + 类型         │
              │  · 每个回合的拍数 + 结果               │
              └─────────────────┬───────────────────┘
                                │
                                ▼
              ┌─────────────────────────────────────┐
              │         并行处理：每个有效片段         │
              │                                     │
              │  ┌──────────┐  ┌──────────────┐    │
              │  │ 姿态估计  │  │  球 3D 追踪   │    │
              │  │ (每帧)   │  │  (每帧)       │    │
              │  └────┬─────┘  └──────┬───────┘    │
              │       │               │             │
              │       ▼               ▼             │
              │  ┌──────────┐  ┌──────────────┐    │
              │  │ 动作分割  │  │  轨迹分析     │    │
              │  │ (击球阶段)│  │  (速度/旋转)  │    │
              │  └────┬─────┘  └──────┬───────┘    │
              │       │               │             │
              │       └───────┬───────┘             │
              │               ▼                     │
              │  ┌──────────────────────────┐      │
              │  │    击球事件结构化数据      │      │
              │  │  (ShotEvent 数据结构)     │      │
              │  └──────────────────────────┘      │
              └─────────────────────────────────────┘
                                │
                                ▼
              ┌─────────────────────────────────────┐
              │          全局聚合分析                  │
              │  · 全视频 ShotEvent[] 聚合统计         │
              │  · 分时段对比（前半 vs. 后半）          │
              │  · 失误模式聚类分析                    │
              │  · 站位热力图                          │
              └─────────────────────────────────────┘
```

### 4.2 球场标定

球场标定是后续所有空间分析的基础——建立像素坐标到真实世界坐标的映射。

```
算法流程:
  输入: 包含完整球场的视频帧
  输出: 单应性矩阵 H (3×3), 像素→米 映射

  Step 1: 球场线检测
          - Canny 边缘检测
          - HoughLinesP 检测线段
          - 基于颜色掩码过滤白色线条区域

  Step 2: 球场模板匹配
          - 已知标准网球场尺寸: 23.77m × 10.97m (双打)
          - 检测到的线段聚类 → 找到底线+边线+发球线
          - 通过几何约束验证（平行/垂直/距离比例）

  Step 3: 单应性矩阵计算
          - 4+ 对应点对（图像像素 ↔ 球场坐标）
          - 用 RANSAC 排除异常点
          - 计算单应性矩阵 H

  Step 4: 坐标变换
          - 任意像素点 (u, v) → 球场坐标 (x, y) via H
          - 误差: 目标 < 15cm (典型手机视频距离)
```

**球场坐标系定义：**

```
          x (m) →
    ┌─────────────────────────┐
    │  0                 10.97│  ← 底线 (y = 11.885)
    │                         │
    │   ┌─────────────────┐   │
    │   │                 │   │  ← 发球线 (y = 6.40)
    │   │    发球区       │   │
    │   ├────────┬────────┤   │
    │   │   T点  │  T点   │   │  ← 中线
    │   ├────────┴────────┤   │
    │   │    发球区       │   │
    │   └─────────────────┘   │  ← 发球线 (y = 5.485)
    │                         │
    │  0                 10.97│  ← 底线 (y = 0)
    └─────────────────────────┘
    y (m) ↓                     球员A在 y<0 侧, 球员B在 y>11.885 侧
```

### 4.3 姿态估计

使用 MediaPipe Pose (BlazePose GHUM 3D) 进行逐帧 3D 人体姿态估计。

```
输出: 33 个 3D 关键点 (x, y, z 相对坐标 + 可见度)
频率: 30fps (与视频帧率同步)

关键点索引 (MediaPipe 标准):
  0: 鼻尖        11: 左肩        12: 右肩
  13: 左肘        14: 右肘
  15: 左手腕      16: 右手腕       ← 握拍手关键
  17: 左小指      18: 右小指
  19: 左食指      20: 右食指
  23: 左髋        24: 右髋
  25: 左膝        26: 右膝
  27: 左脚踝      28: 右脚踝
  29: 左脚跟      30: 右脚跟
  31: 左脚尖      32: 右脚尖
```

**从姿态提取的网球专项特征：**

```python
@dataclass
class PoseFeatures:
    """从姿态关键点计算的网球专项特征"""
    # 身体朝向
    shoulder_angle: float          # 双肩连线与底线夹角 (deg)
    hip_angle: float               # 双髋连线与底线夹角 (deg)

    # 引拍阶段
    backswing_amplitude: float     # 球拍手后引距离 (m)
    shoulder_rotation: float       # 肩部旋转角度 (deg)
    hip_rotation: float            # 髋部旋转角度 (deg)
    unit_turn_ratio: float         # 转体充分度: hip_rot / shoulder_rot

    # 击球阶段
    contact_point_x: float         # 击球点前后位置 (m, 相对身体)
    contact_point_y: float         # 击球点高度 (m)
    contact_point_z: float         # 击球点左右位置 (m, 相对身体)
    knee_flexion: float            # 膝部弯曲角度

    # 随挥阶段
    follow_through_length: float   # 随挥路径长度
    follow_through_height: float   # 随挥终点高度

    # 脚步
    split_step_timing: float       # 分腿垫步与对手击球的时间差 (s)
    stance_width: float            # 击球时双脚间距
    weight_transfer_distance: float # 重心转移距离
```

### 4.4 球追踪与轨迹重建

使用 TrackNet V3 进行球的 2D 检测，结合单应性矩阵重建 3D 轨迹。

```
模型: TrackNet V3 (基于 ResNet-50 的 heatmap 回归)
输入: 连续视频帧 (默认 3 帧堆叠)
输出: 球中心点的 2D heatmap → argmax → (u, v)

3D 重建:
  1. 2D 检测 (u, v) → 单应性逆变换 → 球场坐标 (x, y)
  2. 球高度 z 估计:
     - 基于球的视觉大小（远小近大）
     - 或基于球阴影与球的位置偏差
     - 简化方案: 二分法，已知球过网高度 ≈ 1-2m 约束
  3. 轨迹平滑: Kalman 滤波器
  4. 落点检测: 轨迹与地面 (z=0) 的交点
```

**从球轨迹提取的特征：**

```python
@dataclass
class BallTrajectoryFeatures:
    """从球轨迹提取的特征"""
    # 速度
    incoming_speed: float          # 来球速度 (km/h)
    outgoing_speed: float          # 回球速度 (km/h)
    speed_ratio: float             # 回球速度 / 来球速度

    # 弧线
    max_height: float              # 球过网最高点 (m)
    net_clearance: float           # 过网高度 (m)
    trajectory_curvature: float    # 弧线曲率 (判断上旋/平击)

    # 落点
    bounce_x: float                # 落点 x 坐标
    bounce_y: float                # 落点 y 坐标
    depth_in_court: float          # 落点距底线距离 (m)
    line_type: str                 # "cross_court" | "down_the_line" | "middle"

    # 旋转估计（基于轨迹偏转）
    estimated_spin_type: str       # "topspin" | "flat" | "slice" | "unknown"
    lateral_deflection: float      # 落地后侧向偏转量 (m)
```

### 4.5 击球事件检测与分割

将视频自动切分为独立击球事件，是整个分析的基础：

```
击球事件检测:

  信号源融合:
  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
  │ 音频: 击球声  │  │ 姿态: 挥拍动作│  │ 轨迹: 球方向  │
  │ 峰值检测      │  │ 速度峰值      │  │ 突变          │
  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘
         │                 │                 │
         └────────┬────────┼────────┬────────┘
                  │        │        │
                  ▼        ▼        ▼
            ┌──────────────────────────────┐
            │  加权融合 → 击球时刻 t_shot    │
            │  权重: 音频 0.3 + 姿态 0.4    │
            │       + 轨迹 0.3              │
            └──────────────┬───────────────┘
                           │
                           ▼
            ┌──────────────────────────────┐
            │  以 t_shot 为中心取窗口:       │
            │  [t-1.5s, t+2.0s] → 单次击球片段│
            │  包含: 准备→引拍→击球→随挥→恢复  │
            └──────────────────────────────┘
```

**击球事件数据结构：**

```python
@dataclass
class ShotEvent:
    """单次击球的完整结构化数据"""
    # 基础信息
    shot_id: str                   # 唯一标识
    timestamp: float               # 击球时刻 (秒, 从视频开始)
    clip_start: float              # 片段起始时间
    clip_end: float                # 片段结束时间

    # 击球类型
    shot_type: str                 # "forehand"|"backhand"|"serve"|"volley"
                                   # |"overhead"|"drop_shot"|"lob"|"slice"
    shot_subtype: str              # "topspin"|"flat"|"slice"|"kick"

    # 球员定位
    player_position: tuple         # (x, y) 击球时球员在球场的位置

    # 姿态特征
    pose_before: PoseFeatures      # 引拍完成时的姿态
    pose_at_contact: PoseFeatures  # 击球瞬间的姿态

    # 球轨迹
    incoming_ball: BallTrajectoryFeatures
    outgoing_ball: BallTrajectoryFeatures

    # 结果
    result: str                    # "in"|"net"|"out"|"winner"|"error"
    is_unforced_error: bool        # 是否为非受迫失误
    rally_shot_number: int         # 回合中第几拍

    # 上下文
    point_id: str                  # 所属的分数
    rally_id: str                  # 所属的回合
```

### 4.6 动作质量评估模型

这是最核心的"教练眼光"来源。需要训练一个评估模型：

```
方案: 对比学习 + 回归评分

训练流程:
  Step 1: 收集标注数据
          - 专业教练对击球片段进行 NTRP 等级标注
          - 每个片段: NTRP 1.0-7.0 等级 + 细分项评分 (0-100)

  Step 2: 特征编码
          - 姿态序列 (T×99 维) → Temporal Transformer Encoder → 固定维度嵌入
          - 球轨迹 (T×10 维) → 1D CNN → 固定维度嵌入
          - 球员位置 (T×2 维) → 编码为球场区域 one-hot
          - 多模态特征融合: Cross-Attention → 统一嵌入向量

  Step 3: 对比学习预训练
          - 正样本对: 同一球员同一技术类型的不同击球
          - 负样本对: 不同 NTRP 等级的击球
          - InfoNCE Loss 拉近同等级、拉远异等级

  Step 4: 回归微调
          - 在标注数据上 Fine-tune
          - 输出: NTRP 等级 (分类) + 各子项评分 (回归)

数据需求（MVP）:
  - 每个 NTRP 等级 ≥ 200 个击球片段
  - 每个片段有 3 位教练的独立评分（取中位数）
  - 覆盖: 正手/反手/发球/截击 四大类
  - 总计: ~10,000 个标注片段
```

### 4.7 分析产物汇总

视频处理完成后输出的结构化分析产物：

```python
@dataclass
class VideoAnalysisResult:
    """视频分析的完整产出"""
    video_id: str
    duration_analyzed: float        # 实际分析的有效时长 (分钟)
    total_shots: int                # 总击球数

    # 球场信息
    court_calibration: dict         # 单应性矩阵 + 球场角点坐标

    # 击球统计
    shots_by_type: dict             # {"forehand": 120, "backhand": 80, ...}
    shots_by_result: dict           # {"in": 200, "net": 15, "out": 25, ...}

    # 回合统计
    total_rallies: int              # 总回合数
    avg_rally_length: float         # 平均回合拍数
    rally_length_distribution: dict # 回合拍数分布

    # 技术指标 (按类型聚合)
    technique_metrics: dict         # {
                                    #   "forehand": {
                                    #     "avg_net_clearance": 1.2,
                                    #     "depth_compliance_rate": 0.65,
                                    #     "line_change_success_rate": 0.55,
                                    #     ...
                                    #   },
                                    #   ...
                                    # }

    # 位置数据
    position_heatmap: np.ndarray    # 球员位置热力图 (100×50 网格)
    court_coverage_ratio: float     # 实际覆盖面积 / 半场面积

    # 失误分析
    error_analysis: dict            # {
                                    #   "total_unforced_errors": 22,
                                    #   "error_by_type": {"forehand": 8, ...},
                                    #   "error_by_situation": {"deep_ball": 5, ...},
                                    # }

    # 所有击球事件
    shot_events: list[ShotEvent]

    # 分段分析 (前半 vs. 后半)
    segment_comparison: dict        # 体能下降导致的技术变化
```

---

## 五、手表数据引擎

### 5.1 数据处理流水线

```
运动手表原始数据
       │
       ├──→ Apple Watch: HealthKit Workout 数据
       ├──→ OPPO Watch: Content Provider 查询
       ├──→ 华为 Watch: Health Kit REST API
       └──→ 手动导入: FIT/TCX/GPX 文件解析
              │
              ▼
       ┌──────────────────┐
       │  数据标准化层     │
       │  → TennisHealthData │  (统一数据结构, 见 3.4 节)
       └────────┬─────────┘
                │
                ▼
       ┌──────────────────┐
       │  降噪与插值       │
       │  · HR: 中值滤波   │
       │  · GPS: Kalman   │
       │  · IMU: 巴特沃斯  │
       │  · 时间戳重采样   │
       │    (统一 1Hz)     │
       └────────┬─────────┘
                │
                ▼
       ┌──────────────────┐
       │  特征提取         │
       │  (见 5.2 节)      │
       └────────┬─────────┘
                │
                ▼
       ┌──────────────────┐
       │  体能评估         │
       │  (见 5.3 节)      │
       └──────────────────┘
```

### 5.2 网球专项体能特征提取

```python
@dataclass
class FitnessFeatures:
    """从手表数据提取的网球专项体能特征"""

    # === 心肺功能 ===
    avg_heart_rate: float               # 平均心率 (bpm)
    max_heart_rate: float               # 最大心率 (bpm)
    hr_zone_distribution: dict          # {"zone1": 0.15, "zone2": 0.35,
                                        #  "zone3": 0.30, "zone4": 0.15,
                                        #  "zone5": 0.05}
    hr_recovery_rate: float             # 分间心率恢复速率 (bpm/min)
    hr_variability: float               # 心率变异性 (SDNN, ms)

    # === 运动负荷 ===
    training_impulse: float             # TRIMP 训练冲量
    epoc: float                         # 运动后过量氧耗 (ml/kg)
    training_load_score: float          # 0-100 综合训练负荷评分

    # === 移动能力 ===
    total_distance: float               # 总跑动距离 (m)
    distance_per_minute: float          # 每分钟跑动距离 (m/min)
    max_speed: float                    # 最大速度 (km/h)
    avg_speed: float                    # 平均速度 (km/h)

    # === 敏捷性 ===
    acceleration_peak: float            # 启动加速度峰值 (m/s²)
    deceleration_count: int             # 急停次数
    direction_change_count: int         # 变向次数
    avg_reaction_time: float            # 平均反应时间 (s, 基于加速度突变)

    # === 步频 ===
    avg_cadence: float                  # 平均步频 (steps/min)
    cadence_variability: float          # 步频变异性

    # === 分段对比（检测体能衰减）===
    first_half: dict                    # 前半段指标
    second_half: dict                   # 后半段指标
    fatigue_ratio: float                # 体能衰减率 (后半/前半)
```

### 5.3 体能评估输出

```python
class FitnessAssessment:
    """网球专项体能评估"""

    def assess(self, features: FitnessFeatures, player_ntrp: float) -> dict:
        return {
            # 综合体能等级 (NTRP 对标)
            "fitness_ntrp_equivalent": self._estimate_fitness_ntrp(features),

            # 各项评分
            "cardiovascular_endurance": {  # 有氧耐力
                "score": 72,               # 0-100
                "ntrp_benchmark": 75,      # 当前等级基准
                "gap": -3,
                "status": "below_average"
            },
            "anaerobic_power": {           # 无氧爆发力
                "score": 68,
                "ntrp_benchmark": 70,
                "gap": -2,
                "status": "average"
            },
            "agility": {                   # 敏捷性
                "score": 65,
                "ntrp_benchmark": 75,
                "gap": -10,                # ⚠️ 明显短板
                "status": "weakness"
            },
            "recovery_ability": {          # 恢复能力
                "score": 80,
                "ntrp_benchmark": 70,
                "gap": +10,                # ✅ 优势
                "status": "strength"
            },
            "movement_efficiency": {       # 移动效率
                "score": 70,
                "ntrp_benchmark": 70,
                "gap": 0,
                "status": "average"
            },

            # 疲劳分析
            "fatigue": {
                "performance_drop": 0.12,   # 后半段表现下降 12%
                "hr_drift": 0.08,          # 心率漂移 8%
                "is_fatigue_significant": True,
                "recommendation": "建议加强耐力训练, 重点提升后半段移动保持率"
            },

            # 训练负荷建议
            "training_load": {
                "current_session_load": "moderate",
                "recommended_weekly_volume": "3-4 sessions",
                "recovery_needed_hours": 24,
            }
        }
```

---

## 六、多模态对齐引擎

### 6.1 对齐策略

这是连接视频分析和手表数据的关键环节。

```
对齐目标: 将每个 ShotEvent.timestamp 与手表数据的对应时刻精确关联

挑战:
  - 视频时钟 vs 手表时钟 可能不同步 (几秒到几分钟偏差)
  - 手表数据可能有 GPS 丢帧、HR 采样不均匀
  - 视频中可能有暂停拍摄、死球时间等

对齐方案: 三层级联对齐

  Level 1 — 粗对齐 (时间戳)
      视频录制开始时间 ≈ 手表 Workout 开始时间
      → 对齐误差: ±30 秒
      → 方法: 用户确认开始/结束时间戳

  Level 2 — 细对齐 (运动模式匹配)
      从视频提取的"移动强度序列":
        每 5 秒窗口内的球员位移量
      从手表提取的"运动强度序列":
        每 5 秒窗口内的加速度幅度 / 速度
      → 互相关 (Cross-Correlation) 找到最佳偏移量
      → 对齐误差: ±2 秒

  Level 3 — 精对齐 (生理信号)
      击球时刻 → HR 微升 (约 1-2 秒延迟)
      连续多拍高强度回合 → HR 持续上升
      → 动态时间规整 (DTW) 对齐
      → 对齐误差: ±0.5 秒
```

### 6.2 对齐后的融合数据

```python
@dataclass
class AlignedShotEvent(ShotEvent):
    """融合了手表数据的击球事件"""
    # 手表数据 (对齐到击球时刻)
    hr_at_shot: float                   # 击球时的心率
    hr_5s_before: float                 # 击球前 5 秒平均心率
    acceleration_magnitude: float       # 击球时的加速度幅度
    speed_at_shot: float                # 击球时的移动速度
    position_from_gps: tuple            # GPS 位置 (如果可用)

    # 回合级数据
    rally_hr_avg: float                 # 整个回合的平均心率
    rally_hr_peak: float                # 回合内心率峰值
    rally_distance_covered: float       # 回合内跑动距离
    rally_energy_cost: float            # 回合能耗 (kcal)

    # 分间数据
    between_points_hr_recovery: float   # 分间心率恢复量
    between_points_time: float          # 分间间隔时间
```

---

## 七、三维度评估引擎

### 7.1 技术评估详细方案

技术评估的**核心逻辑**是将视频提取的技术指标与 NTRP 等级标准进行对标匹配。

**评估流程：**

```
Step 1: 技术特征标准化
  - 将原始指标 (速度、角度、比率) 转换为 0-100 评分
  - 评分函数基于 NTRP 手册中的量化基准

Step 2: NTRP 等级推算
  - 按手册规则: "未达标项目数 - 超标项目数 ≥ -1 即可定级"
  - 对每个技术模块（正手/反手/发球/…）独立推算
  - 综合等级 = 各模块等级的加权中位数

Step 3: 强弱项识别
  - 低于综合等级 0.5+ 的模块 → ⚠️ 短板
  - 高于综合等级 0.5+ 的模块 → ✅ 优势
  - 短板占比 > 30% → 降低综合等级置信度

Step 4: 对比诊断
  - 与目标等级的差距分析
  - 与同等级球员的百分位对比 (如果积累足够数据)
```

**NTRP 等级到技术指标的映射表（部分示例）：**

| 指标 | 2.0 基准 | 2.5 基准 | 3.0 基准 | 3.5 基准 | 4.0 基准 |
|------|----------|----------|----------|----------|----------|
| **正手深度达标率** | — | 60% | 70% | 80% | 85% |
| **正手线路变化成功率** | — | — | 55% | 70% | 75% |
| **反手侧身绕正手比例** | 不做限制 | <30% | <10% | <5% | 0% |
| **一发成功率** | 40% | 60% | 65% | 68% | 70% |
| **二发双误率** | 不做限制 | <10% | <5% | <3% | <2% |
| **接发成功率** | — | 70% | 80% | 85% | 90% |
| **网前截击成功率** | — | 70% | 80% | 85% | 90% |
| **全场移动到位率** | — | 80% | 90% | 95% | 98% |
| **10+拍连续对拉能力** | 偶尔 | 稳定 | 频繁 | 常态 | 常态 |
| **非受迫失误率** | 不评估 | <30% | <20% | <12% | <8% |

### 7.2 体能评估详细方案

评估逻辑同技术评估，将体能指标与 NTRP 手册中的体能描述进行对标：

| NTRP 等级 | 体能要求的量化解读 |
|-----------|-------------------|
| 2.0–2.5 | 能完成慢节奏短回合，无专项体能要求 |
| 3.0 | 全场覆盖到位率 ≥80%，能完成 1 盘单打，后半盘动作不变形 |
| 3.5 | 全场覆盖到位率 ≥90%，1 盘对抗中后半盘非受迫失误率上升 ≤20%，分间心率恢复良好 |
| 4.0 | 移动到位率 ≥95%，能完成 3 盘 2 胜单打，后半盘无明显能力下降 |
| 4.5 | 移动到位率 ≥98%，职业级体能储备，多盘全程稳定，非受迫失误率波动 ≤5% |

### 7.3 战术评估详细方案（Phase 2+）

战术评估需要分析球员的决策模式，技术难度最高：

```
战术评估子模块:

  1. 打法风格分类
     输入: 站位分布 + 击球类型分布 + 上网频率
     输出: "底线防守型" | "底线进攻型" | "全场型" | "发球上网型" | "防守反击型"

  2. 得分模式分析
     输入: 所有得分点的 ShotEvent 序列
     输出: {
       "winner_patterns": {"forehand_cross_court": 35%, "serve_ace": 15%, ...},
       "forced_error_patterns": {...},
       "unforced_error_patterns": {"backhand_deep_ball": 25%, ...}
     }

  3. 决策质量评估
     输入: 关键决策时刻 (如浅球是否上网、是否变线)
     输出: 决策正确率 (基于结果和 NTRP 标准)
     例: "3.0 水平球员在浅球(落点发球线内)出现时, 上网率为 25%,
          同级标准为 40%+, 建议提升浅球上网意识"

  4. 关键分心理分析
     输入: 关键分 vs. 普通分的 HR / 动作一致性 / 失误率 对比
     输出: {
       "hr_increase_on_key_points": 8,       # 关键分心率增加 8 bpm
       "error_rate_increase": 0.22,           # 关键分失误率上升 22%
       "technique_deformation_detected": True # 检测到动作变形
     }
```

### 7.4 综合评估输出

```python
@dataclass
class ComprehensiveAssessment:
    """三维度综合评估结果"""
    assessment_id: str
    user_id: str
    created_at: datetime

    # NTRP 评级
    overall_ntrp: float                     # 综合 NTRP 等级 (e.g., 3.0)
    ntrp_confidence: float                  # 置信度 0-1
    ntrp_by_module: dict                    # {"forehand": 3.0, "backhand": 2.5, ...}

    # 三维度评分
    technique_score: float                  # 技术总分 0-100
    fitness_score: float                    # 体能总分 0-100
    tactics_score: float                    # 战术总分 0-100

    # 各维度详情
    technique_breakdown: dict               # 各技术模块的详细评分
    fitness_breakdown: dict                 # 各体能指标的详细评分
    tactics_breakdown: dict                 # 各战术指标的详细评分

    # 强弱项
    strengths: list[str]                    # ["发球", "有氧耐力"]
    weaknesses: list[str]                   # ["反手", "网前截击", "敏捷性"]

    # 与目标等级差距
    target_ntrp: float
    gaps: dict                              # {"正手深度控制": -15, "反手稳定性": -22, ...}

    # 失误模式
    primary_error_patterns: list[dict]      # [{"type": "反手深球受迫失误", "count": 12, "pct": 0.35}, ...]

    # 体能衰减
    fatigue_impact: dict                    # {"movement_drop": 0.12, "error_increase": 0.18, ...}
```

---

## 八、RAG 知识库与建议生成

### 8.1 知识库构建

基于 NTRP 手册（已上传的完整文档），构建结构化知识库：

```
知识库拆分策略 (按手册第三部分建议):

  索引结构:
  {
    "doc_id": "ntrp_3_0_forehand",
    "ntrp_level": 3.0,
    "module": "forehand",
    "category": "teaching_points",  # teaching_points | errors | training_plan
    "language": "zh",
    "content": "熟练掌握上旋击球技术...",
    "key_metrics": ["depth_compliance", "line_change_success"],
    "difficulty": "intermediate",
    "prerequisites": ["ntrp_2_5_forehand"]
  }

  拆分粒度:
  - Chunk 大小: 300-500 tokens (手册推荐)
  - 块重叠: 10%-15%
  - 每个 Chunk 独立可检索、独立有意义

  总文档量估算:
  - 评级手册 (1.0-7.0): 13 个等级 × ~3 个分块 ≈ 40 个 chunk
  - 教学指南 (2.0-4.0): 5 个等级 × 6 模块 × 3 类别 ≈ 90 个 chunk
  - 高级教学 (4.5-5.5): 3 个等级 × ~4 个 chunk ≈ 12 个 chunk
  - 总计: ~150 个高质量 chunk
```

### 8.2 RAG 检索流程

```
用户评估结果 (弱项=反手深度控制, NTRP=3.0, 目标=3.5)
                          │
         ┌────────────────┼────────────────┐
         ▼                ▼                ▼
   ┌───────────┐   ┌───────────┐   ┌───────────┐
   │ 弱项检索   │   │ 等级检索   │   │ 目标检索   │
   │ "反手"     │   │ "3.0"     │   │ "3.5"     │
   │ "深度控制" │   │           │   │           │
   └─────┬─────┘   └─────┬─────┘   └─────┬─────┘
         │               │               │
         ▼               ▼               ▼
   ┌───────────┐   ┌───────────┐   ┌───────────┐
   │ 错误纠正   │   │ 当前水平   │   │ 进阶方向   │
   │ 训练方法   │   │ 教学要点   │   │ 目标基准   │
   │ e.g.,     │   │ e.g.,     │   │ e.g.,     │
   │ "击球点   │   │ "3.0反手  │   │ "3.5反手  │
   │  靠后纠正"│   │  回球深度 │   │  能处理   │
   │           │   │  达标率   │   │  高速来球"│
   │           │   │  ≥75%"    │   │           │
   └─────┬─────┘   └─────┬─────┘   └─────┬─────┘
         │               │               │
         └───────────────┼───────────────┘
                         │
                         ▼
               ┌──────────────────┐
               │ 结果融合 + 去重   │
               │ Top-10 最相关     │
               │ chunk             │
               └────────┬─────────┘
                        │
                        ▼
               ┌──────────────────┐
               │ Prompt 组装       │
               │ (见 8.3 节)      │
               └────────┬─────────┘
                        │
                        ▼
               ┌──────────────────┐
               │ Claude Sonnet 4.6 │
               │ 生成最终报告      │
               └──────────────────┘
```

### 8.3 LLM Prompt 设计

```markdown
# System Prompt

你是一位经验丰富的 NTRP 认证网球教练，拥有 20 年一线教学经验。
你精通从 NTRP 1.0 到 7.0 全等级的技术教学、体能训练和战术指导。

## 你的核心能力
1. 基于视频分析和运动手表数据，精准评估球员的 NTRP 等级
2. 识别球员在技术、体能、战术三个维度的优势和短板
3. 基于 NTRP 教学体系，生成个性化、可落地的训练方案
4. 所有建议必须基于 NTRP 官方教学指南，不得凭空编造

## 输出要求
- 使用专业但易懂的语言，避免过于学术的术语
- 所有训练建议必须标注来源（引用 NTRP 教学指南的具体章节）
- 量化指标优先，避免模糊描述（"多练反手" ❌ → "每次训练完成 4 组 × 15 球反手强制击球练习" ✅）
- 考虑国内业余选手每周 1-2 次训练的实际情况，训练计划必须在标准球场和居家条件下可执行

## 安全与边界
- 如果你是 4.0+ 的球员，请明确标注"建议同步咨询线下专业教练"
- 涉及伤病史的训练建议必须标注"请先咨询医生/康复师"
- 如果视频质量不足以支撑准确分析，诚实告知而非猜测

## RAG 上下文
以下是与你当前分析的球员水平和弱项最相关的 NTRP 教学指南内容：

{retrieved_chunks}
```

### 8.4 训练计划生成

训练计划生成遵循 NTRP 手册中的模板结构，由 LLM 结合检索内容自动生成：

```python
@dataclass
class TrainingPlan:
    """个性化训练计划"""
    plan_id: str
    assessment_id: str
    created_at: datetime

    # 计划周期
    duration_weeks: int             # 计划周期 (推荐 4 周)
    sessions_per_week: int          # 每周训练次数

    # 核心目标 (2-3 个)
    primary_goals: list[dict]       # [{"goal": "反手深度控制达标率从52%→70%",
                                    #   "metric": "depth_compliance",
                                    #   "current": 52, "target": 70}, ...]

    # 每周训练方案
    weekly_plans: list[dict]        # [
                                    #   {
                                    #     "week": 1,
                                    #     "focus": "反手稳定性 + 底线深度",
                                    #     "sessions": [
                                    #       {
                                    #         "day": 1,
                                    #         "duration_minutes": 150,
                                    #         "structure": [
                                    #           {"phase": "warmup", "duration": 20, "activities": [...]},
                                    #           {"phase": "technical", "duration": 60, "drills": [
                                    #             {
                                    #               "name": "反手位强制反手多球",
                                    #               "sets": 4,
                                    #               "reps_per_set": 15,
                                    #               "focus": "禁止侧身绕正手",
                                    #               "source": "NTRP 2.5 常见错误 #2"
                                    #             },
                                    #             ...
                                    #           ]},
                                    #           {"phase": "tactical", "duration": 40, ...},
                                    #           {"phase": "fitness", "duration": 20, ...},
                                    #           {"phase": "cooldown", "duration": 10, ...}
                                    #         ]
                                    #       },
                                    #       ...
                                    #     ]
                                    #   },
                                    #   ...
                                    # ]

    # 关键技术纠正点
    correction_drills: list[dict]   # [{"issue": "反手侧身绕正手",
                                    #   "correction": "反手位强制反手多球",
                                    #   "source": "NTRP 2.5 错误纠正 #2"}, ...]

    # 居家辅助训练
    home_exercises: list[dict]      # 无器械居家可做的辅助训练

    # 复评建议
    reassessment_recommendation: str  # "建议 4 周后进行复评"
```

---

## 九、后端服务设计

### 9.1 微服务拆分

```
服务列表:

  1. api-gateway (Kong)
     - 统一认证 (JWT + OAuth2)
     - 限流 (用户级别: 每日 3 次分析)
     - 路由转发
     - 请求日志

  2. user-service (FastAPI)
     - 用户注册/登录 (手机号/微信/Apple ID)
     - 个人信息管理
     - 等级历史查询
     - 健康数据授权管理

  3. video-service (FastAPI)
     - 视频上传 (TUS 协议)
     - 视频存储管理
     - 视频处理状态查询
     - 视频预处理触发

  4. analysis-orchestrator (FastAPI + Celery)
     - 分析任务创建与管理
     - 流水线编排 (Airflow-lite)
     - 任务状态推送 (WebSocket)
     - 结果聚合与存储

  5. ai-video-engine (独立 Python Worker)
     - 球场标定
     - 姿态估计 (GPU)
     - 球追踪 (GPU)
     - 动作分割与分类
     - 技术特征提取

  6. ai-fitness-engine (Python Worker)
     - 手表数据解析
     - 标准化与降噪
     - 体能特征提取
     - 体能评估

  7. ai-assessment-engine (Python Worker)
     - 多模态数据融合
     - NTRP 等级推算
     - 三维度评估
     - 强弱项识别

  8. ai-prescription-engine (Python Worker)
     - RAG 检索
     - LLM 推理 (Claude API 调用)
     - 训练计划生成
     - 报告渲染

  9. notification-service
     - 推送通知 (APNs / FCM)
     - 分析完成通知
     - 训练提醒
```

### 9.2 分析任务编排 (Celery Workflow)

```python
# 网球分析主流水线 (Celery Canvas)

from celery import chain, chord, group

@celery_app.task
def analyze_tennis_session(video_id: str, health_data_id: str, user_id: str):
    """
    网球分析主任务 - 编排整个分析流水线
    """
    workflow = chain(
        # Step 1: 并行预处理
        chord(
            group(
                process_video.s(video_id),           # 视频预处理
                process_health_data.s(health_data_id) # 手表数据预处理
            ),
            validate_inputs.s()                       # 验证输入完整性
        ),

        # Step 2: 并行深度分析 (两个独立流)
        group(
            # 视频分析流
            chain(
                calibrate_court.s(),                   # 球场标定
                detect_shot_events.s(),                # 击球事件检测
                chord(
                    group(
                        estimate_pose.s(),              # 姿态估计 (全视频)
                        track_ball.s(),                 # 球追踪 (全视频)
                    ),
                    fuse_pose_and_ball.s()              # 融合姿态+球数据
                ),
                classify_shots.s(),                    # 击球分类
                extract_technique_features.s(),         # 技术特征提取
            ),

            # 手表数据分析流
            chain(
                denoise_health_data.s(),                # 降噪
                extract_fitness_features.s(),           # 体能特征提取
            ),
        ),

        # Step 3: 多模态对齐
        align_video_and_watch.s(),                     # 视频↔手表时间对齐

        # Step 4: 三维度评估
        chord(
            group(
                assess_technique.s(),                   # 技术评估
                assess_fitness.s(),                     # 体能评估
                assess_tactics.s(),                     # 战术评估
            ),
            merge_assessments.s()                       # 合并评估结果
        ),

        # Step 5: 生成报告
        chain(
            retrieve_ntrp_knowledge.s(),                # RAG 检索
            generate_report.s(),                        # LLM 生成报告
            render_and_store.s(),                       # 渲染并存储
        ),

        # Step 6: 通知用户
        notify_user.s(user_id),                         # 推送通知
    )

    return workflow.apply_async()
```

### 9.3 GPU 资源规划

```
推理负载估算 (每次分析):

  输入: 30 分钟视频, 1080p, 30fps
  有效帧: ~30 × 60 × 30 × 0.7(去死球时间) ≈ 37,800 帧
  有效击球片段: ~300-500 个

  计算量:
  ┌──────────────────┬─────────────┬──────────────┬─────────────┐
  │ 任务              │ 模型         │ 单帧耗时     │ 总耗时       │
  ├──────────────────┼─────────────┼──────────────┼─────────────┤
  │ 姿态估计          │ MediaPipe   │ ~5ms (GPU)   │ ~3 min      │
  │ 球追踪            │ TrackNet V3 │ ~8ms (GPU)   │ ~5 min      │
  │ 击球分类          │ VideoMAE    │ ~50ms/clip   │ ~0.5 min    │
  │ 动作分割          │ 规则+分类器  │ —            │ ~0.5 min    │
  │ 球场标定          │ 传统CV      │ —            │ ~0.2 min    │
  │ LLM 推理          │ Claude API  │ —            │ ~0.5 min    │
  ├──────────────────┼─────────────┼──────────────┼─────────────┤
  │ 合计 (并行优化后)  │             │              │ ~6-8 min    │
  └──────────────────┴─────────────┴──────────────┴─────────────┘

  GPU 需求 (支撑每日 100 次分析):
  - 2× NVIDIA L40S (48GB) 或 4× A10G (24GB)
  - 可支持 4-6 路并发分析
```

---

## 十、数据库设计

### 10.1 PostgreSQL 核心表

```sql
-- 用户表
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    phone VARCHAR(20) UNIQUE,
    wechat_union_id VARCHAR(64) UNIQUE,
    apple_id VARCHAR(128) UNIQUE,
    nickname VARCHAR(64),
    avatar_url TEXT,
    gender VARCHAR(10),              -- 'male' | 'female' | 'other'
    birth_year INTEGER,
    playing_years FLOAT,             -- 球龄
    self_rated_ntrp FLOAT,           -- 自评 NTRP 等级
    target_ntrp FLOAT,               -- 目标 NTRP 等级
    handedness VARCHAR(10),          -- 'right' | 'left'
    grip_forehand VARCHAR(20),       -- 'semi_western' | 'eastern' | 'western'
    grip_backhand VARCHAR(20),       -- 'two_handed' | 'one_handed'
    injury_history TEXT[],           -- 伤病史标签
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 健康数据授权表
CREATE TABLE health_auths (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    source VARCHAR(20),              -- 'apple_health' | 'oppo_health' | 'huawei_health'
    authorized_at TIMESTAMPTZ,
    last_synced_at TIMESTAMPTZ,
    metadata JSONB,                  -- 设备信息等
    UNIQUE(user_id, source)
);

-- 视频表
CREATE TABLE videos (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    title VARCHAR(128),
    duration_seconds FLOAT,
    resolution_width INTEGER,
    resolution_height INTEGER,
    fps FLOAT,
    codec VARCHAR(20),
    file_size_bytes BIGINT,
    storage_path TEXT,               -- MinIO 存储路径
    camera_position VARCHAR(30),     -- 'behind_baseline' | 'side_45' | 'other'
    thumbnail_path TEXT,
    upload_status VARCHAR(20) DEFAULT 'uploading',
    -- 'uploading' | 'uploaded' | 'processing' | 'analyzed' | 'failed'
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 手表运动记录表
CREATE TABLE health_workouts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    source VARCHAR(20),
    source_workout_id VARCHAR(128),
    workout_type VARCHAR(30),        -- 'tennis' | 'training' | 'match'
    start_time TIMESTAMPTZ,
    end_time TIMESTAMPTZ,
    duration_seconds FLOAT,
    raw_data_path TEXT,              -- 原始数据存储路径
    processed_data JSONB,            -- 标准化后的数据
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 评估报告表
CREATE TABLE assessments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    video_id UUID REFERENCES videos(id),
    health_workout_id UUID REFERENCES health_workouts(id),

    -- NTRP 评级
    overall_ntrp FLOAT,
    ntrp_confidence FLOAT,

    -- 三维度总分
    technique_score FLOAT,           -- 0-100
    fitness_score FLOAT,             -- 0-100
    tactics_score FLOAT,             -- 0-100

    -- 分项评分 (JSONB 存储灵活结构)
    technique_breakdown JSONB,       -- {"forehand": {...}, "backhand": {...}, ...}
    fitness_breakdown JSONB,
    tactics_breakdown JSONB,

    -- 强弱项
    strengths TEXT[],
    weaknesses TEXT[],

    -- 分析元数据
    total_shots_analyzed INTEGER,
    valid_duration_minutes FLOAT,
    video_quality_score FLOAT,       -- 视频质量对分析可靠性的影响

    -- 报告
    report_markdown TEXT,            -- 完整 Markdown 报告
    report_json JSONB,               -- 结构化报告数据

    -- 状态
    status VARCHAR(20) DEFAULT 'processing',
    -- 'processing' | 'completed' | 'failed'
    error_message TEXT,
    processing_duration_seconds FLOAT,

    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 训练计划表
CREATE TABLE training_plans (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    assessment_id UUID REFERENCES assessments(id),

    duration_weeks INTEGER DEFAULT 4,
    sessions_per_week INTEGER,
    primary_goals JSONB,
    weekly_plans JSONB,              -- 完整的周训练方案
    correction_drills JSONB,         -- 纠错练习
    home_exercises JSONB,            -- 居家训练

    status VARCHAR(20) DEFAULT 'active',
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 训练打卡表
CREATE TABLE training_checkins (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    training_plan_id UUID REFERENCES training_plans(id),
    session_index INTEGER,           -- 第几次训练
    completed_at TIMESTAMPTZ,
    duration_minutes INTEGER,
    notes TEXT,
    health_workout_id UUID REFERENCES health_workouts(id),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 分析任务表
CREATE TABLE analysis_tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    video_id UUID REFERENCES videos(id),
    health_workout_id UUID REFERENCES health_workouts(id),
    assessment_id UUID REFERENCES assessments(id),
    celery_task_id VARCHAR(128),
    status VARCHAR(20) DEFAULT 'queued',
    -- 'queued' | 'processing' | 'completed' | 'failed'
    progress FLOAT DEFAULT 0,        -- 0-1
    current_stage VARCHAR(50),
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

### 10.2 Milvus 向量集合

```python
# NTRP 知识库 Collection
collection_name = "ntrp_knowledge"

schema = {
    "fields": [
        {"name": "id", "dtype": "INT64", "is_primary": True, "auto_id": True},
        {"name": "embedding", "dtype": "FLOAT_VECTOR", "dim": 1024},  # BGE-M3 维度
        {"name": "ntrp_level", "dtype": "FLOAT"},
        {"name": "module", "dtype": "VARCHAR", "max_length": 50},
        {"name": "category", "dtype": "VARCHAR", "max_length": 50},
        {"name": "language", "dtype": "VARCHAR", "max_length": 10},
        {"name": "content", "dtype": "VARCHAR", "max_length": 4096},
        {"name": "key_metrics", "dtype": "ARRAY", "element_type": "VARCHAR", "max_length": 50},
    ],
    "index": {
        "field_name": "embedding",
        "index_type": "IVF_FLAT",
        "metric_type": "COSINE",
        "params": {"nlist": 128}
    }
}
```

### 10.3 Redis 缓存设计

```
缓存键设计:
  # 用户 Session
  session:{session_id} → user_json (TTL: 7d)

  # 分析任务状态
  task:{task_id} → status_json (TTL: 1h)

  # 评估结果缓存 (热点数据)
  assessment:latest:{user_id} → assessment_summary_json (TTL: 24h)

  # 排行榜
  leaderboard:weekly → sorted_set (TTL: 7d)

  # API 限流
  ratelimit:{user_id}:{endpoint} → counter (TTL: window)

  # 视频上传进度
  upload:{video_id} → progress_json (TTL: 1h)
```

---

## 十一、API 设计

### 11.1 RESTful API 总览

```
Base URL: https://api.tenniscoach.ai/v1

认证方式: Bearer Token (JWT)

┌──────────────────────────────────────────────────────────────────┐
│  API 分组                  │  端点                               │
├──────────────────────────────────────────────────────────────────┤
│  认证                      │  POST   /auth/register              │
│                            │  POST   /auth/login                 │
│                            │  POST   /auth/refresh               │
│                            │  POST   /auth/wechat                │
│                            │  POST   /auth/apple                 │
├────────────────────────────┼─────────────────────────────────────┤
│  用户                      │  GET    /users/me                   │
│                            │  PATCH  /users/me                   │
│                            │  GET    /users/me/level-history     │
│                            │  DELETE /users/me                   │
├────────────────────────────┼─────────────────────────────────────┤
│  视频                      │  POST   /videos/upload/init         │
│                            │  PATCH  /videos/{id}/upload         │
│                            │  GET    /videos/{id}                │
│                            │  GET    /videos/{id}/status         │
│                            │  DELETE /videos/{id}                │
├────────────────────────────┼─────────────────────────────────────┤
│  健康数据                   │  GET    /health/sources             │
│                            │  POST   /health/authorize           │
│                            │  GET    /health/workouts            │
│                            │  GET    /health/workouts/{id}       │
│                            │  POST   /health/import/fit          │
├────────────────────────────┼─────────────────────────────────────┤
│  分析                      │  POST   /analysis/start             │
│                            │  GET    /analysis/tasks/{id}        │
│                            │  WS     /analysis/tasks/{id}/stream │
│                            │  GET    /analysis/assessments       │
│                            │  GET    /analysis/assessments/{id}  │
│                            │  GET    /analysis/assessments/{id}/report│
├────────────────────────────┼─────────────────────────────────────┤
│  训练计划                   │  GET    /training/plans             │
│                            │  GET    /training/plans/{id}        │
│                            │  POST   /training/plans/{id}/checkin│
│                            │  GET    /training/progress          │
└──────────────────────────────────────────────────────────────────┘
```

### 11.2 核心 API 详细定义

```yaml
# POST /analysis/start — 发起一次分析
Request:
  video_id: string (required)
  health_workout_id: string (optional, 手表数据)
  target_ntrp: float (optional, 目标等级)
  notes: string (optional, 用户备注，如"今天反手感觉特别差")

Response 202:
  task_id: string
  status: "queued"
  estimated_duration_seconds: 480  # 预估 8 分钟

# GET /analysis/tasks/{id} — 查询分析任务状态
Response 200:
  task_id: string
  status: "processing"  # queued | processing | completed | failed
  progress: 0.65         # 0-1
  current_stage: "姿态估计分析中..."
  stages:
    - name: "视频预处理"
      status: "completed"
      duration_seconds: 45
    - name: "姿态估计"
      status: "completed"
      duration_seconds: 180
    - name: "球轨迹追踪"
      status: "running"
      duration_seconds: null
    - name: "体能分析"
      status: "pending"
    - name: "综合评估"
      status: "pending"
    - name: "报告生成"
      status: "pending"
  assessment_id: null  # 完成后填充
  created_at: "2026-06-15T10:30:00Z"

# WebSocket /analysis/tasks/{id}/stream — 实时进度推送
Message types:
  {
    "type": "progress",
    "stage": "ball_tracking",
    "progress": 0.45,
    "message": "已追踪 234/520 次击球事件"
  }
  {
    "type": "stage_complete",
    "stage": "pose_estimation",
    "duration_seconds": 180,
    "summary": "识别正手击球 156 次, 反手 98 次, 发球 42 次"
  }
  {
    "type": "complete",
    "assessment_id": "abc-123",
    "summary": {
      "overall_ntrp": 3.0,
      "technique_score": 68,
      "fitness_score": 72,
      "tactics_score": 55
    }
  }

# GET /analysis/assessments/{id}/report — 获取完整报告
Response 200:
  assessment_id: string
  report: {
    markdown: string,        # 完整 Markdown 文本
    json: {                  # 结构化数据 (用于 App 渲染)
      overview: { ... },
      technique: { ... },
      fitness: { ... },
      tactics: { ... },
      training_plan: { ... },
      video_annotations: [   # 关键帧标注
        {
          timestamp: 125.5,
          shot_type: "backhand",
          issue: "击球点靠后",
          ideal_contact_point: {x: 0.3, y: 0.5},
          actual_contact_point: {x: -0.1, y: 0.5},
          screenshot_url: "..."
        }
      ]
    }
  }
```

---

## 十二、模型训练与数据标注

### 12.1 数据标注计划

| 标注类型 | 数据量需求 | 标注内容 | 标注方式 |
|----------|-----------|----------|----------|
| **击球分类** | 20,000 clips | 击球类型 (正手/反手/发球/截击…) + NTRP 粗略等级 | 众包 + 专家审核 |
| **动作质量评分** | 10,000 clips | 18 项技术指标评分 (0-100) + 3 位教练独立评分 | 专业教练标注 |
| **失误标注** | 5,000 clips | 失误类型 (受迫/非受迫) + 失误原因标签 | 专业教练标注 |
| **战术标注** | 2,000 rallies | 打法风格 + 战术决策正确性 + 得分模式 | 专业教练标注 |
| **球场标定** | 500 张 | 球场角点 + 单应性矩阵真值 | 工具辅助 + 人工校验 |

### 12.2 模型训练策略

```
Phase 1: 使用公开数据集 + 迁移学习
  - 姿态估计: MediaPipe 预训练模型 (无需标注)
  - 球追踪: TrackNet V3 (公开网球数据集: TennisSense, THE-17)
  - 击球分类: Kinetics-700 预训练 VideoMAE → 网球数据微调

Phase 2: 收集自有数据 + 微调
  - 用户上传的视频 (经授权后)
  - 教练标注的动作评分数据
  - 逐步提升模型精度

Phase 3: 持续学习 (Active Learning)
  - 模型低置信度预测 → 推送给教练标注 → 重新训练
  - 每周更新模型版本
  - A/B 测试新旧模型效果
```

---

## 十三、开发路线图

### Phase 1 — MVP (8-12 周)

```
Week 1-2: 基础设施搭建
├── 项目脚手架 (React Native + FastAPI)
├── CI/CD 流水线
├── PostgreSQL + Redis + MinIO 部署
└── 用户认证系统 (手机号 + 微信)

Week 3-4: 移动端核心页面
├── 注册/登录/个人信息
├── 视频上传 (TUS + 预处理)
├── Apple Health 授权读取
└── 分析任务状态页面 (WebSocket 进度)

Week 5-7: 视频分析引擎 MVP
├── 球场标定
├── MediaPipe 姿态估计集成
├── TrackNet V3 球追踪集成
├── 击球事件检测 + 分类
└── 技术特征提取

Week 8-9: 手表数据 + 评估引擎
├── OPPO / 华为健康数据适配
├── 体能特征提取
├── 多模态时间对齐
├── NTRP 等级推算逻辑
└── 三维度评估 (技术 + 体能 为主)

Week 10-11: RAG + 报告生成
├── NTRP 知识库入库 + Embedding
├── RAG 检索服务
├── LLM Prompt 调优
├── 报告渲染 (Markdown → 移动端富文本)
└── 训练计划生成

Week 12: 测试 + 内测发布
├── 端到端集成测试
├── 性能优化 (分析时间 < 8 分钟)
├── TestFlight / 内测 APK 发布
└── 收集早期用户反馈
```

### Phase 2 — 增强 (12-20 周)

```
├── 动作质量评分模型训练
├── 战术维度分析
├── 视频标注回放 (关键帧慢动作 + 参考对比)
├── 历史趋势对比
├── 训练打卡 + 进度追踪
├── 社区分享 (匿名报告卡片)
└── Android 手表直连支持
```

### Phase 3 — 进阶 (20-32 周)

```
├── 实时训练辅助 (AR 叠加动作引导)
├── 虚拟对练 (弱项针对性模拟)
├── 排行榜 + 等级认证徽章
├── 多语言支持 (英语/日语)
├── 教练端 (教练查看学员报告)
└── 赛事级别分析
```

---

## 十四、附录：NTRP 等级评估矩阵

基于手册内容整理的完整评估矩阵，用于 Agent 的评分计算。

### 14.1 技术模块 × 等级矩阵

| 技术模块 | 2.0 | 2.5 | 3.0 | 3.5 | 4.0 | 4.5 |
|----------|-----|-----|-----|-----|-----|-----|
| **正手** | 动作不完整，无方向控制 | 慢节奏可对拉 | 中速球稳定，缺深度 | 主动变线变节奏 | 全面可靠，深度/旋转/方向 | 力量+旋转结合，掌控节奏 |
| **反手** | 抗拒反手，无稳定性 | 握拍有问题，习惯侧身 | 可稳定回中速球 | 控制方向+落点 | 无短板，可主动进攻 | 与正手一体化 |
| **发球** | 动作不完整，频繁双误 | 动作趋于完整，抛球不稳 | 完整节奏，基础落点 | 主动控制落点+上旋 | 一发攻击力+旋转变化 | 精准落点，关键分稳定 |
| **接发** | 极易失误 | 可接慢速球 | 基础稳定性 | 控制方向，极少主动失误 | 针对弱点主动施压 | 完整接发体系 |
| **网前** | 无上网意识 | 仍有不适，反手截击差 | 正手截击稳定，反手薄弱 | 正手截击有深度，反手需加强 | 全面控制方向+深度 | 细腻全面，主动得分 |
| **脚步** | 基础分腿垫步 | 小碎步+交叉步 | 全场覆盖提升 | 前后场移动良好 | 流畅连贯，无死角 | 高效简洁，预判性强 |

### 14.2 体能指标 × 等级矩阵

| 指标 | 2.0-2.5 | 3.0 | 3.5 | 4.0 | 4.5 | 5.0 |
|------|---------|-----|-----|-----|-----|-----|
| 全场移动到位率 | — | ≥80% | ≥90% | ≥95% | ≥98% | ≥99% |
| 可持续对抗盘数 | <0.5 盘 | 1 盘 | 1 盘 | 3 盘 2 胜 | 多盘 | 职业级多盘 |
| 后半盘动作变形 | 明显 | 中等 | 轻微 | 几乎无 | 无 | 无 |
| 分间心率恢复 | — | 一般 | 良好 | 优秀 | 极佳 | 专业 |
| 启动爆发力 | — | 基础 | 中等 | 良好 | 优秀 | 专业 |

### 14.3 战术指标 × 等级矩阵

| 指标 | 2.0-2.5 | 3.0 | 3.5 | 4.0 | 4.5 |
|------|---------|-----|-----|-----|-----|
| 打法风格 | 无 | 无 | 开始形成 | 清晰 | 成熟体系 |
| 变线意识 | 无 | 偶尔 | 主动变线创造机会 | 熟练运用线路变化 | 多维变化掌控比赛 |
| 弱点针对 | 无 | 无 | 基础意识 | 能制定比赛计划 | 快速识别+实时调整 |
| 上网决策 | 无 | 基础 | 随球上网 | 战术上网 | 上网战术体系 |
| 关键分处理 | — | — | 一般 | 稳定 | 极稳定，极少失误 |
| 战术执行力 | — | — | 基础 | 坚定 | 极强 |

---

## 文档版本

| 版本 | 日期 | 变更 |
|------|------|------|
| v1.0 | 2026-06-15 | 初始完整技术设计文档 |

---

> **下一步**：当你准备好提供视频素材和手表数据样本后，我们可以进入 Phase 1 的开发——优先搭建视频分析流水线和健康数据接入层。
