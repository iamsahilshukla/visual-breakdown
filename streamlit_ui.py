#!/usr/bin/env python3
"""
Streamlit Web UI for YouTube Batch Video Analyzer

A modern, user-friendly web interface for analyzing YouTube videos and comparing their similarities.
"""

import streamlit as st
import asyncio
import os
import json
import time
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Import our modules
from batch_processor import BatchVideoProcessor
from youtube_utils import YouTubeDownloader, validate_youtube_urls
from gpt_utils import test_api_connection
from ui_utils import run_with_progress, create_sample_urls, create_url_validation_tips, create_tips_and_tricks, estimate_processing_time


# Page configuration
st.set_page_config(
    page_title="YouTube Video Analyzer",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load environment variables
load_dotenv()


def init_session_state():
    """Initialize session state variables."""
    if 'processing_status' not in st.session_state:
        st.session_state.processing_status = 'idle'
    if 'results' not in st.session_state:
        st.session_state.results = None
    if 'urls' not in st.session_state:
        st.session_state.urls = []
    if 'api_key_valid' not in st.session_state:
        st.session_state.api_key_valid = False


def check_api_key(api_key: str) -> bool:
    """Check if the API key is valid."""
    try:
        return test_api_connection(api_key)
    except Exception:
        return False


def validate_urls_ui(urls):
    """Validate URLs and show results in UI."""
    if not urls:
        return [], []
    
    downloader = YouTubeDownloader()
    valid_urls, invalid_urls = downloader.validate_urls(urls)
    
    if valid_urls:
        st.success(f"✅ {len(valid_urls)} valid YouTube URLs found")
        with st.expander("Valid URLs", expanded=False):
            for i, url in enumerate(valid_urls, 1):
                st.write(f"{i}. {url}")
    
    if invalid_urls:
        st.error(f"❌ {len(invalid_urls)} invalid URLs found")
        with st.expander("Invalid URLs", expanded=True):
            for url in invalid_urls:
                st.write(f"• {url}")
    
    return valid_urls, invalid_urls


def display_cost_estimate(num_videos: int, max_frames: int):
    """Display cost estimation."""
    frame_cost = num_videos * max_frames * 0.01
    summary_cost = num_videos * 0.03
    similarity_cost = 0.10
    total_cost = frame_cost + summary_cost + similarity_cost
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Frame Analysis", f"${frame_cost:.2f}", f"{num_videos * max_frames} frames")
    with col2:
        st.metric("Video Summaries", f"${summary_cost:.2f}", f"{num_videos} summaries")
    with col3:
        st.metric("Similarity Analysis", f"${similarity_cost:.2f}", "1 analysis")
    with col4:
        st.metric("**Total Estimate**", f"**${total_cost:.2f}**", "Approximate")


def display_results_summary(results):
    """Display a summary of processing results."""
    if not results or not results.get('summary'):
        return
    
    summary = results['summary']
    
    # Main metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Videos Processed", summary.get('successful_analyses', 0))
    with col2:
        st.metric("Frames Analyzed", summary.get('total_frames_analyzed', 0))
    with col3:
        st.metric("Tokens Used", f"{summary.get('total_tokens_used', 0):,}")
    with col4:
        st.metric("Actual Cost", f"${summary.get('estimated_cost_usd', 0):.3f}")


def display_similarity_analysis(results):
    """Display similarity analysis results."""
    similarity = results.get('similarity_analysis', {})
    if not similarity:
        return
    
    comprehensive = similarity.get('comprehensive_analysis', {})
    pairwise = similarity.get('pairwise_comparisons', {})
    
    if comprehensive.get('success'):
        st.subheader("🔗 Similarity Analysis")
        
        # Display comprehensive analysis
        with st.expander("📊 Comprehensive Analysis", expanded=True):
            st.markdown(comprehensive.get('analysis', ''))
        
        # Display pairwise comparisons
        if pairwise.get('success'):
            with st.expander("🔄 Pairwise Comparisons", expanded=False):
                comparisons = pairwise.get('pairwise_comparisons', [])
                
                if comparisons:
                    # Create a simple comparison table
                    comparison_data = []
                    for comp in comparisons:
                        comparison_data.append({
                            'Video 1': comp.get('video1_title', 'Unknown')[:30] + '...',
                            'Video 2': comp.get('video2_title', 'Unknown')[:30] + '...',
                            'Comparison': comp.get('comparison', '')[:100] + '...'
                        })
                    
                    df = pd.DataFrame(comparison_data)
                    st.dataframe(df, use_container_width=True)


def display_individual_videos(results):
    """Display individual video analyses."""
    video_analyses = results.get('video_analyses', [])
    if not video_analyses:
        return
    
    st.subheader("📹 Individual Video Analyses")
    
    for i, video in enumerate(video_analyses):
        if not video.get('breakdown_success'):
            continue
            
        breakdown = video.get('breakdown_data', {})
        metadata = breakdown.get('metadata', {})
        youtube_info = metadata.get('youtube_info', {})
        video_summary = breakdown.get('video_summary', {})
        
        with st.expander(f"Video {i+1}: {youtube_info.get('title', 'Unknown Title')}", expanded=False):
            
            # Video info
            col1, col2, col3 = st.columns(3)
            with col1:
                st.write(f"**Duration Analyzed:** {metadata.get('processing_settings', {}).get('duration_seconds', 0)}s")
            with col2:
                st.write(f"**Frames Extracted:** {video.get('frames_extracted', 0)}")
            with col3:
                st.write(f"**Tokens Used:** {video.get('total_tokens', 0)}")
            
            # Video summary
            if video_summary.get('success'):
                st.markdown("**📝 Video Summary:**")
                st.markdown(video_summary.get('summary', ''))
            
            # Sample frame analyses
            frame_analyses = breakdown.get('frame_analyses', [])
            successful_frames = [f for f in frame_analyses if f.get('success')]
            
            if successful_frames:
                st.markdown("**🖼️ Sample Frame Descriptions:**")
                # Show first 3 frames as examples
                for frame in successful_frames[:3]:
                    timestamp = frame.get('timestamp', 0)
                    description = frame.get('description', '')
                    st.write(f"• **{timestamp:.1f}s:** {description[:200]}{'...' if len(description) > 200 else ''}")


async def run_analysis(urls, duration, max_frames, max_videos, batch_size, api_key, output_dir):
    """Run the batch analysis."""
    processor = BatchVideoProcessor(
        api_key=api_key,
        output_dir=output_dir
    )
    
    try:
        result = await processor.process_youtube_urls(
            urls=urls,
            duration_seconds=duration,
            max_videos=max_videos,
            max_frames_per_video=max_frames,
            batch_size=batch_size
        )
        return result
    except Exception as e:
        st.error(f"Error during analysis: {str(e)}")
        return None
    finally:
        processor.cleanup()


def main():
    """Main Streamlit application."""
    init_session_state()
    
    # Header
    st.title("🎬 YouTube Video Analyzer")
    st.markdown("*Analyze and compare YouTube videos using AI-powered visual breakdown*")
    
    # Sidebar for settings
    with st.sidebar:
        st.header("⚙️ Settings")
        
        # API Key
        st.subheader("🔑 OpenAI API Key")
        api_key = st.text_input(
            "API Key", 
            value=os.getenv('OPENAI_API_KEY', ''),
            type="password",
            help="Your OpenAI API key for GPT-4o Vision"
        )
        
        if st.button("Test API Key"):
            if api_key:
                with st.spinner("Testing API connection..."):
                    st.session_state.api_key_valid = check_api_key(api_key)
                if st.session_state.api_key_valid:
                    st.success("✅ API key is valid!")
                else:
                    st.error("❌ API key is invalid or connection failed")
            else:
                st.warning("Please enter an API key")
        
        st.divider()
        
        # Processing Settings
        st.subheader("🎛️ Processing Settings")
        
        duration = st.slider(
            "Duration per video (seconds)",
            min_value=5,
            max_value=60,
            value=20,
            help="How many seconds of each video to analyze"
        )
        
        max_frames = st.slider(
            "Max frames per video",
            min_value=5,
            max_value=50,
            value=20,
            help="Maximum number of frames to extract per video"
        )
        
        max_videos = st.slider(
            "Max videos to process",
            min_value=1,
            max_value=10,
            value=10,
            help="Maximum number of videos to process"
        )
        
        batch_size = st.slider(
            "Batch size",
            min_value=1,
            max_value=10,
            value=5,
            help="Number of frames to process in parallel"
        )
        
        output_dir = st.text_input(
            "Output Directory",
            value="streamlit_outputs",
            help="Directory to save results"
        )
    
    # Main content area
    
    # URL Input Section
    st.header("📋 YouTube URLs")
    
    # Help and samples
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown("Enter YouTube URLs to analyze and compare their visual content.")
    with col2:
        if st.button("📝 Use Sample URLs"):
            sample_urls = create_sample_urls()
            st.session_state.sample_urls = '\n'.join(sample_urls)
    
    # Show help
    with st.expander("📖 Help & URL Formats"):
        st.markdown(create_url_validation_tips())
    
    # URL input method selection
    input_method = st.radio(
        "How would you like to provide URLs?",
        ["Manual Entry", "Upload File", "Paste List"],
        horizontal=True
    )
    
    urls = []
    
    if input_method == "Manual Entry":
        st.subheader("Enter URLs manually")
        default_value = st.session_state.get('sample_urls', '')
        url_input = st.text_area(
            "YouTube URLs (one per line)",
            value=default_value,
            height=150,
            placeholder="https://www.youtube.com/watch?v=...\nhttps://youtu.be/...\n..."
        )
        if url_input:
            urls = [url.strip() for url in url_input.split('\n') if url.strip()]
    
    elif input_method == "Upload File":
        st.subheader("Upload a text file")
        uploaded_file = st.file_uploader(
            "Choose a .txt file with YouTube URLs",
            type=['txt'],
            help="Upload a text file with one YouTube URL per line"
        )
        if uploaded_file:
            content = uploaded_file.read().decode('utf-8')
            urls = [url.strip() for url in content.split('\n') if url.strip() and not url.startswith('#')]
    
    elif input_method == "Paste List":
        st.subheader("Paste a list of URLs")
        pasted_urls = st.text_area(
            "Paste YouTube URLs here",
            height=150,
            placeholder="Paste multiple URLs separated by lines, commas, or spaces"
        )
        if pasted_urls:
            # Split by various delimiters
            import re
            urls = re.split(r'[\n,\s]+', pasted_urls.strip())
            urls = [url.strip() for url in urls if url.strip()]
    
    # URL Validation
    if urls:
        st.session_state.urls = urls
        valid_urls, invalid_urls = validate_urls_ui(urls)
        
        if valid_urls:
            # Limit to max_videos
            if len(valid_urls) > max_videos:
                st.warning(f"⚠️ Limiting to first {max_videos} videos (found {len(valid_urls)})")
                valid_urls = valid_urls[:max_videos]
            
            # Cost Estimation
            st.subheader("💰 Cost Estimation")
            display_cost_estimate(len(valid_urls), max_frames)
            
            # Time Estimation
            estimated_time = estimate_processing_time(len(valid_urls), max_frames)
            st.info(f"⏱️ Estimated processing time: **{estimated_time}**")
            
            # Analysis Button
            if api_key and st.session_state.api_key_valid:
                if st.button("🚀 Start Analysis", type="primary", use_container_width=True):
                    st.session_state.processing_status = 'running'
                    
                    # Show processing info
                    with st.container():
                        st.info("🎬 Processing started! This will take several minutes...")
                        st.warning("⚠️ **Note**: Processing continues even if progress seems to pause. Each video takes 2-3 minutes to analyze.")
                        
                        # Video list being processed
                        st.write("**Videos to analyze:**")
                        for i, url in enumerate(valid_urls, 1):
                            st.write(f"{i}. {url}")
                        
                        # Processing details
                        col1, col2 = st.columns(2)
                        with col1:
                            st.write(f"⏱️ **Estimated time:** {estimated_time}")
                        with col2:
                            st.write(f"🖼️ **Frames per video:** {max_frames}")
                        
                        st.write("---")
                        
                        # Run analysis with enhanced progress tracking
                        result = run_with_progress(
                            run_analysis,
                            None,  # progress_callback
                            valid_urls, duration, max_frames, max_videos, batch_size, api_key, output_dir
                        )
                        
                        if result:
                            st.session_state.results = result
                            st.session_state.processing_status = 'completed'
                            st.success("🎉 Analysis completed successfully!")
                            st.balloons()
                            st.rerun()  # Refresh to show results
                        else:
                            st.session_state.processing_status = 'failed'
                            st.error("❌ Analysis failed. Please check the logs and try again.")
            else:
                st.warning("⚠️ Please enter a valid API key before starting analysis")
    
    # Results Section
    if st.session_state.results:
        st.header("📊 Results")
        
        # Summary
        display_results_summary(st.session_state.results)
        
        # Tabs for different views
        tab1, tab2, tab3 = st.tabs(["🔗 Similarities", "📹 Individual Videos", "📄 Raw Data"])
        
        with tab1:
            display_similarity_analysis(st.session_state.results)
        
        with tab2:
            display_individual_videos(st.session_state.results)
        
        with tab3:
            st.subheader("📄 Complete Results")
            st.json(st.session_state.results)
            
            # Download button
            results_json = json.dumps(st.session_state.results, indent=2)
            st.download_button(
                label="📥 Download Results",
                data=results_json,
                file_name=f"youtube_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )
    
    # Tips and Help Section
    if not st.session_state.results:  # Only show when no results to avoid clutter
        st.header("💡 Tips & Tricks")
        with st.expander("🎯 How to get the best results", expanded=False):
            st.markdown(create_tips_and_tricks())
    
    # Footer
    st.divider()
    st.markdown("""
    <div style='text-align: center; color: #666;'>
        <p>🎬 YouTube Video Analyzer | Powered by OpenAI GPT-4o Vision</p>
        <p>Built with Streamlit • Open source tool for video content analysis</p>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()