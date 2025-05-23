FROM python:3.10-slim

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    # 图形界面支持
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    # 图像编解码库
    libjpeg-dev \
    libpng-dev \
    libtiff-dev \
    libopenexr-dev \
    # 视频处理库
    libavcodec-dev \
    libavformat-dev \
    libswscale-dev \
    libgstreamer1.0-0 \
    libgstreamer-plugins-base1.0-0 \
    # 清理缓存以减小镜像体积
    && rm -rf /var/lib/apt/lists/*

# 创建非 root 用户
RUN  mkdir /app 

WORKDIR /app

# 安装 Poetry 并禁用虚拟环境
ENV POETRY_VERSION=2.0.0
ENV PATH="/home/appuser/.local/bin:$PATH"
RUN pip install "poetry==$POETRY_VERSION" \
    && poetry config virtualenvs.create false

# 复制依赖文件
COPY pyproject.toml poetry.lock ./

# 安装应用依赖
RUN poetry install --no-root --only main

# 复制应用代码
COPY . .

EXPOSE 8501
CMD ["streamlit", "run", "smartvision/app.py", "--server.port=8501", "--server.address=0.0.0.0"]
