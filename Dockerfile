# 使用官方Python基础镜像
FROM python:3.9-slim

# 设置工作目录
WORKDIR /app

# 复制项目文件到容器
COPY . .

# 安装Python依赖
RUN pip install -r requirements.txt

# 暴露 Flask 默认端口
EXPOSE 80

# 运行 Flask 应用
CMD ["python", "app.py"]
