# Data Platform Installer

页面挑选组件并填写配置后，**一键下载镜像并启动**，通过 Docker Compose 搭建并监控：

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

## 快速启动

### 1. 后端

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

健康检查：<http://127.0.0.1:8000/api/health>

### 2. 前端

```powershell
cd frontend
npm install
npm run dev
```

打开：<http://127.0.0.1:5173>

### 3. 最小验证路径（MySQL + Flink）

1. 打开「一键启动」
2. 勾选 **MySQL**、**Apache Flink**（有依赖的组件会自动带上依赖）
3. 填写端口/密码等配置
4. 点击 **一键下载并启动**
5. 在「下载/启动进度」看：准备配置 → 下载镜像 → 启动组件 → 就绪
6. 到「监控看板」查看 health（首次拉镜像可能较久）

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
