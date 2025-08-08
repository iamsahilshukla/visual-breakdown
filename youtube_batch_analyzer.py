#!/usr/bin/env python3
"""
YouTube Batch Video Analyzer

This tool takes multiple YouTube URLs, downloads the first 20 seconds of each video,
performs visual breakdown analysis, and analyzes similarities between them using LLM.

Usage examples:
  python youtube_batch_analyzer.py --urls "url1" "url2" "url3"
  python youtube_batch_analyzer.py --urls-file urls.txt
  python youtube_batch_analyzer.py --interactive
"""

import argparse
import asyncio
import sys
import os
from typing import List
from dotenv import load_dotenv

from batch_processor import BatchVideoProcessor
from gpt_utils import test_api_connection


def read_urls_from_file(file_path: str) -> List[str]:
    """
    Read YouTube URLs from a text file.
    
    Args:
        file_path (str): Path to the file containing URLs
        
    Returns:
        List[str]: List of URLs
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            urls = [line.strip() for line in f.readlines()]
            # Filter out empty lines and comments
            urls = [url for url in urls if url and not url.startswith('#')]
            return urls
    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found.")
        return []
    except Exception as e:
        print(f"Error reading file '{file_path}': {e}")
        return []


def interactive_mode() -> List[str]:
    """
    Interactive mode to collect YouTube URLs from user input.
    
    Returns:
        List[str]: List of URLs entered by user
    """
    print("\n🎬 YouTube Batch Analyzer - Interactive Mode")
    print("="*50)
    print("Enter YouTube URLs one by one (press Enter after each URL)")
    print("Type 'done' when finished, or 'quit' to exit")
    print("Maximum 10 videos will be processed")
    
    urls = []
    
    while len(urls) < 10:
        try:
            url = input(f"\nURL {len(urls) + 1} (or 'done'): ").strip()
            
            if url.lower() in ['done', 'quit', 'exit']:
                break
            
            if url:
                urls.append(url)
                print(f"✓ Added: {url}")
            
        except KeyboardInterrupt:
            print("\n\nOperation cancelled by user.")
            sys.exit(0)
    
    if not urls:
        print("No URLs provided. Exiting.")
        sys.exit(0)
    
    print(f"\n📋 Collected {len(urls)} URLs for processing")
    return urls


def validate_and_confirm_settings(urls: List[str], args) -> bool:
    """
    Display settings and ask for confirmation.
    
    Args:
        urls (List[str]): List of URLs to process
        args: Command line arguments
        
    Returns:
        bool: True if user confirms, False otherwise
    """
    print("\n📊 Processing Settings:")
    print("="*30)
    print(f"Number of videos: {len(urls)}")
    print(f"Duration per video: {args.duration} seconds")
    print(f"Max frames per video: {args.max_frames}")
    print(f"Batch size: {args.batch_size}")
    print(f"Output directory: {args.output_dir}")
    
    print("\n🎬 Videos to process:")
    for i, url in enumerate(urls, 1):
        print(f"  {i}. {url}")
    
    if not args.yes:
        try:
            confirm = input("\nProceed with analysis? [y/N]: ").strip().lower()
            return confirm in ['y', 'yes']
        except KeyboardInterrupt:
            print("\n\nOperation cancelled by user.")
            return False
    
    return True


async def main():
    """
    Main function to orchestrate the YouTube batch analysis.
    """
    # Load environment variables
    load_dotenv()
    
    # Set up command line arguments
    parser = argparse.ArgumentParser(
        description="Analyze multiple YouTube videos and compare their visual content",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python youtube_batch_analyzer.py --urls "https://youtu.be/abc123" "https://youtu.be/def456"
  python youtube_batch_analyzer.py --urls-file my_urls.txt --max-frames 20
  python youtube_batch_analyzer.py --interactive
  
URL File Format:
  One URL per line, lines starting with # are ignored
        """
    )
    
    # URL input options (mutually exclusive)
    url_group = parser.add_mutually_exclusive_group(required=True)
    url_group.add_argument(
        "--urls",
        nargs="+",
        help="YouTube URLs to process (space-separated)"
    )
    url_group.add_argument(
        "--urls-file",
        help="Text file containing YouTube URLs (one per line)"
    )
    url_group.add_argument(
        "--interactive",
        action="store_true",
        help="Interactive mode to enter URLs manually"
    )
    
    # Processing options
    parser.add_argument(
        "--duration",
        type=int,
        default=20,
        help="Duration to analyze per video in seconds (default: 20)"
    )
    parser.add_argument(
        "--max-frames",
        type=int,
        default=20,
        help="Maximum frames to extract per video (default: 20)"
    )
    parser.add_argument(
        "--max-videos",
        type=int,
        default=10,
        help="Maximum number of videos to process (default: 10)"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=5,
        help="Number of frames to process in parallel (default: 5)"
    )
    parser.add_argument(
        "--output-dir",
        default="batch_outputs",
        help="Output directory for all results (default: batch_outputs)"
    )
    
    # API and misc options
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
        "--yes", "-y",
        action="store_true",
        help="Skip confirmation prompts"
    )
    parser.add_argument(
        "--no-cleanup",
        action="store_true",
        help="Don't clean up temporary files after processing"
    )
    
    args = parser.parse_args()
    
    # Test API connection if requested
    if args.test_api:
        success = test_api_connection(args.api_key)
        sys.exit(0 if success else 1)
    
    # Get URLs based on input method
    if args.urls:
        urls = args.urls
    elif args.urls_file:
        urls = read_urls_from_file(args.urls_file)
        if not urls:
            sys.exit(1)
    elif args.interactive:
        urls = interactive_mode()
    else:
        print("Error: No URL input method specified.")
        sys.exit(1)
    
    # Validate settings and get confirmation
    if not validate_and_confirm_settings(urls, args):
        print("Operation cancelled.")
        sys.exit(0)
    
    # Test API connection
    print("\n🔑 Testing OpenAI API connection...")
    if not test_api_connection(args.api_key):
        print("Failed to connect to OpenAI API. Please check your API key.")
        sys.exit(1)
    
    # Initialize batch processor
    processor = BatchVideoProcessor(
        api_key=args.api_key,
        output_dir=args.output_dir
    )
    
    try:
        # Process all videos
        result = await processor.process_youtube_urls(
            urls=urls,
            duration_seconds=args.duration,
            max_videos=args.max_videos,
            max_frames_per_video=args.max_frames,
            batch_size=args.batch_size
        )
        
        # Display final results
        print("\n" + "="*60)
        print("🎉 BATCH ANALYSIS COMPLETE")
        print("="*60)
        
        if result.get('success', False) or result.get('summary'):
            summary = result.get('summary', {})
            print(f"📊 Videos processed: {summary.get('successful_analyses', 0)}")
            print(f"🖼️  Total frames analyzed: {summary.get('total_frames_analyzed', 0)}")
            print(f"🤖 Total tokens used: {summary.get('total_tokens_used', 0)}")
            print(f"💰 Estimated cost: ${summary.get('estimated_cost_usd', 0):.3f}")
            
            # Show similarity insights if available
            similarity = result.get('similarity_analysis', {})
            if similarity.get('comprehensive_analysis', {}).get('success'):
                print(f"\n🔗 Similarity Analysis:")
                print(f"   Videos compared: {similarity['comprehensive_analysis'].get('videos_compared', 0)}")
                
            print(f"\n📁 All results saved in: {args.output_dir}")
            print(f"📋 Full report: {args.output_dir}/batch_analysis_report.json")
            
        else:
            print(f"❌ Analysis failed: {result.get('error', 'Unknown error')}")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n\n⏹️  Processing interrupted by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error during processing: {e}")
        sys.exit(1)
    finally:
        # Cleanup unless disabled
        if not args.no_cleanup:
            processor.cleanup()


def create_sample_files():
    """Create sample configuration files for users."""
    # Sample URLs file
    sample_urls_content = """# Sample YouTube URLs for batch analysis
# Lines starting with # are ignored
# Add your YouTube URLs below (one per line)

https://www.youtube.com/watch?v=dQw4w9WgXcQ
https://youtu.be/9bZkp7q19f0

# Add more URLs here...
"""
    
    with open("sample_urls.txt", "w") as f:
        f.write(sample_urls_content)
    
    print("Created sample_urls.txt - Edit this file with your YouTube URLs")


if __name__ == "__main__":
    # Check if user wants to create sample files
    if len(sys.argv) == 2 and sys.argv[1] == "--create-samples":
        create_sample_files()
        sys.exit(0)
    
    # Run the main application
    asyncio.run(main())