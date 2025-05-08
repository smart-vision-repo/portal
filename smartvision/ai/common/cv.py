import cv2
import os
from ultralytics import YOLO
from common.utils import list_video_files


def cv_clip_video(file_name, start_time, end_time, output_path):
    """
    Clips a video file from a specified start time to end time and saves the result using H.264 codec.

    Args:
        file_name (str): Path to the input video file.
        start_time (float): Start time for the clip in seconds.
        end_time (float): End time for the clip in seconds.
        output_path (str): Directory where the clipped video will be saved.

    Returns:
        bool: True if clipping was successful, False otherwise.

    Notes:
        - This function uses OpenCV for video processing. GPU usage depends on the
          OpenCV build configuration and system hardware support for decoding/encoding.
        - The output video is encoded using H.264 (via 'avc1' FourCC). Ensure necessary codecs are installed.
        - If end_time exceeds the video duration, the clip will extend to the end
          of the video.
        - If start_time exceeds the video duration, the function returns False.
        - The output video will have the same filename as the input, saved in output_path.
        - Ensures the output directory exists.
    """
    # Check if input file exists
    if not os.path.isfile(file_name):
        print(f"Error: Input video file not found: {file_name}")
        return False

    # Open the video file
    cap = cv2.VideoCapture(file_name)
    if not cap.isOpened():
        print(f"Error: Could not open video file: {file_name}")
        return False

    # Get video properties
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    # Handle cases where FPS or total_frames might be invalid
    if fps <= 0 or total_frames <= 0:
        print(
            f"Error: Invalid video properties (FPS: {fps}, Frames: {total_frames}) for file: {file_name}"
        )
        cap.release()
        return False

    duration = total_frames / fps

    # Validate start_time
    if start_time >= duration:
        print(
            f"Error: Start time ({start_time:.2f}s) is beyond video duration ({duration:.2f}s)."
        )
        cap.release()
        return False

    # Adjust end_time if it exceeds duration
    if end_time > duration:
        print(
            f"Warning: End time ({end_time:.2f}s) exceeds video duration ({duration:.2f}s). Clipping to the end."
        )
        end_time = duration

    # Ensure end_time is not before start_time
    if end_time <= start_time:
        print(
            f"Error: End time ({end_time:.2f}s) must be after start time ({start_time:.2f}s)."
        )
        cap.release()
        return False

    # Calculate start and end frame indices
    start_frame = int(start_time * fps)
    end_frame = int(end_time * fps)

    # Ensure frame indices are within valid range
    start_frame = max(0, start_frame)
    end_frame = min(total_frames - 1, end_frame)  # Frame indices are 0-based

    # Prepare output path
    base_name = os.path.basename(file_name)
    # Ensure output file has .mp4 extension if using H.264 in MP4 container
    output_file_name = os.path.splitext(base_name)[0] + ".mp4"
    output_file = os.path.join(output_path, output_file_name)
    os.makedirs(
        output_path, exist_ok=True
    )  # Create output directory if it doesn't exist

    # Define the codec and create VideoWriter object
    # Use 'avc1' for H.264 encoding in an MP4 container.
    # Alternatives might be 'H264', 'h264', 'X264' depending on system codecs.
    fourcc = cv2.VideoWriter_fourcc(*"avc1")
    out = cv2.VideoWriter(output_file, fourcc, fps, (frame_width, frame_height))

    if not out.isOpened():
        print(
            f"Error: Could not open VideoWriter for output file: {output_file}. Check if H.264 ('avc1') codec is supported/installed."
        )
        cap.release()
        # Try falling back to mp4v if avc1 fails? Or just report error. Reporting is safer.
        return False

    # Set the starting frame position
    # Note: Setting frame position might not be perfectly accurate for all video formats.
    cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)

    current_frame_index = start_frame
    frames_written = 0

    print(
        f"Clipping video '{base_name}' from frame {start_frame} to {end_frame} (Output: {output_file_name})..."
    )

    # Read frames from start_frame to end_frame and write to output
    while current_frame_index <= end_frame:
        ret, frame = cap.read()
        if not ret:
            # If read fails before reaching end_frame, it might be due to inaccurate frame count or read error
            print(
                f"Warning: Could not read frame at index {current_frame_index} (expected end: {end_frame}). Stopping clip."
            )
            break

        out.write(frame)
        frames_written += 1
        current_frame_index += 1

        # Optional: Add progress indicator if needed
        # if current_frame_index % int(fps) == 0: # Print progress every second
        #     print(f"  Processed frame {current_frame_index}/{end_frame}")

    # Release everything when job is finished
    cap.release()
    out.release()

    if frames_written > 0:
        print(
            f"Successfully clipped video and saved to {output_file} ({frames_written} frames written)."
        )
        return True
    else:
        print(f"Error: No frames were written to the output file: {output_file}")
        # Clean up empty file if created
        if os.path.exists(output_file) and os.path.getsize(output_file) == 0:
            try:
                os.remove(output_file)
                print(f"Removed empty output file: {output_file}")
            except OSError as e:
                print(f"Error removing empty output file {output_file}: {e}")
        return False


def cv_video_info(video_path):
    """
    Get video information such as duration, frame rate, and total frames.
    """

    if not os.path.exists(video_path):
        raise ValueError(f"Video file does not exist: {video_path}")

    files = list_video_files(video_path)

    videos = []

    for file in files:
        file_name = os.path.join(video_path, file)
        video = cv2.VideoCapture(file_name)
        if not video.isOpened():
            raise ValueError(f"Could not open video file: {video_path}")

        fps = video.get(cv2.CAP_PROP_FPS)
        total_frames = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = total_frames / fps
        resolution = f"{video.get(cv2.CAP_PROP_FRAME_WIDTH)}, {video.get(cv2.CAP_PROP_FRAME_HEIGHT)}"

        video.release()

        item = {
            "file": file,
            "fps": fps,
            "total_frames": total_frames,
            "duration": int(duration),
            "resolution": resolution,
        }
        videos.append(item)
    return videos


def cv_extract_frames(
    on_extracting, # 提取进度回调函数
    placeholder, # 占位符
    video_path, # 视频文件目录
    output_dir, # 提取的图像存放目录
    start_time, # 提取的起始时间
    duration, # 提取的持续时间
    frames_per_second, # 每秒提取的帧数
    max=0, # 最多提取的图像数量
):
    # Create the output directory if it doesn't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    files = [
        f
        for f in os.listdir(video_path)
        if os.path.isfile(os.path.join(video_path, f))
        and f.endswith((".mp4", ".avi", ".mov"))  # Check for video files
    ]
    if not files:
        print(f">>>>>>>>> No video files found in {video_path}")
        return

    total_images = []

    files = sorted(files)
    index = 1
    for file_name in files:
        video_info = {}
        # print(output_dir, index)
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        full_video_path = os.path.join(video_path, file_name)
        # Open the video file
        video = cv2.VideoCapture(full_video_path)

        # Get the video's frame rate and total number of frames
        fps = video.get(cv2.CAP_PROP_FPS)
        if fps == 0:
            print("fps is zero.")
            continue

        # Get the video's frame rate and total number of frames
        total_frames = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
        video_duration = total_frames / fps
        video_info["duration"] = video_duration

        # Validate start_time
        if start_time > video_duration:
            raise ValueError("Start time cannot be greater than the video duration.")

        # Calculate the end time
        end_time = video_duration
        if duration > 0:
            end_time = min(start_time + duration, video_duration)

        # Calculate the start and end frame numbers
        start_frame = int(start_time * fps)
        end_frame = int(end_time * fps)

        # Set the current frame to the start frame
        video.set(cv2.CAP_PROP_POS_FRAMES, start_frame)

        # Initialize the frame count and image counter
        frame_count = 0
        image_index = 1
        total = int(total_frames / 30 * frames_per_second)
        frame_interval = (
            fps / frames_per_second if frames_per_second > 0 else float("inf")
        )
        next_frame_to_extract = 0

        video_summary = []
        # Loop through the frames
        while frame_count <= (end_frame - start_frame):
            # Read the next frame
            ret, frame = video.read()

            # If the frame was not read successfully, break out of the loop
            if not ret:
                break

            # Calculate the time of the current frame
            current_time = start_time + frame_count / fps

            # Check if it's time to extract a frame
            if frame_count >= next_frame_to_extract:
                # Save the frame as an image
                hours = int(current_time // 3600)
                minutes = int((current_time % 3600) // 60)
                seconds = int(current_time % 60)

                # Generate the image filename
                frame_number_in_second = int(frame_count % fps * frames_per_second) + 1
                image_filename = "{:02d}-{:02d}-{:02d}-{:02d}-{:02d}-{:05d}.jpg".format(
                    index, hours, minutes, seconds, frame_number_in_second, image_index
                )
                image_path = os.path.join(output_dir, image_filename)

                # Save the image
                cv2.imwrite(image_path, frame)

                if max > 0 and image_index == max:
                    break

                total_images.append(image_index)
                # Update the next frame to extract
                next_frame_to_extract += frame_interval

                if on_extracting:
                    on_extracting(placeholder, image_index, total)

                image_index += 1
                # Increment the frame count
            frame_count += 1
        video_info["image_count"] = image_index
        # Release the video file
        video.release()
        video_summary.append(video_info)
        index += 1

    return video_summary


def extract_frames_finished(frame_counts):
    print(frame_counts)


if __name__ == "__main__":
    video_dir = "/var/tmp/smart-vision/video/303fef46-5cb8-48b4-88ef-eef408739423"
    image_dir = "/var/tmp/smart-vision/image/303fef46-5cb8-48b4-88ef-eef408739423"
    cv_extract_frames(None, None, video_dir, image_dir, 60, 6, 0.5)
