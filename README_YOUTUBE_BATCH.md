# YouTube Batch Video Analyzer

This tool extends the original visual breakdown tool to analyze multiple YouTube videos and compare their similarities using AI.

## Features

- 📥 **Download up to 10 YouTube videos** automatically
- ⏱️ **Analyze first 20 seconds** of each video (configurable)
- 🖼️ **Frame-by-frame visual analysis** using GPT-4o Vision
- 🔗 **AI-powered similarity analysis** comparing all videos
- 📊 **Comprehensive reporting** with detailed insights
- 🚀 **Parallel processing** for faster analysis

## Quick Start

### 1. Install Dependencies

```bash
# Install new dependencies
pip install -r requirements.txt
```

### 2. Set up OpenAI API Key

```bash
# Option 1: Environment variable (recommended)
export OPENAI_API_KEY="your-api-key-here"

# Option 2: Create .env file
echo "OPENAI_API_KEY=your-api-key-here" > .env
```

### 3. Run the Analyzer

```bash
# Interactive mode (easiest for beginners)
python youtube_batch_analyzer.py --interactive

# Direct URLs
python youtube_batch_analyzer.py --urls "https://youtu.be/abc123" "https://youtu.be/def456"

# From file
python youtube_batch_analyzer.py --urls-file my_urls.txt
```

## Usage Examples

### Interactive Mode

```bash
python youtube_batch_analyzer.py --interactive
```

This will guide you through entering URLs manually.

### Multiple URLs at Once

```bash
python youtube_batch_analyzer.py --urls \
  "https://www.youtube.com/watch?v=dQw4w9WgXcQ" \
  "https://youtu.be/9bZkp7q19f0" \
  "https://www.youtube.com/watch?v=oHg5SJYRHA0"
```

### From File

```bash
# Create URLs file
echo "https://youtu.be/abc123" > my_urls.txt
echo "https://youtu.be/def456" >> my_urls.txt

# Process from file
python youtube_batch_analyzer.py --urls-file my_urls.txt
```

### Advanced Options

```bash
python youtube_batch_analyzer.py \
  --urls-file my_urls.txt \
  --duration 30 \
  --interval 0.5 \
  --batch-size 3 \
  --output-dir my_analysis \
  --yes
```

## Command Line Options

### Required (choose one):

- `--urls URL1 URL2 ...` - Direct YouTube URLs
- `--urls-file FILE` - Text file with URLs (one per line)
- `--interactive` - Interactive mode to enter URLs

### Optional:

- `--duration SECONDS` - Duration to analyze per video (default: 20)
- `--interval SECONDS` - Frame extraction interval (default: 1.0)
- `--max-videos N` - Maximum videos to process (default: 10)
- `--batch-size N` - Parallel frame processing (default: 5)
- `--output-dir DIR` - Output directory (default: batch_outputs)
- `--api-key KEY` - OpenAI API key (if not in env)
- `--yes` - Skip confirmation prompts
- `--no-cleanup` - Keep temporary files
- `--test-api` - Test API connection only

## Output Structure

The tool creates a comprehensive output directory:

```
batch_outputs/
├── batch_analysis_report.json      # Complete analysis report
├── downloaded_videos/              # Original downloaded videos
├── frames/                         # Extracted frames per video
│   ├── video_1_abc123/
│   └── video_2_def456/
├── individual_breakdowns/          # Per-video analysis
│   ├── video_1_abc123_breakdown.json
│   └── video_2_def456_breakdown.json
└── similarity_analysis/            # Cross-video comparisons
    └── similarity_analysis.json
```

## What the Analysis Includes

### Per-Video Analysis:

- Frame-by-frame visual descriptions
- Comprehensive video summary
- Technical metadata (resolution, FPS, etc.)
- Processing statistics

### Similarity Analysis:

- Overall similarity assessment (1-10 scale)
- Common themes and patterns
- Content categorization
- Visual and production similarities
- Thematic clustering
- Key differences and unique aspects

## URL File Format

Create a text file with one YouTube URL per line:

```
# This is a comment (lines starting with # are ignored)
https://www.youtube.com/watch?v=dQw4w9WgXcQ
https://youtu.be/9bZkp7q19f0
https://www.youtube.com/watch?v=oHg5SJYRHA0

# Another comment
https://youtu.be/another_video_id
```

## Supported YouTube URL Formats

- `https://www.youtube.com/watch?v=VIDEO_ID`
- `https://youtu.be/VIDEO_ID`
- `https://www.youtube.com/embed/VIDEO_ID`
- `https://www.youtube.com/v/VIDEO_ID`
- `https://www.youtube.com/shorts/VIDEO_ID`

## Cost Estimation

The tool uses OpenAI's GPT-4o model. Approximate costs:

- **Per frame analysis**: ~$0.01-0.02
- **Video summary**: ~$0.02-0.05
- **Similarity analysis**: ~$0.05-0.10

**Example**: 3 videos × 20 frames each ≈ $1.50-3.00 total

## Tips for Best Results

1. **Start small**: Try 2-3 videos first to understand the output
2. **Choose related content**: Videos with some similarities provide more interesting comparisons
3. **Adjust frame interval**: Use `--interval 2.0` for longer videos to reduce cost
4. **Check API limits**: Ensure your OpenAI account has sufficient credits

## Troubleshooting

### Common Issues:

**API Connection Failed**

```bash
# Test your API key
python youtube_batch_analyzer.py --test-api
```

**Video Download Failed**

- Check if the video is public and available
- Some age-restricted or region-locked videos may fail
- Try with different videos

**Out of Memory**

- Reduce `--batch-size` (try 2-3)
- Increase `--interval` to process fewer frames

**High Costs**

- Use `--duration 10` for shorter analysis
- Increase `--interval 2.0` for fewer frames
- Process fewer videos at once

## Advanced Usage

### Custom Analysis Pipeline

For advanced users, you can use the modules directly:

```python
from batch_processor import BatchVideoProcessor

processor = BatchVideoProcessor()
result = await processor.process_youtube_urls(
    urls=["https://youtu.be/abc123"],
    duration_seconds=15,
    frame_interval=2.0
)
```

### Integration with Existing Code

The new modules are designed to work alongside the original `main.py`:

- `youtube_utils.py` - YouTube downloading
- `similarity_analyzer.py` - LLM-based comparisons
- `batch_processor.py` - Orchestrates the entire pipeline
- `youtube_batch_analyzer.py` - User-friendly CLI interface

## Development

### Adding New Features

The modular design makes it easy to extend:

- Add new similarity metrics in `similarity_analyzer.py`
- Extend video sources beyond YouTube in `youtube_utils.py`
- Add new visualization options in `batch_processor.py`

### Testing

```bash
# Create sample files for testing
python youtube_batch_analyzer.py --create-samples

# Test with sample URLs
python youtube_batch_analyzer.py --urls-file sample_urls.txt
```
