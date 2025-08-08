import cv2
import os
from typing import List, Tuple


def extract_fixed_frames(video_path: str, output_dir: str, max_frames: int = 20, max_duration: float = 20.0) -> List[Tuple[float, str]]:
    """
    Extract a fixed number of frames evenly distributed across video duration.
    
    Args:
        video_path (str): Path to the input video file
        output_dir (str): Directory to save extracted frames
        max_frames (int): Maximum number of frames to extract (default: 20)
        max_duration (float): Maximum duration to analyze in seconds (default: 20.0)
        
    Returns:
        List[Tuple[float, str]]: List of (timestamp, frame_path) tuples
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Open the video file
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError(f"Error: Could not open video file {video_path}")
    
    # Get video properties
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = total_frames / fps
    
    # Limit analysis to max_duration seconds
    analysis_duration = min(duration, max_duration)
    analysis_frames = int(fps * analysis_duration)
    
    print(f"Video info: {fps:.2f} FPS, {duration:.2f}s duration, {total_frames} total frames")
    print(f"Analyzing first {analysis_duration:.2f}s ({analysis_frames} frames)")
    
    # Calculate which frames to extract (evenly distributed)
    if analysis_frames <= max_frames:
        # If video has fewer frames than max_frames, extract all available frames
        frame_indices = list(range(analysis_frames))
    else:
        # Extract max_frames evenly distributed across the analysis duration
        frame_indices = [int(i * analysis_frames / max_frames) for i in range(max_frames)]
    
    print(f"Extracting {len(frame_indices)} frames evenly distributed")
    
    extracted_frames = []
    
    # Extract specific frames
    for i, frame_index in enumerate(frame_indices):
        # Set video position to specific frame
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_index)
        ret, frame = cap.read()
        
        if not ret:
            print(f"Warning: Could not read frame at index {frame_index}")
            continue
            
        timestamp = frame_index / fps
        frame_filename = f"frame_{i+1:02d}_{timestamp:.2f}s.jpg"
        frame_path = os.path.join(output_dir, frame_filename)
        
        # Save the frame
        success = cv2.imwrite(frame_path, frame)
        if success:
            extracted_frames.append((timestamp, frame_path))
            print(f"Extracted frame {i+1}/{len(frame_indices)}: {timestamp:.2f}s -> {frame_filename}")
        else:
            print(f"Failed to save frame at {timestamp:.2f}s")
    
    cap.release()
    print(f"Extraction complete: {len(extracted_frames)} frames extracted from {analysis_duration:.2f}s")
    return extracted_frames


def extract_frames(video_path: str, output_dir: str, interval_seconds: float = 1.0) -> List[Tuple[float, str]]:
    """
    Extract frames from a video at regular intervals.
    
    Args:
        video_path (str): Path to the input video file
        output_dir (str): Directory to save extracted frames
        interval_seconds (float): Interval between frames in seconds
        
    Returns:
        List[Tuple[float, str]]: List of (timestamp, frame_path) tuples
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Open the video file
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError(f"Error: Could not open video file {video_path}")
    
    # Get video properties
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = total_frames / fps
    
    print(f"Video info: {fps:.2f} FPS, {duration:.2f}s duration, {total_frames} total frames")
    
    # Calculate frame interval
    frame_interval = int(fps * interval_seconds)
    
    extracted_frames = []
    frame_count = 0
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
            
        # Extract frame at specified intervals
        if frame_count % frame_interval == 0:
            timestamp = frame_count / fps
            frame_filename = f"frame_{timestamp:.2f}s.jpg"
            frame_path = os.path.join(output_dir, frame_filename)
            
            # Save the frame
            success = cv2.imwrite(frame_path, frame)
            if success:
                extracted_frames.append((timestamp, frame_path))
                print(f"Extracted frame at {timestamp:.2f}s -> {frame_path}")
            else:
                print(f"Failed to save frame at {timestamp:.2f}s")
        
        frame_count += 1
    
    cap.release()
    print(f"Extraction complete: {len(extracted_frames)} frames extracted")
    return extracted_frames


def validate_video_file(video_path: str) -> bool:
    """
    Validate if the video file exists and can be opened.
    
    Args:
        video_path (str): Path to the video file
        
    Returns:
        bool: True if valid, False otherwise
    """
    if not os.path.exists(video_path):
        print(f"Error: Video file {video_path} does not exist")
        return False
    
    cap = cv2.VideoCapture(video_path)
    is_valid = cap.isOpened()
    cap.release()
    
    if not is_valid:
        print(f"Error: Could not open video file {video_path}")
    
    return is_valid


def get_video_info(video_path: str) -> dict:
    """
    Get basic information about the video file.
    
    Args:
        video_path (str): Path to the video file
        
    Returns:
        dict: Video information including fps, duration, resolution
    """
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError(f"Could not open video file {video_path}")
    
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    duration = total_frames / fps
    
    cap.release()
    
    return {
        "fps": fps,
        "total_frames": total_frames,
        "duration_seconds": duration,
        "width": width,
        "height": height,
        "resolution": f"{width}x{height}"
    } 