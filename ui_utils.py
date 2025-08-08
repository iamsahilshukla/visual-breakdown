#!/usr/bin/env python3
"""
UI Utilities for Streamlit interface

Helper functions and classes for the YouTube Video Analyzer UI.
"""

import asyncio
import threading
import time
from typing import Any, Callable, Optional
import streamlit as st


class AsyncRunner:
    """Helper class to run async functions in Streamlit."""
    
    def __init__(self):
        self.result = None
        self.error = None
        self.finished = False
    
    def run_async_function(self, async_func, *args, **kwargs):
        """Run an async function in a separate thread."""
        def thread_function():
            try:
                # Create new event loop for this thread
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                # Run the async function
                self.result = loop.run_until_complete(async_func(*args, **kwargs))
                
            except Exception as e:
                self.error = e
            finally:
                self.finished = True
                loop.close()
        
        # Start the thread
        thread = threading.Thread(target=thread_function)
        thread.start()
        
        return thread


def run_with_progress(async_func, progress_callback: Optional[Callable] = None, *args, **kwargs):
    """Run an async function with progress tracking."""
    runner = AsyncRunner()
    thread = runner.run_async_function(async_func, *args, **kwargs)
    
    # Create progress indicators
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    # More realistic progress tracking based on typical processing times
    progress_steps = [
        (5, "🔍 Validating URLs..."),
        (15, "📥 Downloading videos..."),
        (25, "🖼️ Extracting frames from videos..."),
        (35, "🤖 Analyzing video 1 with AI..."),
        (65, "🤖 Analyzing video 2 with AI..."),
        (80, "📝 Generating video summaries..."),
        (90, "🔗 Comparing similarities between videos..."),
        (95, "📋 Generating final report..."),
        (99, "🧹 Cleaning up temporary files..."),
        (100, "✅ Complete!")
    ]
    
    step_index = 0
    start_time = time.time()
    last_progress = 0
    
    # Wait for completion with progress updates
    while not runner.finished:
        elapsed = time.time() - start_time
        
        # More sophisticated progress estimation
        # First 30 seconds: downloading and setup (25%)
        # Next 3-5 minutes: AI analysis (50% of total time)
        # Final minute: similarity and report generation (25%)
        
        if elapsed < 30:
            # Initial phase: downloading and setup
            progress = min(25, int(elapsed / 30 * 25))
        elif elapsed < 300:  # 5 minutes
            # Main analysis phase (this is where most time is spent)
            analysis_progress = (elapsed - 30) / 270  # 270 seconds = 4.5 minutes
            progress = 25 + int(analysis_progress * 55)  # 25% to 80%
        else:
            # Final phase: similarity analysis and reporting
            final_progress = min(1.0, (elapsed - 300) / 60)  # 1 minute for final phase
            progress = 80 + int(final_progress * 20)  # 80% to 100%
        
        # Don't go backwards in progress
        progress = max(last_progress, progress)
        last_progress = progress
        
        # Update progress bar
        progress_bar.progress(min(99, progress))  # Never show 100% until actually done
        
        # Update status text based on progress
        for threshold, message in progress_steps:
            if progress >= threshold - 5 and step_index < len(progress_steps):
                if progress_steps[step_index][1] != message:
                    status_text.text(message)
                    step_index += 1
                break
        
        time.sleep(2)  # Update every 2 seconds
    
    # Wait for thread to complete
    thread.join()
    
    # Final progress update
    if runner.error:
        progress_bar.progress(0)
        status_text.text(f"❌ Error: {str(runner.error)}")
        st.error(f"Analysis failed: {str(runner.error)}")
        return None
    else:
        progress_bar.progress(100)
        status_text.text("✅ Analysis completed successfully!")
        time.sleep(1)  # Brief pause to show completion
        return runner.result


def create_sample_urls():
    """Create sample YouTube URLs for testing."""
    return [
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ",  # Rick Roll (famous)
        "https://youtu.be/9bZkp7q19f0",  # PSY - GANGNAM STYLE
        "https://www.youtube.com/watch?v=kJQP7kiw5Fk",  # Despacito
    ]


def format_duration(seconds: float) -> str:
    """Format duration in seconds to human readable format."""
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f}m"
    else:
        hours = seconds / 3600
        return f"{hours:.1f}h"


def format_large_number(number: int) -> str:
    """Format large numbers with K, M suffixes."""
    if number < 1000:
        return str(number)
    elif number < 1000000:
        return f"{number/1000:.1f}K"
    else:
        return f"{number/1000000:.1f}M"


def create_url_validation_tips():
    """Create helpful tips for URL validation."""
    return """
    ### 📋 Supported YouTube URL Formats:
    
    - **Standard:** `https://www.youtube.com/watch?v=VIDEO_ID`
    - **Short:** `https://youtu.be/VIDEO_ID`
    - **Embed:** `https://www.youtube.com/embed/VIDEO_ID`
    - **Shorts:** `https://www.youtube.com/shorts/VIDEO_ID`
    
    ### 💡 Tips:
    - One URL per line
    - Remove any extra parameters for cleaner URLs
    - Make sure videos are public and not age-restricted
    - Playlists are not supported (individual videos only)
    """


def estimate_processing_time(num_videos: int, max_frames: int) -> str:
    """Estimate processing time based on configuration."""
    # Rough estimates based on testing
    download_time = num_videos * 30  # 30 seconds per video
    frame_analysis_time = num_videos * max_frames * 2  # 2 seconds per frame
    summary_time = num_videos * 20  # 20 seconds per summary
    similarity_time = 60  # 60 seconds for similarity analysis
    
    total_seconds = download_time + frame_analysis_time + summary_time + similarity_time
    
    return format_duration(total_seconds)


def create_tips_and_tricks():
    """Create helpful tips for users."""
    return """
    ### 🎯 Tips for Best Results:
    
    **🎬 Video Selection:**
    - Choose videos with similar themes for more interesting comparisons
    - Mix different content types (tutorials, vlogs, etc.) for diverse analysis
    - Ensure videos are at least 20 seconds long
    
    **⚙️ Settings Optimization:**
    - **20 frames** is usually perfect for most videos
    - **Higher batch size** = faster processing (if you have good internet)
    - **Shorter duration** = lower costs but less context
    
    **💰 Cost Management:**
    - Start with 2-3 videos to test
    - Use 10-15 frames for quick previews
    - Each video costs approximately $0.20-0.50 to analyze
    
    **🚀 Performance:**
    - Close other applications for faster processing
    - Stable internet connection recommended
    - Processing time: ~2-5 minutes per video
    """