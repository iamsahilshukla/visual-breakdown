#!/usr/bin/env python3
"""
Progress Tracker for YouTube Video Analyzer

This module provides real-time progress tracking between the backend processing
and the Streamlit UI.
"""

import json
import os
import time
from typing import Dict, Any, Optional
from pathlib import Path


class ProgressTracker:
    """A class to track and share progress between backend and UI."""
    
    def __init__(self, session_id: str = None, output_dir: str = "streamlit_outputs"):
        """
        Initialize the progress tracker.
        
        Args:
            session_id (str): Unique session identifier
            output_dir (str): Output directory for progress files
        """
        self.session_id = session_id or f"session_{int(time.time())}"
        self.output_dir = output_dir
        self.progress_file = os.path.join(output_dir, f"progress_{self.session_id}.json")
        
        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)
        
        # Initialize progress file
        self.update_progress(0, "Initializing...")
    
    def update_progress(self, percentage: int, message: str, extra_data: Dict[str, Any] = None):
        """
        Update the progress.
        
        Args:
            percentage (int): Progress percentage (0-100)
            message (str): Current status message
            extra_data (Dict): Additional data to store
        """
        progress_data = {
            "session_id": self.session_id,
            "percentage": percentage,
            "message": message,
            "timestamp": time.time(),
            "updated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "extra_data": extra_data or {}
        }
        
        try:
            with open(self.progress_file, 'w') as f:
                json.dump(progress_data, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not update progress file: {e}")
    
    def get_progress(self) -> Optional[Dict[str, Any]]:
        """
        Get the current progress.
        
        Returns:
            Dict: Progress data or None if not available
        """
        try:
            if os.path.exists(self.progress_file):
                with open(self.progress_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Warning: Could not read progress file: {e}")
        return None
    
    def set_video_progress(self, video_index: int, total_videos: int, video_title: str, step: str):
        """
        Update progress for a specific video.
        
        Args:
            video_index (int): Current video index (1-based)
            total_videos (int): Total number of videos
            video_title (str): Title of current video
            step (str): Current processing step
        """
        # Calculate overall progress based on video progress
        video_progress = (video_index - 1) / total_videos
        
        # Each video goes through: download (5%), extract (10%), analyze (80%), summary (5%)
        if step == "download":
            step_progress = 0.05
        elif step == "extract":
            step_progress = 0.15
        elif step == "analyze":
            step_progress = 0.80
        elif step == "summary":
            step_progress = 0.95
        else:
            step_progress = 0
        
        current_video_progress = step_progress / total_videos
        overall_progress = int((video_progress + current_video_progress) * 70)  # 70% for video processing
        
        message = f"Video {video_index}/{total_videos}: {step.title()} - {video_title[:40]}{'...' if len(video_title) > 40 else ''}"
        
        extra_data = {
            "current_video": video_index,
            "total_videos": total_videos,
            "video_title": video_title,
            "step": step
        }
        
        self.update_progress(overall_progress, message, extra_data)
    
    def set_similarity_progress(self, step: str):
        """
        Update progress for similarity analysis.
        
        Args:
            step (str): Current similarity analysis step
        """
        if step == "comprehensive":
            progress = 75
            message = "🔗 Analyzing similarities between videos..."
        elif step == "pairwise":
            progress = 85
            message = "🔄 Generating pairwise comparisons..."
        elif step == "report":
            progress = 95
            message = "📋 Generating final report..."
        else:
            progress = 70
            message = f"🔗 {step}..."
        
        self.update_progress(progress, message)
    
    def set_complete(self, success: bool = True, final_message: str = None):
        """
        Mark the process as complete.
        
        Args:
            success (bool): Whether the process completed successfully
            final_message (str): Final message to display
        """
        if success:
            progress = 100
            message = final_message or "✅ Analysis completed successfully!"
        else:
            progress = 0
            message = final_message or "❌ Analysis failed"
        
        self.update_progress(progress, message)
    
    def cleanup(self):
        """Clean up the progress file."""
        try:
            if os.path.exists(self.progress_file):
                os.remove(self.progress_file)
        except Exception as e:
            print(f"Warning: Could not clean up progress file: {e}")


def get_session_progress(session_id: str, output_dir: str = "streamlit_outputs") -> Optional[Dict[str, Any]]:
    """
    Get progress for a specific session.
    
    Args:
        session_id (str): Session identifier
        output_dir (str): Output directory
        
    Returns:
        Dict: Progress data or None
    """
    progress_file = os.path.join(output_dir, f"progress_{session_id}.json")
    try:
        if os.path.exists(progress_file):
            with open(progress_file, 'r') as f:
                return json.load(f)
    except Exception:
        pass
    return None