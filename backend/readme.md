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
```
