import numpy as np
import os
import cv2
import time
from ultralytics import YOLO
from collections import defaultdict
from smartvision.common.utils import get_str_time, get_available_device


class VehicleDetectionSystem:
    def __init__(self, model_path="yolov8n.pt", output_dir="output"):
        """Initialize the vehicle detection system with a YOLO model."""
        self.model = YOLO(model_path, verbose=False)
        self.output_dir = output_dir
        self.device = get_available_device()
        os.makedirs(self.output_dir, exist_ok=True)

    def get_frame(self, video_file_name, start_time):
        # Open the video file
        cap = cv2.VideoCapture(video_file_name)
        if not cap.isOpened():
            raise ValueError(f"Could not open video file: {video_file_name}")

        # Get video properties
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        # Calculate the frame number for the start time
        start_frame = int(start_time * fps)
        if start_frame >= total_frames:
            raise ValueError(f"Start time {start_time} is beyond the video duration")

        # Set the frame position
        cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)

        # Read the frame
        ret, frame = cap.read()
        if not ret:
            cap.release()
            raise ValueError("Failed to read frame from video")
        cap.release()
        return frame

    def get_vehicle_annotation_data(self, video_file_name, start_time):
        """
        Extract a frame from the video at the specified start time and annotate all vehicles.
        Vehicles are color-coded based on their size, with IDs displayed directly on the image.

        Args:
            video_file_name (str): Path to the video file
            start_time (float): Time in seconds from which to extract the frame

        Returns:
            tuple: (extracted_image_file_name, vehicles)
                - extracted_image_file_name (str): Path to the saved annotated image
                - vehicles (list): List of dictionaries containing vehicle IDs and bounding boxes
        """
        frame = self.get_frame(video_file_name=video_file_name, start_time=start_time)
        # Detect vehicles using YOLO
        results = self.model.predict(
            source=frame, device=self.device, classes=[2], verbose=False
        )  # Common vehicle class indices in COCO

        vehicles = []
        detections_with_area = []

        # Calculate area for each detection
        for i, detection in enumerate(results[0].boxes.data):
            x1, y1, x2, y2, conf, cls = detection
            x1, y1, x2, y2 = map(int, [x1, y1, x2, y2])
            box = [x1, y1, x2, y2]

            # Calculate box area
            area = (x2 - x1) * (y2 - y1)

            detections_with_area.append(
                {"index": i, "box": box, "area": area, "detection": detection}
            )

        # Sort detections by area (largest to smallest)
        detections_with_area.sort(key=lambda x: x["area"], reverse=True)

        # Define size categories and colors
        # Size thresholds can be adjusted based on your specific video characteristics
        size_categories = [
            {"name": "Very Large", "color": (0, 0, 255)},  # Red
            {"name": "Large", "color": (0, 165, 255)},  # Orange
            {"name": "Medium", "color": (0, 255, 0)},  # Green
            # {"name": "Small", "color": (255, 0, 0)},         # Blue
            # {"name": "Very Small", "color": (255, 255, 0)}   # Cyan
        ]

        # Find area thresholds for categories
        if detections_with_area:
            max_area = detections_with_area[0]["area"]
            min_area = (
                detections_with_area[-1]["area"]
                if len(detections_with_area) > 1
                else max_area
            )

            # Calculate thresholds
            area_range = max_area - min_area
            thresholds = [
                min_area + (area_range * 0.8),  # Very Large threshold
                min_area + (area_range * 0.6),  # Large threshold
                # min_area + (area_range * 0.4),  # Medium threshold
                # min_area + (area_range * 0.2)   # Small threshold
                # Below this is Very Small
            ]
        else:
            thresholds = [0, 0, 0, 0]  # Default if no detections

        annotated_frame = frame.copy()

        # Add a legend to the image
        legend_y = 30
        for i, category in enumerate(size_categories):
            # Draw colored rectangle for legend
            cv2.rectangle(
                annotated_frame,
                (10, legend_y - 20),
                (30, legend_y),
                category["color"],
                -1,
            )

            # Add category name
            cv2.putText(
                annotated_frame,
                category["name"],
                (40, legend_y),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                category["color"],
                2,
            )

            legend_y += 30

        # Process each detection with appropriate color based on size
        for i, detection_data in enumerate(detections_with_area):
            if i == 6:
                break
            box = detection_data["box"]
            area = detection_data["area"]
            x1, y1, x2, y2 = box

            # Assign vehicle ID (based on size rank)
            vehicle_id = i + 1

            # Determine category based on area
            category_index = 1  # Default to "Very Small"
            for j, threshold in enumerate(thresholds):
                if area >= threshold:
                    category_index = j
                    break

            # Get color for this category
            color = size_categories[category_index]["color"]
            category_name = size_categories[category_index]["name"]

            # Add to vehicles list
            vehicles.append(
                {"vehicle_id": vehicle_id, "box": box, "category": category_name}
            )

            # Draw bounding box with category-based color
            cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), color, 2)

            # Create background for text to improve readability
            text = f"ID:{vehicle_id}"
            text_size = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)[0]
            cv2.rectangle(
                annotated_frame,
                (x1, y1 - text_size[1] - 10),
                (x1 + text_size[0] + 10, y1),
                color,
                -1,
            )

            # Add ID text
            cv2.putText(
                annotated_frame,
                text,
                (x1 + 5, y1 - 5),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (255, 255, 255),
                2,
            )

        # Save the annotated image
        image_filename = f"{self.output_dir}/annotated_frame.jpg"
        cv2.imwrite(image_filename, annotated_frame)

        # Release resources

        return image_filename, vehicles

    def nearest_distance_detection(self, video_file_name, target_vehicle, start_time):
        """
        Find the top 3 vehicles that come closest to the target vehicle and generate 10-second clips.

        Args:
            video_file_name (str): Path to the video file
            target_vehicle (dict): Dict with vehicle_id and box of the target vehicle
            start_time (float): Time in seconds from which to start the detection

        Returns:
            list: List of dictionaries containing distance, seconds, and footage file name for top 3 closest vehicles
        """
        # Open the video file
        cap = cv2.VideoCapture(video_file_name)
        if not cap.isOpened():
            raise ValueError(f"Could not open video file: {video_file_name}")

        # Get video properties
        fps = cap.get(cv2.CAP_PROP_FPS)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        # Calculate the frame number for the start time
        start_frame = int(start_time * fps)
        if start_frame >= total_frames:
            cap.release()
            raise ValueError(f"Start time {start_time} is beyond the video duration")

        # Set the frame position
        cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)

        # Extract target vehicle box
        target_box = target_vehicle["box"]

        # Calculate the target vehicle's center
        target_center_x = (target_box[0] + target_box[2]) / 2
        target_center_y = (target_box[1] + target_box[3]) / 2
        target_center = (target_center_x, target_center_y)

        # Store distance data for each detected vehicle over time
        vehicle_distances = defaultdict(list)
        frame_index = start_frame

        # Process one frame per second
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            # Current time in the video
            current_time = frame_index / fps

            # Detect vehicles
            results = self.model.predict(
                source=frame, device=self.device, verbose=False, classes=[2, 3, 5, 7]
            )  # Common vehicle class indices in COCO

            # Process each detection
            for detection in results[0].boxes.data:
                x1, y1, x2, y2, conf, cls = detection
                x1, y1, x2, y2 = map(int, [x1, y1, x2, y2])

                # Calculate the center of the detected vehicle
                center_x = (x1 + x2) / 2
                center_y = (y1 + y2) / 2

                # Compute Euclidean distance to target vehicle
                distance = np.sqrt(
                    (center_x - target_center_x) ** 2
                    + (center_y - target_center_y) ** 2
                )

                # Create a unique ID for this vehicle based on its position (simple approach)
                # In a real system, you'd want to use tracking
                vehicle_key = f"{int(center_x/10)}_{int(center_y/10)}_{int(cls)}"

                # Store the distance and time
                vehicle_distances[vehicle_key].append(
                    (distance, current_time, (x1, y1, x2, y2))
                )

            # Skip to the next second
            frame_index += fps
            if frame_index >= total_frames:
                break
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_index)

        # Find minimum distance for each vehicle
        min_distances = {}
        for vehicle_key, distances in vehicle_distances.items():
            if distances:  # Check if the list is not empty
                min_distance_data = min(distances, key=lambda x: x[0])
                min_distances[vehicle_key] = min_distance_data

        # Sort vehicles by minimum distance and get top 3
        top_vehicles = sorted(min_distances.items(), key=lambda x: x[1][0])[:3]

        # Generate 10-second clips for each of the top 3 vehicles
        results = []

        for i, (vehicle_key, (distance, time_point, box)) in enumerate(top_vehicles):
            # Calculate start and end times for the 10-second clip (5 seconds before and 5 seconds after)
            clip_start_time = max(0, time_point - 5)
            clip_end_time = min(total_frames / fps, time_point + 5)

            # Create the clip
            clip_filename = self._create_clip(
                video_file_name, clip_start_time, clip_end_time, target_box, box, i + 1
            )

            results.append(
                {
                    "distance": distance,
                    "seconds": time_point,
                    "footage_file_name": clip_filename,
                }
            )

        # Release resources
        cap.release()

        return results

    def _create_clip(
        self, video_file_name, start_time, end_time, target_box, vehicle_box, index
    ):
        """
        Create a 10-second clip showing the target vehicle and the detected close vehicle.

        Args:
            video_file_name (str): Path to the video file
            start_time (float): Start time for the clip
            end_time (float): End time for the clip
            target_box (list): Bounding box of the target vehicle
            vehicle_box (tuple): Bounding box of the detected vehicle
            index (int): Index for the output filename

        Returns:
            str: Path to the created clip
        """
        # Open the video file
        cap = cv2.VideoCapture(video_file_name)
        if not cap.isOpened():
            raise ValueError(f"Could not open video file: {video_file_name}")

        # Get video properties
        fps = cap.get(cv2.CAP_PROP_FPS)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        # Create VideoWriter object
        timestamp = int(time.time())
        output_filename = f"{self.output_dir}/vehicle_{index}_proximity_{timestamp}.mp4"
        # fourcc = cv2.VideoWriter_fourcc(*"mp4v")  # or use 'XVID'
        fourcc = cv2.VideoWriter_fourcc(*"avc1")
        out = cv2.VideoWriter(output_filename, fourcc, fps, (width, height))

        # Set starting frame
        start_frame = int(start_time * fps)
        end_frame = int(end_time * fps)
        cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)

        # Process frames
        for _ in range(start_frame, end_frame):
            ret, frame = cap.read()
            if not ret:
                break

            # Draw the target vehicle (in red)
            cv2.rectangle(
                frame,
                (target_box[0], target_box[1]),
                (target_box[2], target_box[3]),
                (0, 0, 255),
                2,
            )
            cv2.putText(
                frame,
                "Target",
                (target_box[0], target_box[1] - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 0, 255),
                2,
            )

            # Draw the detected close vehicle (in blue)
            x1, y1, x2, y2 = vehicle_box
            cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 0, 0), 2)
            cv2.putText(
                frame,
                f"Proximity {index}",
                (x1, y1 - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (255, 0, 0),
                2,
            )

            # Write the frame
            out.write(frame)

        # Release resources
        cap.release()
        out.release()

        return output_filename


# Example usage
if __name__ == "__main__":
    detector = VehicleDetectionSystem(model_path="/opt/models/yolo/yolov8n.pt")

    # Example parameters
    video_file = "/Users/tju/Resources/videos/collision-origin.mp4"
    start_time = 10.0  # Start at 10 seconds into the video

    # 1. Get frame with annotated vehicles
    image_file, vehicles = detector.get_vehicle_annotation_data(video_file, start_time)
    # detector.test(video_file_name=video_file, start_time=start_time)

    # Assuming the user selected vehicle ID 2
    selected_vehicle_id = 1
    selected_vehicle = next(
        (v for v in vehicles if v["vehicle_id"] == selected_vehicle_id), None
    )

    if selected_vehicle:
        # 2. Detect nearest vehicles
        results = detector.nearest_distance_detection(
            video_file, selected_vehicle, start_time
        )
        print("\nTop 3 closest vehicles:")
        for i, result in enumerate(results):
            print(
                f"{i+1}. Distance: {result['distance']:.2f} pixels, Time: {result['seconds']:.2f}s"
            )
            print(f"   Video clip: {result['footage_file_name']}")
    else:
        print(f"Vehicle with ID {selected_vehicle_id} not found")
