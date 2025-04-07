# NIS3366WebDev
NIS3366课程项目：匿名聊天社区

## Quick Start

### Run in python env

先安装python所需依赖：
``` bash
pip install -r backend/requirements.txt
```

可选：编译前端（确保你已经安装了所需的依赖，若为安装可在`frontend`文件夹运行`npm install`）
``` bash
# for unix
bash build.sh
# for windows
./build.ps1
```

如不想编译前端，可直接使用已经编译完成的前端文件，位于`frontend/dist`文件夹下。

启动应用:
``` bash
python -m backend.main
```

### Run in docker

载入已经封装好的docker镜像：
``` bash
gzip -dk nis3366.tar.gz
docker load -i nis3366.tar
```

启动应用：
``` bash
docker run --name nis3366_test nis3366:latest /bin/bash /app/start_service.sh
```
