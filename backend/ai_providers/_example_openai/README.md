# 自定义 AI Provider 扩展口

复制本目录为 `backend/ai_providers/<your_id>/`（目录名不要以 `_` 开头），实现：

```python
from app.core.ai_base import AIProvider

class XxxProvider(AIProvider):
    id = "xxx"
    name = "XXX"
    def chat(self, messages, api_key, **kwargs):
        ...

provider = XxxProvider()
```

重启后端后即可在设置里选择。
