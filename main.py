#!/usr/bin/env python3
"""
Video Visual Breakdown Tool

This tool extracts frames from a video file and uses OpenAI's GPT-4o Vision API
to analyze each frame, providing detailed descriptions of the visual content.
"""

import argparse
import asyncio
import json
import os
import sys
import time
from datetime import datetime
from dotenv import load_dotenv

from video_utils import extract_frames, validate_video_file, get_video_info
from gpt_utils import GPTVisionAnalyzer, test_api_connection


def setup_output_directories(base_output_dir: str = "outputs") -> tuple:
    """
    Create necessary output directories.
    
    Args:
        base_output_dir (str): Base output directory name
        
    Returns:
        tuple: (frames_dir, output_json_path)
    """
    # Create main output directory
    os.makedirs(base_output_dir, exist_ok=True)
    
    # Create frames subdirectory
    frames_dir = os.path.join(base_output_dir, "frames")
    os.makedirs(frames_dir, exist_ok=True)
    
    # Define output JSON path
    output_json_path = os.path.join(base_output_dir, "breakdown.json")
    
    return frames_dir, output_json_path


def save_results_to_json(results: list, output_path: str, video_info: dict, processing_info: dict, summary: dict = None):
    """
    Save analysis results to a JSON file with metadata.
    
    Args:
        results (list): List of frame analysis results
        output_path (str): Path to save the JSON file
        video_info (dict): Video file information
        processing_info (dict): Processing metadata
        summary (dict, optional): Comprehensive video summary
    """
    # Prepare the complete output structure
    output_data = {
        "metadata": {
            "generated_at": datetime.now().isoformat(),
            "video_file": processing_info["video_path"],
            "video_info": video_info,
            "processing_settings": {
                "frame_interval_seconds": processing_info["interval_seconds"],
                "total_frames_extracted": len(results),
                "batch_size": processing_info.get("batch_size", 1),
                "processing_time_seconds": processing_info.get("processing_time", 0),
                "model_used": "gpt-4o"
            }
        },
        "frame_analyses": results
    }
    
    # Add summary if provided
    if summary:
        output_data["video_summary"] = summary
    
    # Save to JSON file
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    print(f"Results saved to: {output_path}")


def progress_callback(current: int, total: int, result: dict):
    """
    Callback function to show progress during frame analysis.
    
    Args:
        current (int): Current frame number
        total (int): Total number of frames
        result (dict): Analysis result for current frame
    """
    percentage = (current / total) * 100
    status = "✓" if result["success"] else "✗"
    print(f"Progress: {status} {current}/{total} ({percentage:.1f}%)")


async def main():
    """
    Main function to orchestrate the video breakdown process.
    """
    # Load environment variables
    load_dotenv()
    
    # Set up command line arguments
    parser = argparse.ArgumentParser(
        description="Extract and analyze video frames using OpenAI GPT-4o Vision",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "video_path",
        help="Path to the input video file (.mp4)"
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=1.0,
        help="Interval between frames in seconds (default: 1.0)"
    )
    parser.add_argument(
        "--output-dir",
        default="outputs",
        help="Output directory for frames and results (default: outputs)"
    )
    parser.add_argument(
        "--api-key",
        help="OpenAI API key (if not set as environment variable)"
    )
    parser.add_argument(
        "--test-api",
        action="store_true",
        help="Test OpenAI API connection and exit"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=5,
        help="Number of frames to process in parallel (default: 5)"
    )
    parser.add_argument(
        "--no-summary",
        action="store_true",
        help="Skip generating comprehensive video summary"
    )
    
    args = parser.parse_args()
    
    # Test API connection if requested
    if args.test_api:
        success = test_api_connection(args.api_key)
        sys.exit(0 if success else 1)
    
    # Validate video file
    if not validate_video_file(args.video_path):
        print("Error: Invalid or inaccessible video file.")
        sys.exit(1)
    
    # Get video information
    try:
        video_info = get_video_info(args.video_path)
        print(f"Video Info: {video_info['resolution']}, {video_info['fps']:.2f} FPS, {video_info['duration_seconds']:.2f}s")
    except Exception as e:
        print(f"Error getting video info: {e}")
        sys.exit(1)
    
    # Setup output directories
    frames_dir, output_json_path = setup_output_directories(args.output_dir)
    
    # Extract frames from video
    print(f"\nExtracting frames every {args.interval} seconds...")
    try:
        extracted_frames = extract_frames(
            video_path=args.video_path,
            output_dir=frames_dir,
            interval_seconds=args.interval
        )
    except Exception as e:
        print(f"Error extracting frames: {e}")
        sys.exit(1)
    
    if not extracted_frames:
        print("No frames were extracted. Check your video file and try again.")
        sys.exit(1)
    
    # Initialize GPT Vision Analyzer
    print(f"\nInitializing OpenAI GPT-4o Vision analyzer...")
    try:
        analyzer = GPTVisionAnalyzer(api_key=args.api_key)
        
        # Test API connection
        if not test_api_connection(args.api_key):
            print("Failed to connect to OpenAI API. Please check your API key.")
            sys.exit(1)
            
    except Exception as e:
        print(f"Error initializing OpenAI client: {e}")
        print("Make sure you have set your OPENAI_API_KEY environment variable or provided --api-key")
        sys.exit(1)
    
    # Analyze frames with GPT-4o Vision (async parallel processing)
    print(f"\nAnalyzing {len(extracted_frames)} frames with GPT-4o Vision (parallel processing)...")
    print(f"Batch size: {args.batch_size} frames per batch")
    print("This will be much faster than sequential processing...")
    
    start_time = time.time()
    try:
        results = await analyzer.analyze_multiple_frames_async(
            frame_data=extracted_frames,
            batch_size=args.batch_size,
            progress_callback=progress_callback
        )
        processing_time = time.time() - start_time
    except Exception as e:
        print(f"Error during frame analysis: {e}")
        sys.exit(1)
    
    # Calculate statistics
    successful_analyses = sum(1 for r in results if r["success"])
    failed_analyses = len(results) - successful_analyses
    total_tokens = sum(r.get("tokens_used", 0) for r in results if r["success"])
    
    print(f"\nFrame Analysis Summary:")
    print(f"  Total frames: {len(results)}")
    print(f"  Successful analyses: {successful_analyses}")
    print(f"  Failed analyses: {failed_analyses}")
    print(f"  Total tokens used: {total_tokens}")
    print(f"  Processing time: {processing_time:.1f} seconds")
    print(f"  Average time per frame: {processing_time/len(results):.1f} seconds")
    
    # Generate comprehensive video summary
    summary_result = None
    if not args.no_summary and successful_analyses > 0:
        print(f"\nGenerating comprehensive video summary...")
        try:
            summary_result = await analyzer.generate_comprehensive_summary(results, video_info)
            if summary_result["success"]:
                print(f"✓ Video summary generated successfully ({summary_result['tokens_used']} tokens)")
                total_tokens += summary_result['tokens_used']
            else:
                print(f"✗ Failed to generate summary: {summary_result['error']}")
        except Exception as e:
            print(f"✗ Error generating summary: {e}")
    
    # Save results to JSON
    processing_info = {
        "video_path": args.video_path,
        "interval_seconds": args.interval,
        "batch_size": args.batch_size,
        "processing_time": processing_time,
        "total_tokens_used": total_tokens
    }
    
    try:
        save_results_to_json(results, output_json_path, video_info, processing_info, summary_result)
    except Exception as e:
        print(f"Error saving results: {e}")
        sys.exit(1)
    
    print(f"\n✓ Video breakdown complete!")
    print(f"  Frames saved in: {frames_dir}")
    print(f"  Results saved in: {output_json_path}")
    if summary_result and summary_result["success"]:
        print(f"  Video summary included in results")
    print(f"  Total cost estimate: ~${total_tokens * 0.000015:.3f} (approximate)")


async def main_async():
    """
    Async wrapper for the main function.
    """
    await main()


if __name__ == "__main__":
    asyncio.run(main_async()) 