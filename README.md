# Data Platform Installer

轻量 FineBI/CDH 风格控制台：多用户权限隔离、主机库存选 FE/BE、一键下载启动、集群总览、异常日志下载、设置中心、右下角可收缩 AI 助手。

- Apache Doris
- Apache Flink
- MySQL
- Flink CDC（侧车 + SQL 骨架）
- Apache DolphinScheduler

并预留自定义平台扩展口（插件目录扫描）。

## 环境要求

- Windows / macOS / Linux
- Python 3.11+（已在 3.14 验证可安装依赖；若 pip 需编译失败，请改用 3.11/3.12）
- Node.js 18+
- Docker Desktop（或等价 Docker Engine + Compose v2），且 `docker` 在 PATH 中
  - 控制面可在无 Docker 时启动；真正 `compose up` 需要本机 Docker

## 快速启动（一键脚本）

### Linux 服务器

```bash
cd data-platform-installer
chmod +x bin/*.sh
./bin/start.sh      # 推荐：启动 API:8000 + Web:5173
# 或：bash bin/start.sh
# 不要用 dash 的纯 sh 特性来理解脚本；若写成 sh bin/start.sh 也会自动转 bash
./bin/status.sh     # 查看状态
./bin/stop.sh       # 停止
```

日志目录：`logs/api.log`、`logs/web.log`

### Windows

```powershell
cd data-platform-installer
.\bin\start.ps1
```

### 手动启动（可选）

后端：

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

前端：

```bash
cd frontend
npm install
npm run dev -- --host 0.0.0.0 --port 5173
```

健康检查：<http://127.0.0.1:8000/api/health>  
页面：<http://127.0.0.1:5173>

### 3. 首次登录

1. 打开页面，首次进入会要求 **初始化主账号**
2. 密码规则：至少 8 位、需含字母、**不能全是数字**
3. 之后运维使用该账号登录

### 4. 最小验证路径（MySQL + Flink）

1. 打开「一键启动」
2. 勾选 **MySQL**、**Apache Flink**（有依赖的组件会自动带上依赖）
3. 填写端口/密码等配置（避开已占用端口，如 8081）
4. 点击 **一键下载并启动**
5. 在「下载/启动进度」看进度；失败可下载任务日志
6. 「集群总览」看组件拓扑；可下载异常日志 ZIP
7. 「AI 自检」配置 DeepSeek API Key 后可自动分析问题

### 5. 扩展其他 AI

复制 `backend/ai_providers/_example_openai/` 为新目录（不要 `_` 前缀），实现 `AIProvider` 并导出 `provider`，重启后端即可。

也可在后端已启动时跑：

```powershell
.\scripts\smoke_api.ps1
```

若本机无 Docker，任务会在渲染/合并 compose 后失败，并在日志中提示安装 Docker——这是预期行为。

Prometheus 指标：<http://127.0.0.1:8000/metrics>


## 架构要点

- 控制面：FastAPI + SQLite
- 部署引擎：本机 `docker compose`
- 插件：`backend/plugins/<id>/plugin.py` 导出 `plugin = XxxPlugin()`
- 模板：`templates/<id>/*.j2`（Jinja2）
- 工作区：`workspaces/dpi-<cluster>/`

## 如何扩展其他平台

1. 复制 `backend/plugins/_example_custom/` → `backend/plugins/my_platform/`
2. 复制 `templates/_example_custom/` → `templates/my_platform/`
3. 修改 `plugin.id / name / schema / render / health_checks`
4. **目录名不要以 `_` 开头**（`_` 前缀表示禁用/样例）
5. 重启后端，在向导中即可看到新平台

## API

| Method | Path | 说明 |
|--------|------|------|
| GET | `/api/plugins` | 已注册插件与表单 schema |
| POST | `/api/clusters` | 创建集群配置 |
| POST | `/api/clusters/{id}/deploy` | 触发部署 |
| POST | `/api/clusters/{id}/stop` | 停止 |
| POST | `/api/clusters/{id}/restart` | 重启 |
| GET | `/api/clusters/{id}/health` | 健康聚合 |
| GET | `/api/jobs/{id}` | 任务状态 |
| GET | `/api/jobs/{id}/logs` | 任务日志 |
| GET | `/metrics` | Prometheus |

## 注意

- 本仓库为 **演示/开发规模** Compose，非生产高可用。
- Doris / DolphinScheduler 镜像较大，内存不足时任务会失败，但日志可在任务页查看。
- Flink CDC 插件提供侧车与 SQL 骨架；正式跑 CDC 还需自行放入 connector JAR。
