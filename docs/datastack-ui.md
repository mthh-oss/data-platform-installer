# DataStack UI 落地说明

定位：**插件化大数据底座编排平台**（不是 CDH）。

## 主链路

登录 → 工作台 → 新建编排（4 步）→ 部署任务详情 → 实例管理 / 详情

## 路由

| 页面 | 路径 |
|------|------|
| 工作台 | `/workbench` |
| 组件编排 | `/orchestrate` |
| 部署任务 | `/tasks` `/tasks/:jobId` |
| 实例管理 | `/instances` `/instances/:id` |
| 主机资源池 | `/hosts` `/hosts/:hid` |
| 插件市场 | `/plugins` `/plugins/:pid` |
| 告警 / 日志 / 监控 | `/alerts` `/logs` `/monitor` |
| 系统管理 | `/admin/users` `/admin/audit` `/admin/settings` |

## 状态分离

- **部署任务**：排队 / 部署中 / 成功 / 失败 / 已取消（`utils/plugin.js` → `deployStatus`）
- **实例运行**：正常 / 告警 / 离线 / 停止（`instanceStatus`）

## 插件驱动

- 组件选择列表、角色分配、配置表单均读取 `/api/plugins` 的 schema / dependencies
- 实例详情为**通用模板**，禁止组件专属页面
- 插件市场为独立入口；禁用列表本地标记，编排 Step1 过滤

## 后端映射（过渡）

| 产品概念 | 现有 API |
|----------|----------|
| 实例 | `clusters` |
| 部署任务 | `jobs` |
| 插件 | `plugins` registry |
