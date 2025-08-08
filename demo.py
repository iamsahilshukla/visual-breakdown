#!/usr/bin/env python3
"""
Demo script for YouTube Batch Video Analyzer

This script demonstrates how to use the new YouTube batch analysis functionality.
"""

import asyncio
import os
from dotenv import load_dotenv

# Import our new modules
from batch_processor import BatchVideoProcessor
from youtube_utils import YouTubeDownloader
from similarity_analyzer import VideoSimilarityAnalyzer


async def demo_basic_functionality():
    """Demonstrate basic functionality with sample URLs."""
    
    print("🎬 YouTube Batch Video Analyzer Demo")
    print("="*50)
    
    # Load environment variables
    load_dotenv()
    
    # Check if API key is available
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("❌ OPENAI_API_KEY not found in environment variables")
        print("Please set your OpenAI API key:")
        print("export OPENAI_API_KEY='your-key-here'")
        return
    
    # Sample YouTube URLs for demonstration
    # Note: Replace these with actual working YouTube URLs
    sample_urls = [
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ",  # Rick Roll
        "https://youtu.be/9bZkp7q19f0",  # Another example
    ]
    
    print(f"📋 Demo URLs:")
    for i, url in enumerate(sample_urls, 1):
        print(f"  {i}. {url}")
    
    # Demonstrate URL validation
    print(f"\n🔍 Step 1: Validating URLs...")
    downloader = YouTubeDownloader()
    valid_urls, invalid_urls = downloader.validate_urls(sample_urls)
    
    print(f"✅ Valid URLs: {len(valid_urls)}")
    print(f"❌ Invalid URLs: {len(invalid_urls)}")
    
    if invalid_urls:
        print("Invalid URLs found:")
        for url in invalid_urls:
            print(f"  - {url}")
    
    # Initialize batch processor
    print(f"\n🚀 Step 2: Initializing Batch Processor...")
    processor = BatchVideoProcessor(
        api_key=api_key,
        output_dir="demo_outputs"
    )
    
    print("✅ Batch processor initialized")
    print("📁 Output directory: demo_outputs")
    
    # Note: Actual processing would happen here
    print(f"\n💡 To run full analysis, use:")
    print(f"python youtube_batch_analyzer.py --urls {' '.join(f'"{url}"' for url in sample_urls)}")
    
    print(f"\n🎯 What the full analysis would do:")
    print("1. Download first 20 seconds of each video")
    print("2. Extract exactly 20 frames evenly distributed across duration") 
    print("3. Analyze each frame with GPT-4o Vision")
    print("4. Generate comprehensive video summaries")
    print("5. Compare all videos for similarities")
    print("6. Create detailed reports and insights")
    
    print(f"\n📊 Expected output structure:")
    print("demo_outputs/")
    print("├── batch_analysis_report.json")
    print("├── downloaded_videos/")
    print("├── frames/")
    print("├── individual_breakdowns/")
    print("└── similarity_analysis/")


def demo_url_validation():
    """Demonstrate URL validation functionality."""
    
    print("\n🔍 URL Validation Demo")
    print("="*30)
    
    test_urls = [
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ",  # Valid
        "https://youtu.be/9bZkp7q19f0",                # Valid
        "https://youtube.com/shorts/abc123",           # Valid
        "https://example.com/not-youtube",             # Invalid
        "not-a-url-at-all",                           # Invalid
        "",                                            # Invalid
    ]
    
    downloader = YouTubeDownloader()
    
    for url in test_urls:
        is_valid = downloader.is_valid_youtube_url(url)
        status = "✅ Valid" if is_valid else "❌ Invalid"
        print(f"{status}: {url if url else '(empty)'}")


def create_sample_urls_file():
    """Create a sample URLs file for testing."""
    
    sample_content = """# Sample YouTube URLs for testing
# Replace these with actual YouTube URLs you want to analyze

https://www.youtube.com/watch?v=dQw4w9WgXcQ
https://youtu.be/9bZkp7q19f0

# Add more URLs here (max 10 will be processed)
# Lines starting with # are ignored
"""
    
    filename = "sample_urls.txt"
    with open(filename, "w") as f:
        f.write(sample_content)
    
    print(f"📄 Created {filename}")
    print("Edit this file with your YouTube URLs, then run:")
    print(f"python youtube_batch_analyzer.py --urls-file {filename}")


def show_usage_examples():
    """Show usage examples for the tool."""
    
    print("\n📚 Usage Examples")
    print("="*30)
    
    examples = [
        {
            "title": "Interactive Mode (Easiest)",
            "command": "python youtube_batch_analyzer.py --interactive",
            "description": "Guides you through entering URLs manually"
        },
        {
            "title": "Direct URLs",
            "command": 'python youtube_batch_analyzer.py --urls "https://youtu.be/abc123" "https://youtu.be/def456"',
            "description": "Process specific URLs directly"
        },
        {
            "title": "From File",
            "command": "python youtube_batch_analyzer.py --urls-file my_urls.txt",
            "description": "Read URLs from a text file"
        },
        {
            "title": "Custom Settings",
            "command": "python youtube_batch_analyzer.py --urls-file urls.txt --duration 30 --max-frames 15",
            "description": "Analyze 30 seconds with exactly 15 frames per video"
        },
        {
            "title": "Test API Connection",
            "command": "python youtube_batch_analyzer.py --test-api",
            "description": "Verify your OpenAI API key works"
        }
    ]
    
    for i, example in enumerate(examples, 1):
        print(f"\n{i}. {example['title']}")
        print(f"   {example['description']}")
        print(f"   Command: {example['command']}")


async def main():
    """Main demo function."""
    
    print("🎬 YouTube Batch Video Analyzer")
    print("🔧 Demo & Setup Script")
    print("="*50)
    
    # Show what this tool does
    print("\n✨ This tool can:")
    print("• Download up to 10 YouTube videos (first 20 seconds each)")
    print("• Extract exactly 20 frames per video (evenly distributed)")
    print("• Analyze each frame with AI (GPT-4o Vision)")
    print("• Generate detailed descriptions and summaries")
    print("• Compare videos and find similarities")
    print("• Create comprehensive reports")
    
    # Basic validation demo
    demo_url_validation()
    
    # Show usage examples
    show_usage_examples()
    
    # Create sample files
    print(f"\n📁 Setting up sample files...")
    create_sample_urls_file()
    
    # Demo basic functionality
    await demo_basic_functionality()
    
    print(f"\n🎯 Next Steps:")
    print("1. Set your OpenAI API key: export OPENAI_API_KEY='your-key-here'")
    print("2. Install dependencies: pip install -r requirements.txt") 
    print("3. Edit sample_urls.txt with real YouTube URLs")
    print("4. Run: python youtube_batch_analyzer.py --urls-file sample_urls.txt")
    
    print(f"\n💡 Tips:")
    print("• Start with 2-3 videos to understand the output")
    print("• Use --test-api to verify your API key")
    print("• Check costs: ~$1-3 for analyzing 3 short videos")


if __name__ == "__main__":
    asyncio.run(main())