#!/usr/bin/env python3
"""
Batch Video Processor

This module provides functionality to process multiple YouTube videos in batch,
perform visual breakdown analysis, and analyze similarities between them.
"""

import os
import json
import time
import asyncio
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path

from youtube_utils import YouTubeDownloader
from video_utils import extract_frames, extract_fixed_frames, get_video_info, validate_video_file
from gpt_utils import GPTVisionAnalyzer
from similarity_analyzer import VideoSimilarityAnalyzer, save_similarity_results


class BatchVideoProcessor:
    """
    A class to handle batch processing of multiple YouTube videos.
    """
    
    def __init__(self, api_key: str = None, output_dir: str = "batch_outputs"):
        """
        Initialize the batch processor.
        
        Args:
            api_key (str, optional): OpenAI API key
            output_dir (str): Base output directory for all results
        """
        self.api_key = api_key
        self.output_dir = output_dir
        self.youtube_downloader = YouTubeDownloader()
        self.gpt_analyzer = GPTVisionAnalyzer(api_key)
        self.similarity_analyzer = VideoSimilarityAnalyzer(api_key)
        
        # Setup output directories
        self.setup_output_directories()
    
    def setup_output_directories(self):
        """Setup all necessary output directories."""
        # Main output directory
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Subdirectories
        self.videos_dir = os.path.join(self.output_dir, "downloaded_videos")
        self.frames_dir = os.path.join(self.output_dir, "frames")
        self.breakdowns_dir = os.path.join(self.output_dir, "individual_breakdowns")
        self.similarity_dir = os.path.join(self.output_dir, "similarity_analysis")
        
        for directory in [self.videos_dir, self.frames_dir, self.breakdowns_dir, self.similarity_dir]:
            os.makedirs(directory, exist_ok=True)
    
    async def process_youtube_urls(self, 
                                 urls: List[str], 
                                 duration_seconds: int = 20,
                                 max_videos: int = 10,
                                 max_frames_per_video: int = 20,
                                 batch_size: int = 5) -> Dict[str, Any]:
        """
        Process multiple YouTube URLs: download, analyze, and compare.
        
        Args:
            urls (List[str]): List of YouTube URLs to process
            duration_seconds (int): Duration to analyze per video (default: 20)
            max_videos (int): Maximum number of videos to process (default: 10)
            max_frames_per_video (int): Maximum frames to extract per video (default: 20)
            batch_size (int): Batch size for parallel frame processing (default: 5)
            
        Returns:
            Dict[str, Any]: Complete processing results
        """
        start_time = time.time()
        
        print(f"🎬 Starting batch processing of {len(urls)} YouTube URLs")
        print(f"📊 Settings: {duration_seconds}s per video, max {max_frames_per_video} frames per video, max {max_videos} videos")
        print(f"📁 Output directory: {self.output_dir}")
        
        # Step 1: Download videos
        print(f"\n📥 Step 1: Downloading videos...")
        download_results = self.youtube_downloader.download_multiple_videos(
            urls, duration_seconds, max_videos
        )
        
        successful_downloads = [r for r in download_results if r['success']]
        if not successful_downloads:
            return {
                'success': False,
                'error': 'No videos were successfully downloaded',
                'download_results': download_results
            }
        
        print(f"✓ Downloaded {len(successful_downloads)} videos successfully")
        
        # Step 2: Process each video
        print(f"\n🔍 Step 2: Analyzing videos...")
        video_results = []
        
        for i, download_result in enumerate(successful_downloads, 1):
            print(f"\n--- Processing Video {i}/{len(successful_downloads)} ---")
            print(f"Title: {download_result['info']['title']}")
            
            video_result = await self.process_single_video(
                download_result, 
                duration_seconds,
                max_frames_per_video, 
                batch_size,
                video_index=i
            )
            video_results.append(video_result)
        
        # Step 3: Similarity analysis
        print(f"\n🔗 Step 3: Analyzing similarities...")
        similarity_result = await self.analyze_video_similarities(video_results)
        
        # Step 4: Generate comprehensive report
        print(f"\n📋 Step 4: Generating final report...")
        final_report = self.generate_final_report(
            download_results, 
            video_results, 
            similarity_result,
            start_time
        )
        
        # Save final report
        report_path = os.path.join(self.output_dir, "batch_analysis_report.json")
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(final_report, f, indent=2, ensure_ascii=False)
        
        processing_time = time.time() - start_time
        
        print(f"\n✅ Batch processing complete!")
        print(f"⏱️  Total time: {processing_time:.1f} seconds")
        print(f"📊 Videos processed: {len(successful_downloads)}")
        print(f"📁 Results saved in: {self.output_dir}")
        print(f"📋 Full report: {report_path}")
        
        return final_report
    
    async def process_single_video(self, 
                                 download_result: Dict[str, Any], 
                                 duration_seconds: int,
                                 max_frames_per_video: int,
                                 batch_size: int,
                                 video_index: int) -> Dict[str, Any]:
        """
        Process a single downloaded video.
        
        Args:
            download_result (Dict): Download result from YouTube downloader
            duration_seconds (int): Duration to analyze
            max_frames_per_video (int): Maximum frames to extract
            batch_size (int): Batch size for parallel processing
            video_index (int): Index of the video in the batch
            
        Returns:
            Dict[str, Any]: Processing result for the video
        """
        video_path = download_result['video_path']
        video_info = download_result['info']
        
        try:
            # Validate video file
            if not validate_video_file(video_path):
                return {
                    **download_result,
                    'breakdown_success': False,
                    'breakdown_error': 'Video file validation failed'
                }
            
            # Get detailed video info
            detailed_info = get_video_info(video_path)
            
            # Create video-specific directories
            video_id = video_info['id']
            video_frames_dir = os.path.join(self.frames_dir, f"video_{video_index}_{video_id}")
            os.makedirs(video_frames_dir, exist_ok=True)
            
            # Extract frames (fixed number evenly distributed)
            print(f"  📸 Extracting {max_frames_per_video} frames from first {duration_seconds}s...")
            extracted_frames = extract_fixed_frames(
                video_path=video_path,
                output_dir=video_frames_dir,
                max_frames=max_frames_per_video,
                max_duration=duration_seconds
            )
            
            if not extracted_frames:
                return {
                    **download_result,
                    'breakdown_success': False,
                    'breakdown_error': 'No frames were extracted'
                }
            
            print(f"  🤖 Analyzing {len(extracted_frames)} frames with GPT-4o...")
            
            # Analyze frames
            frame_analyses = await self.gpt_analyzer.analyze_multiple_frames_async(
                frame_data=extracted_frames,
                batch_size=batch_size,
                progress_callback=None  # Disable individual progress for batch
            )
            
            # Generate video summary
            print(f"  📝 Generating comprehensive summary...")
            video_summary = await self.gpt_analyzer.generate_comprehensive_summary(
                frame_analyses, detailed_info
            )
            
            # Calculate statistics
            successful_analyses = sum(1 for r in frame_analyses if r["success"])
            total_tokens = sum(r.get("tokens_used", 0) for r in frame_analyses if r["success"])
            if video_summary.get('success'):
                total_tokens += video_summary.get('tokens_used', 0)
            
            # Create breakdown data
            breakdown_data = {
                "metadata": {
                    "generated_at": datetime.now().isoformat(),
                    "video_file": video_path,
                    "video_info": detailed_info,
                    "youtube_info": video_info,
                    "processing_settings": {
                        "max_frames_per_video": max_frames_per_video,
                        "duration_seconds": duration_seconds,
                        "total_frames_extracted": len(extracted_frames),
                        "successful_analyses": successful_analyses,
                        "batch_size": batch_size,
                        "model_used": "gpt-4o",
                        "total_tokens_used": total_tokens
                    }
                },
                "frame_analyses": frame_analyses,
                "video_summary": video_summary
            }
            
            # Save individual breakdown
            breakdown_path = os.path.join(
                self.breakdowns_dir, 
                f"video_{video_index}_{video_id}_breakdown.json"
            )
            with open(breakdown_path, 'w', encoding='utf-8') as f:
                json.dump(breakdown_data, f, indent=2, ensure_ascii=False)
            
            print(f"  ✓ Analysis complete: {successful_analyses}/{len(extracted_frames)} frames, {total_tokens} tokens")
            
            return {
                **download_result,
                'breakdown_success': True,
                'breakdown_data': breakdown_data,
                'breakdown_path': breakdown_path,
                'frames_extracted': len(extracted_frames),
                'frames_analyzed': successful_analyses,
                'total_tokens': total_tokens,
                'video_index': video_index
            }
            
        except Exception as e:
            print(f"  ✗ Error processing video: {e}")
            return {
                **download_result,
                'breakdown_success': False,
                'breakdown_error': str(e)
            }
    
    async def analyze_video_similarities(self, video_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze similarities between processed videos.
        
        Args:
            video_results (List[Dict]): List of video processing results
            
        Returns:
            Dict[str, Any]: Similarity analysis results
        """
        try:
            # Main similarity analysis
            print("  🔗 Performing comprehensive similarity analysis...")
            similarity_result = await self.similarity_analyzer.analyze_similarities_async(video_results)
            
            # Pairwise comparisons
            print("  🔗 Generating pairwise comparisons...")
            pairwise_result = await self.similarity_analyzer.generate_pairwise_comparisons(video_results)
            
            # Combine results
            combined_result = {
                'comprehensive_analysis': similarity_result,
                'pairwise_comparisons': pairwise_result,
                'total_tokens_used': (
                    similarity_result.get('tokens_used', 0) + 
                    pairwise_result.get('total_tokens_used', 0)
                )
            }
            
            # Save similarity analysis
            similarity_path = os.path.join(self.similarity_dir, "similarity_analysis.json")
            save_similarity_results(combined_result, similarity_path)
            
            return combined_result
            
        except Exception as e:
            print(f"  ✗ Error in similarity analysis: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def generate_final_report(self, 
                            download_results: List[Dict[str, Any]],
                            video_results: List[Dict[str, Any]],
                            similarity_result: Dict[str, Any],
                            start_time: float) -> Dict[str, Any]:
        """
        Generate a comprehensive final report.
        
        Args:
            download_results (List[Dict]): Download results
            video_results (List[Dict]): Video processing results
            similarity_result (Dict): Similarity analysis results
            start_time (float): Processing start time
            
        Returns:
            Dict[str, Any]: Final comprehensive report
        """
        processing_time = time.time() - start_time
        successful_videos = [r for r in video_results if r.get('breakdown_success', False)]
        
        # Calculate total statistics
        total_frames_extracted = sum(r.get('frames_extracted', 0) for r in successful_videos)
        total_frames_analyzed = sum(r.get('frames_analyzed', 0) for r in successful_videos)
        total_tokens_used = sum(r.get('total_tokens', 0) for r in successful_videos)
        total_tokens_used += similarity_result.get('total_tokens_used', 0)
        
        report = {
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "processing_time_seconds": processing_time,
                "output_directory": self.output_dir
            },
            "summary": {
                "total_urls_provided": len(download_results),
                "successful_downloads": len([r for r in download_results if r['success']]),
                "successful_analyses": len(successful_videos),
                "total_frames_extracted": total_frames_extracted,
                "total_frames_analyzed": total_frames_analyzed,
                "total_tokens_used": total_tokens_used,
                "estimated_cost_usd": total_tokens_used * 0.000015  # Approximate cost
            },
            "download_results": download_results,
            "video_analyses": video_results,
            "similarity_analysis": similarity_result,
            "video_titles": [
                r.get('info', {}).get('title', 'Unknown') 
                for r in successful_videos
            ]
        }
        
        return report
    
    def cleanup(self):
        """Clean up temporary files."""
        try:
            self.youtube_downloader.cleanup_downloads()
            print("✓ Cleanup completed")
        except Exception as e:
            print(f"Warning: Cleanup failed: {e}")


def create_sample_urls_file():
    """Create a sample URLs file for testing."""
    sample_urls = [
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ",  # Rick Roll (example)
        "https://youtu.be/9bZkp7q19f0",  # Example short URL
        # Add more sample URLs here
    ]
    
    with open("sample_youtube_urls.txt", "w") as f:
        for url in sample_urls:
            f.write(f"{url}\n")
    
    print("Sample URLs file created: sample_youtube_urls.txt")


async def main_batch_demo():
    """Demo function for batch processing."""
    # Sample URLs for testing
    sample_urls = [
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "https://youtu.be/9bZkp7q19f0",
    ]
    
    processor = BatchVideoProcessor()
    
    try:
        result = await processor.process_youtube_urls(
            urls=sample_urls,
            duration_seconds=20,
            max_videos=10,
            frame_interval=2.0,  # Every 2 seconds
            batch_size=3
        )
        
        print("\n" + "="*50)
        print("BATCH PROCESSING COMPLETE")
        print("="*50)
        print(f"Videos processed: {result['summary']['successful_analyses']}")
        print(f"Total tokens used: {result['summary']['total_tokens_used']}")
        print(f"Estimated cost: ${result['summary']['estimated_cost_usd']:.3f}")
        
    except Exception as e:
        print(f"Error in batch processing: {e}")
    finally:
        processor.cleanup()


if __name__ == "__main__":
    # Run the demo
    asyncio.run(main_batch_demo())