# CDH 对标页面 × 本平台映射

组件保持：Doris / Flink / MySQL / Flink CDC / DolphinScheduler（不做 HDFS/YARN 全家桶）。

| 文档页面 | 本平台落地 | V1 |
|---------|-----------|----|
| P1 登录 | `/login` | ✅ |
| P2 忘记密码 | 二期 | ❌ |
| P3 集群选择 | `/clusters` | ✅ |
| P4 集群总览 | `/c/:id/overview` | ✅ |
| P5 服务管理 | `/c/:id/services` | ✅ |
| P6 服务详情 | `/c/:id/services/:sid` | ✅ 骨架 |
| P7 角色实例 | 服务详情 Tab | 骨架 |
| P8 主机管理 | `/c/:id/hosts` | ✅ |
| P9 主机详情 | `/c/:id/hosts/:hid` | 骨架 |
| P10 告警中心 | `/c/:id/alerts` | ✅ 骨架 |
| P11 日志检索 | `/c/:id/logs` | 骨架 |
| P12 版本包 | `/c/:id/parcels` | 骨架 |
| P13 客户端配置 | `/c/:id/client` | 骨架 |
| P14 任务中心 | `/c/:id/tasks` | ✅ |
| P15 配置中心 | `/c/:id/config` | 骨架 |
| P16 配置对比 | 二期 | ❌ |
| P17 资源队列 | 不适用（无 YARN） | ❌ |
| P18 用户权限 | `/admin/users` | ✅ 人员关系 |
| P19 审计日志 | `/admin/audit` | 骨架 |
| P20 平台设置 | `/admin/settings` | ✅ |

视觉：主色 `#165DFF`，状态色按文档规范。
