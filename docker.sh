#!/bin/sh

# 定义目标容器和镜像名称
# 这确保所有操作都特定于此应用程序
CONTAINER_NAME="smart-vision-portal"
IMAGE_NAME="smart-vision-portal" # 默认情况下，这将转换为 image:tag as smart-vision-portal:latest

# --- 辅助函数 ---
# 检查特定容器是否存在的函数
container_exists() {
    docker container inspect "${CONTAINER_NAME}" > /dev/null 2>&1
}

# 检查特定容器是否正在运行的函数
container_is_running() {
    # 使用精确的名称过滤，^/确保从名称开头匹配，以防名称中包含其他字符
    docker ps --filter "name=^/${CONTAINER_NAME}$" --filter "status=running" --format "{{.Names}}" | grep -q "^${CONTAINER_NAME}$"
}

# 检查特定镜像是否存在的函数
image_exists() {
    docker image inspect "${IMAGE_NAME}" > /dev/null 2>&1 # 默认检查 IMAGE_NAME:latest
}

# 显示使用信息
usage() {
    echo "Usage: $0 [command]"
    echo "Manages the Docker lifecycle for the Smart Vision Portal."
    echo ""
    echo "Commands:"
    echo "  build    - Build or rebuild the ${IMAGE_NAME} Docker image."
    echo "             Stops and removes existing container and image before building."
    echo "  run      - Run a new ${CONTAINER_NAME} container or restart an existing one."
    echo "             Requires the image to be built first."
    echo "  stop     - Stop the ${CONTAINER_NAME} container if it is running."
    echo "  start    - Start the existing ${CONTAINER_NAME} container if it is stopped."
    echo "  rm       - Remove the ${CONTAINER_NAME} container."
    echo "             Stops the container first if it is running."
    echo "  logs     - Follow the logs of the ${CONTAINER_NAME} container."
    echo "  purge    - Stop and remove the ${CONTAINER_NAME} container and then remove the ${IMAGE_NAME} image."
    echo "  help|-h  - Show this help message."
    echo ""
    echo "All operations are targeted specifically at resources named '${CONTAINER_NAME}' and '${IMAGE_NAME}'."
}

# --- 主脚本逻辑 ---
# 如果未提供参数或请求帮助，则显示用法
if [ $# -eq 0 ] || [ "$1" = "help" ] || [ "$1" = "-h" ]; then
    usage
    exit 0
fi

COMMAND="$1"

case "$COMMAND" in
    build)
        echo "--- Building image ${IMAGE_NAME} ---"
        # 如果容器存在，尝试停止并移除它
        if container_exists; then
            echo "Found existing container '${CONTAINER_NAME}'. Attempting to stop and remove it."
            docker stop "${CONTAINER_NAME}" || echo "Container '${CONTAINER_NAME}' was not running or already stopped."
            docker rm "${CONTAINER_NAME}" || echo "Container '${CONTAINER_NAME}' was not found or already removed."
        fi

        # 如果镜像存在，尝试移除它以确保全新构建
        if image_exists; then
             echo "Found existing image '${IMAGE_NAME}'. Attempting to remove it."
             docker rmi "${IMAGE_NAME}" || echo "Image '${IMAGE_NAME}' could not be removed (perhaps it's in use by other containers not managed by this script, or has multiple tags)."
        fi

        echo "Building new image '${IMAGE_NAME}' from Dockerfile in current directory..."
        docker build -t "${IMAGE_NAME}" .
        if [ $? -eq 0 ]; then
            echo "Image '${IMAGE_NAME}' built successfully."
        else
            echo "Error: Image build for '${IMAGE_NAME}' failed."
            exit 1
        fi
        ;;

    run)
        echo "--- Running or restarting container ${CONTAINER_NAME} ---"
        if ! image_exists; then
            echo "Error: Image '${IMAGE_NAME}' not found. Please build it first using: $0 build"
            exit 1
        fi

        if container_is_running; then
            echo "Container '${CONTAINER_NAME}' is already running. Restarting it..."
            docker restart "${CONTAINER_NAME}"
        elif container_exists; then
            echo "Container '${CONTAINER_NAME}' exists but is stopped. Starting it..."
            docker start "${CONTAINER_NAME}"
        else
            echo "Container '${CONTAINER_NAME}' does not exist. Creating and starting new container..."
            # 来自原始脚本的通用 Docker run 选项
            # 确保 /opt/bash/env 存在或处理其缺失情况
            ENV_FILE="/opt/bash/env"
            DOCKER_RUN_OPTS="-it --name ${CONTAINER_NAME}" # 在此处添加 --name
            # 注意: 原始脚本对卷的主机端使用相对路径 ./ ，可能需要根据脚本运行位置进行调整。
            # 假设 ./ 指的是 docker build 的上下文。
            DOCKER_RUN_OPTS="${DOCKER_RUN_OPTS} -v /app:/Users/tju/Workspace/Projects/ongoing/SmartVision/portal"
            DOCKER_RUN_OPTS="${DOCKER_RUN_OPTS} -v /var/tmp/smart-vision:/var/tmp/smart-vision"
            DOCKER_RUN_OPTS="${DOCKER_RUN_OPTS} -v /opt/models/yolo:/opt/models/yolo"
            DOCKER_RUN_OPTS="${DOCKER_RUN_OPTS} -p 8501:8501"

            if [ -f "${ENV_FILE}" ]; then
                DOCKER_RUN_OPTS="${DOCKER_RUN_OPTS} --env-file ${ENV_FILE}"
            else
                echo "Warning: Environment file ${ENV_FILE} not found. Proceeding without it."
            fi

            # 根据操作系统选择 GPU 选项 (基于原始脚本逻辑)
            if [ "$(uname)" = "Linux" ]; then
                # 更稳健地检查 NVIDIA GPU 是否存在 (如果可能)
                if command -v nvidia-smi &> /dev/null; then # 对 nvidia-smi 的基本检查
                    echo "NVIDIA GPU detected (via nvidia-smi). Adding --gpus option."
                    # 为第一个 GPU 使用标准的 'device=0' 语法。
                    # 原始脚本使用 '"device=0"'，这可能有问题。
                    # 使用 'all' 表示所有可用 GPU: --gpus all
                    DOCKER_RUN_OPTS="${DOCKER_RUN_OPTS} --gpus device=0"
                else
                    echo "nvidia-smi not found. Running without --gpus option. If you have an NVIDIA GPU, ensure drivers and nvidia-container-toolkit are installed."
                fi
                docker run ${DOCKER_RUN_OPTS} "${IMAGE_NAME}"
            else
                # 对于非 Linux 系统 (例如 macOS, Windows with Docker Desktop), GPU 支持通常配置不同。
                echo "Running on non-Linux system ($(uname)). GPU support via --gpus flag might not apply or is handled by Docker Desktop settings."
                docker run ${DOCKER_RUN_OPTS} "${IMAGE_NAME}"
            fi
        fi

        if [ $? -eq 0 ]; then
            echo "Container '${CONTAINER_NAME}' should be up and running. Check with 'docker ps'."
        else
            echo "Error: Failed to run/start container '${CONTAINER_NAME}'."
            # 如果可能，提供更多信息，例如，如果容器已创建但未能启动，则提供 docker logs ${CONTAINER_NAME}
            exit 1
        fi
        ;;

    start) # 新命令
        echo "--- Starting container ${CONTAINER_NAME} ---"
        if ! container_exists; then
            echo "Error: Container '${CONTAINER_NAME}' does not exist. Use '$0 run' to create and run it."
            exit 1
        fi
        if container_is_running; then
            echo "Container '${CONTAINER_NAME}' is already running."
        else
            echo "Starting container '${CONTAINER_NAME}'..."
            docker start "${CONTAINER_NAME}"
            if [ $? -eq 0 ]; then
                echo "Container '${CONTAINER_NAME}' started."
            else
                echo "Error: Failed to start container '${CONTAINER_NAME}'."
                exit 1
            fi
        fi
        ;;

    stop)
        echo "--- Stopping container ${CONTAINER_NAME} ---"
        if container_is_running; then
            echo "Stopping container '${CONTAINER_NAME}'..."
            docker stop "${CONTAINER_NAME}"
            echo "Container '${CONTAINER_NAME}' stopped."
        elif container_exists; then
            echo "Container '${CONTAINER_NAME}' exists but is not running."
        else
            echo "Container '${CONTAINER_NAME}' not found."
        fi
        ;;

    rm)
        echo "--- Removing container ${CONTAINER_NAME} ---"
        if container_exists; then
            if container_is_running; then
                echo "Container '${CONTAINER_NAME}' is running. Stopping it first..."
                docker stop "${CONTAINER_NAME}"
            fi
            echo "Removing container '${CONTAINER_NAME}'..."
            docker rm "${CONTAINER_NAME}"
            echo "Container '${CONTAINER_NAME}' removed."
        else
            echo "Container '${CONTAINER_NAME}' not found."
        fi
        ;;

    logs)
        echo "--- Following logs for ${CONTAINER_NAME} ---"
        if ! container_exists; then # 检查容器是否根本不存在
             echo "Error: Container '${CONTAINER_NAME}' does not exist. Cannot show logs."
             exit 1
        fi
        echo "Press Ctrl+C to stop following logs."
        docker logs -f "${CONTAINER_NAME}"
        ;;

    purge)
        echo "--- Purging container ${CONTAINER_NAME} and image ${IMAGE_NAME} ---"
        # 停止并移除容器
        if container_exists; then
            echo "Stopping container '${CONTAINER_NAME}' (if running)..."
            docker stop "${CONTAINER_NAME}" || true # 如果已停止，允许继续
            echo "Removing container '${CONTAINER_NAME}'..."
            docker rm "${CONTAINER_NAME}" || true   # 如果已移除，允许继续
        else
            echo "Container '${CONTAINER_NAME}' not found, no need to stop or remove."
        fi

        # 移除镜像
        if image_exists; then
            echo "Removing image '${IMAGE_NAME}'..."
            docker rmi "${IMAGE_NAME}"
            if [ $? -eq 0 ]; then
                echo "Image '${IMAGE_NAME}' removed successfully."
            else
                echo "Warning: Image '${IMAGE_NAME}' could not be removed. It might be tagged multiple times or used by other containers."
            fi
        else
            echo "Image '${IMAGE_NAME}' not found, no need to remove."
        fi
        echo "Purge complete."
        ;;

    *)
        echo "Error: Unknown command '$COMMAND'"
        usage
        exit 1
        ;;
esac

exit 0
