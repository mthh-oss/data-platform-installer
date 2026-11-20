# 自定义平台扩展口

把本目录复制为 `backend/plugins/<your_id>/`（目录名不要以 `_` 开头），并同步复制 `templates/_example_custom/` → `templates/<your_id>/`。

必须实现并导出：

```python
plugin = YourPlugin()  # subclass of PlatformPlugin
```

重启后端后访问 `GET /api/plugins` 即可看到新平台。
