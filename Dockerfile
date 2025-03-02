# 使用Python 3.12作为基础镜像
FROM python:3.12-slim

# 设置工作目录
WORKDIR /app

# 复制requirements.txt文件
COPY requirements.txt .

# 使用pip镜像并安装Python依赖
RUN pip config set global.index-url https://mirrors.tuna.tsinghua.edu.cn/pypi/web/simple \
    && pip install --no-cache-dir -r requirements.txt


# 设置时区为Asia/Shanghai
ENV TZ=Asia/Shanghai
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# 复制项目文件到工作目录
COPY . .

# 暴露端口8008
EXPOSE 8009

# 启动命令
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8009"]