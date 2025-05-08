import cv2
import time
import os
from ultralytics import YOLO

model = YOLO("/opt/models/yolo/yolo11x.pt", verbose=False)  #


def detect_object_loss_time(
    video_path, target_label, target_box, tolerance_seconds=10.0
):
    """
    检测视频中指定物体丢失的时间点

    参数:
    video_path (str): 视频文件路径
    target_label (str): 目标物体的标签名称（如"cell phone", "handbag"等）
    target_box (list): 目标物体的初始边界框 [x1, y1, x2, y2]
    tolerance_seconds (float): 容错时间，物体必须连续消失超过这个时间才被视为丢失

    返回:
    float: 物体丢失的时间点（秒），如果物体未丢失则返回None
    """

    files = list_video_files(video_path)
    ans = {"file_name": "", "lost_time": 0}
    for file in files:
        file_name = os.path.join(video_path, file)
        lost_time = _detect_object_loss_time(
            file_name, target_label, target_box, tolerance_seconds
        )
        ans["file_name"] = file_name
        ans["lost_time"] = lost_time
        if lost_time > 0:
            return ans
    return None


def yolo_find_objects_by_video(
    video_dir,
    image_dir,
    object_name,
    min_confidence,
    draw_box: bool = False,
    callback = None,
    placeholder = None,
):
    """
    在视频中查找指定对象，并保存带有标记的帧图像
    参数:
    - callback: 识别过程中的回调函数
    - placeholder: 用于回调程序更新界面
    - video_dir: 视频目录
    - image_dir: 保存图像的目录
    - object_name: 要查找的对象名称
    - min_confidence: 最小置信度
    - draw_box: 是否在图像上绘制边界框
    返回: 检测到的内容
    """

    device = get_available_device
    identified_objects = []
    files = list_video_files(video_dir)
    if len(files) == 0:
        return None

     # print(output_dir, index)
    if not os.path.exists(image_dir):
        os.makedirs(image_dir)

    frame_index = 0
    file_index = 0
    for file in files:
        file_index += 1
        file_name = os.path.join(video_dir, file)
        video = cv2.VideoCapture(file_name)
        if not video.isOpened():
            print(f"无法打开视频文件: {file_name}")
            continue

        # 获取视频属性
        fps = video.get(cv2.CAP_PROP_FPS)

        while video.isOpened():
            ret, frame = video.read()
            if not ret:
                break

            # 每30帧处理一次（可以根据需要调整，提高效率）
            if frame_index % 30 != 0:
                frame_index += 1
                continue
            frame_index += 1

            results = model.predict(frame, device=device)
            time = frame_index_to_time(frame_index, fps)
            file_name = os.path.join(
                image_dir, f"{int(file_index):02}-{time}.jpg"
            )
            frame_info = _handle_predicted_results(
                time,
                results,
                object_name,
                min_confidence,
                callback,
                placeholder,
            )
            if frame_info:
                frame_items = {"file_name": file_name,
                               "frame": frame, 
                               "max_confidence": frame_info["max_confidence"], 
                               "max_box_id": frame_info["max_box_id"],
                               "results": frame_info["results"]}
                identified_objects.append(frame_items)
        video.release()
    return _save_identified_object_images(sorted(identified_objects, key=lambda x: x["file_name"], reverse=False))


def yolo_find_objects_by_images(
    callback,  # 识别过程中的回调
    placeholder,  # 用于回调程序更新界面
    image_dir,  # 图片目录
    object_name,  # 对象名称
    min_confidence,  # 置信率
    draw_box: bool = False,  # 是否在图片作标记
):
    identified_objects = []
    image_index = 0
    files = [
        f
        for f in os.listdir(image_dir)
        if os.path.isfile(os.path.join(image_dir, f))
        and f.endswith((".jpg", ".jpeg", ".png"))  # Check for video files
    ]
    total = len(files)
    suspectors = 0
    for file in files:
        box_index = 0
        file_name = os.path.join(image_dir, file)
        results = model.predict(file_name, device="mps")
        if draw_box:  # if don't need to draw picture, we don't need image.
            image = cv2.imread(file_name)

        file_yolo_info = {
            "image_index": image_index,
            "file_name": file_name,
            "boxes": [],
        }
        for result in results:
            boxes = result.boxes
            for box in boxes:
                box_index += 1
                cls_id = int(box.cls[0])
                label = model.names[cls_id]
                confidence = float("{:02f}".format(float(box.conf[0])))
                if (
                    label == object_name or object_name is None
                ) and confidence >= min_confidence:
                    box_info = {
                        "box_index": box_index,
                        # "video_index": dir,
                        "label": label,
                        "confidence": confidence,
                        "cls_id": cls_id,
                        "box": box,
                    }
                    file_yolo_info["boxes"].append(box_info)
                    suspectors += 1
                    identified_objects.append(file_yolo_info)
                    if not draw_box:
                        callback(
                            placeholder, image_index, total, suspectors, confidence
                        )
                if draw_box:
                    xyxy = box.xyxy[0].cpu().numpy()  # Bo
                    x1, y1, x2, y2 = map(int, xyxy)
                    cv2.rectangle(image, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    text = f"{box_index}-{label} {confidence:.2f}"
                    cv2.putText(
                        image,
                        text,
                        (x1, y1 - 10),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        1.5,
                        (0, 255, 0),
                        2,
                    )
        if draw_box:
            cv2.imwrite(file_name, image)

        if callback:
            callback(placeholder, file_name)

        image_index += 1
    return identified_objects


def _detect_object_loss_time(
    video_path, target_label, target_box, tolerance_seconds=10.0
):
    """
    检测视频中指定物体丢失的时间点

    参数:
    video_path (str): 视频文件路径
    target_label (str): 目标物体的标签名称（如"cell phone", "handbag"等）
    target_box (list): 目标物体的初始边界框 [x1, y1, x2, y2]
    tolerance_seconds (float): 容错时间，物体必须连续消失超过这个时间才被视为丢失

    返回:
    float: 物体丢失的时间点（秒），如果物体未丢失则返回None
    """

    # 打开视频文件
    video = cv2.VideoCapture(video_path)
    if not video.isOpened():
        print(f"无法打开视频文件: {video_path}")
        return None

    # 获取视频属性
    fps = video.get(cv2.CAP_PROP_FPS)
    total_frames = int(video.get(cv2.CAP_PROP_FRAME_COUNT))

    print(f"视频FPS: {fps}")
    print(f"总帧数: {total_frames}")

    # 计算容错帧数
    tolerance_frames = int(tolerance_seconds * fps)

    # 定义函数计算IoU (交并比)
    def calculate_iou(box1, box2):
        # 计算交集区域的坐标
        x1 = max(box1[0], box2[0])
        y1 = max(box1[1], box2[1])
        x2 = min(box1[2], box2[2])
        y2 = min(box1[3], box2[3])

        # 计算交集面积
        intersection = max(0, x2 - x1) * max(0, y2 - y1)

        # 计算两个框的面积
        box1_area = (box1[2] - box1[0]) * (box1[3] - box1[1])
        box2_area = (box2[2] - box2[0]) * (box2[3] - box2[1])

        # 计算并集面积
        union = box1_area + box2_area - intersection

        # 计算IoU
        if union == 0:
            return 0
        return intersection / union

    # 初始化变量
    object_detected = True
    missing_start_frame = None
    missing_count = 0
    lost_time = None

    # 设定IoU阈值，用于判断检测到的物体是否为目标物体
    iou_threshold = 0.3

    # 开始处理视频
    frame_idx = 0
    while video.isOpened():
        ret, frame = video.read()
        if not ret:
            break

        # 每30帧处理一次（可以根据需要调整，提高效率）
        if frame_idx % 30 == 0:
            # 使用YOLO进行物体检测
            results = model(frame)

            # 查找匹配的物体
            object_found = False
            for r in results:
                boxes = r.boxes
                for box in boxes:
                    # 获取预测的类别
                    cls = int(box.cls[0])
                    label = model.names[cls]

                    # 如果标签匹配
                    if label == target_label:
                        # 获取预测的边界框
                        detected_box = (
                            box.xyxy[0].cpu().numpy()
                        )  # 转换为 [x1, y1, x2, y2] 格式

                        # 计算IoU
                        iou = calculate_iou(target_box, detected_box)

                        # 如果IoU大于阈值，认为是目标物体
                        if iou > iou_threshold:
                            object_found = True
                            break

                if object_found:
                    break

            # 检查物体是否消失
            if not object_found:
                if object_detected:  # 物体刚开始消失
                    missing_start_frame = frame_idx
                    object_detected = False

                missing_count = frame_idx - missing_start_frame

                # 检查是否超过容错时间
                if missing_count >= tolerance_frames:
                    lost_time = missing_start_frame / fps
                    print(f"物体在视频 {lost_time:.2f} 秒处丢失")
                    # 可以选择在这里退出循环或继续检测
                    break
            else:
                # 物体重新出现
                if not object_detected:
                    object_detected = True
                    missing_count = 0
                    # 如果在容错时间内物体重新出现，重置丢失时间
                    if (
                        lost_time is not None
                        and (frame_idx / fps - lost_time) <= tolerance_seconds
                    ):
                        print(
                            f"物体在视频 {frame_idx / fps:.2f} 秒处重新出现，不视为丢失"
                        )
                        lost_time = None

        frame_idx += 1

        # 显示进度
        if frame_idx % 100 == 0:
            print(
                f"处理进度: {frame_idx}/{total_frames} 帧 ({frame_idx/total_frames*100:.1f}%)"
            )

    # 释放视频资源
    video.release()

    return lost_time


def _get_max_confidence_image(identified_objects):
    filted_images = []

    max_confidence_image = None
    prev_second = 0
    prev_confidence = 0
    for identified_object in identified_objects:
        file_name = identified_object["file_name"]
        confidence = identified_object["max_confidence"]
        second = int(file_name.split(".")[0].split("-")[-1])
        next_second = prev_second + 1
        if next_second == 60:
            next_second = 0

        if next_second == second:
            if prev_confidence < confidence:
                prev_confidence = confidence
                max_confidence_image = identified_object
            prev_second += 1
        else:
            prev_second = second
            prev_confidence = confidence
            if max_confidence_image is not None:
                filted_images.append(max_confidence_image)
            max_confidence_image = identified_object
    filted_images.append(max_confidence_image)
    return filted_images

def _save_identified_object_images(identified_objects : list):
    """
    保存识别的对象到图像
    参数:
    - image: 图像
    - file_name: 文件名
    - identified_objects: 识别的对象列表
    """

    max_confidence_images = _get_max_confidence_image(identified_objects)
    if len(max_confidence_images) == 0:
        print("没有识别到对象")
        return None

    for identified_object in max_confidence_images:
        image = identified_object["frame"]
        if image is None:
            continue

        file_name = identified_object["file_name"]
        results = identified_object["results"]
        for result in results:
            box_id = result["box_id"]
            label = result["label"]
            confidence = result["confidence"]
            box = result['box']
            # print(f"> {label}: {confidence:.2f}")
            xyxy = box.xyxy[0].cpu().numpy()
        
            x1, y1, x2, y2 = map(int, xyxy)
            cv2.rectangle(image, (x1, y1), (x2, y2), (0, 255, 0), 2)
            text = f"{box_id}-{label} {confidence:.2f}"
            cv2.putText(
                image,
                text,
                (x1, y1 - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                1.5,
                (0, 255, 0),
                2,
            )
        cv2.imwrite(file_name, image)


def _handle_predicted_results(
    time, # 图片文件名
    results, # 识别结果
    object_name, # 物体名称 
    min_confidence, # 置信率
    callback=None, # 回调函数
    placeholder=None, # 占位符
):
    identified_boxes = []
    box_id = 0
    max_confidence = 0
    max_box_id = 0
    for result in results:
        boxes = result.boxes
        for box in boxes:
            cls_id = int(box.cls[0])
            label = model.names[cls_id]
            confidence = float("{:02f}".format(float(box.conf[0])))
            # print(f"> {label}: {confidence:.2f}")
            if label == object_name and confidence >= min_confidence:
                if confidence > max_confidence:
                    max_confidence = confidence
                    max_box_id = box_id
                box_id += 1
                box_info = {
                    "box_id": box_id,
                    "label": label,
                    "confidence": confidence,
                    "cls_id": cls_id,
                    "box": box,
                }
                identified_boxes.append(box_info)
        if callback:
            callback(placeholder, time, confidence)
    if max_confidence > 0:
        return {"max_confidence": max_confidence, "lable": label, "max_box_id": max_box_id, "results": identified_boxes}
    
    return None



def frame_index_to_time(frame_index, fps):
    seconds = frame_index / fps
    minutes = seconds // 60
    seconds = seconds % 60
    hours = minutes // 60
    minutes = minutes % 60  
    return f"{int(hours):02}-{int(minutes):02}-{int(seconds):02}"

def list_video_files(path):
    return [
        f
        for f in os.listdir(path)
        if os.path.isfile(os.path.join(path, f))
        and f.endswith((".mp4", ".avi", ".mov"))  # Check for video files
    ]

def find_object_callback(index, total, file_name, confidence):
    text = f"{index}/{total},{confidence}->{file_name}"
    print(text)

import torch
import platform

def get_available_device():
    """
    检测并返回可用的最佳计算设备 (MPS, CUDA, 或 CPU).
    优先顺序: MPS (在 macOS上), CUDA, CPU.
    """
    # 检查 Apple Silicon (MPS)
    if platform.system() == "Darwin": # macOS
        if torch.backends.mps.is_available():
            print("MPS (Apple Silicon GPU) 可用。")
            # 还可以检查 MPS 是否真的能工作 (某些旧 macOS 版本或 PyTorch 版本可能有问题)
            try:
                # 创建一个简单的张量并移至 mps 设备以验证
                _ = torch.tensor([1.0, 2.0]).to("mps")
                print("MPS 功能正常。将使用 'mps' 设备。")
                return "mps"
            except Exception as e:
                print(f"MPS 可用但测试失败: {e}。将回退到 CPU。")
                # 如果 MPS 测试失败，通常回退到 CPU，因为 CUDA 在 Mac 上不被原生支持
        else:
            print("MPS 不可用。")
    
    # 检查 NVIDIA CUDA
    if torch.cuda.is_available():
        print("CUDA (NVIDIA GPU) 可用。")
        cuda_device_count = torch.cuda.device_count()
        print(f"找到 {cuda_device_count} 个 CUDA 设备。")
        if cuda_device_count > 0:
            # 获取第一个 CUDA 设备的名称
            cuda_device_name = torch.cuda.get_device_name(0)
            print(f"将使用 CUDA 设备 0: {cuda_device_name}")
            return "cuda" # 或者 "cuda:0"
    else:
        print("CUDA 不可用。")
        
    print("MPS 和 CUDA 均不可用。将使用 'cpu' 设备。")
    return "cpu"


if __name__ == "__main__":
    start_time = time.time()
    video_dir = "/var/tmp/smart-vision/video/72f968fc-2483-45a9-9e14-929267e85ceb"
    image_dir = "/var/tmp/smart-vision/image/72f968fc-2483-45a9-9e14-929267e85ceb"
    yolo_find_objects_by_video(video_dir, image_dir, 'dog', 0.1, draw_box=True)
    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f"Elapsed time: {elapsed_time:.2f} seconds")  
