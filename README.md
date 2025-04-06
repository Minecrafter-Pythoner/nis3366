# NIS3366WebDev
NIS3366课程项目：匿名聊天社区

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