## 文件结构

```txt
├── chat
│   └── chat.py
├── topic
│   └── topic.py
├── login
│   └── login.py
├── main.py
└── readme.md
```

每个板块建立对于的文件夹，并在其中建立同名的py文件作为该模块的fastapi子应用。
在main.py中引入子应用，并添加路由。

## 运行

```bash
# make sure you in the root dir of this repo
python -m backend.main
```

## 测试

```bash
# make sure you in the root dir of this repo
python -m backend.topic.unittest
python -m backend.chat.unittest
```
## 不良消息过滤模块
backend/
  └── filter/
      ├── __init__.py
      ├── filter.py         # FastAPI子应用
      ├── models.py         # 数据模型
      ├── prompt_engine.py  # 基于提示工程的过滤引擎
      ├── processor.py      # 文本预处理与关键词过滤
      ├── keyword_lists/    # 关键词过滤列表
      │   ├── abuse.txt     # 辱骂词
      │   ├── adult.txt     # 成人内容
      │   └── sensitive.txt # 敏感内容
      └── config.py         # 配置文件
过滤流程说明
用户发送消息
消息先经过关键词过滤（快速检查）
如果关键词过滤通过，再使用ChatGLM模型基于提示工程进行深入分析
若判定内容不合规，则返回错误并告知用户
若判定内容合规，则允许发布