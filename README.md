# Video Visual Breakdown Tool

A Python tool that extracts frames from video files and uses OpenAI's GPT-4o Vision API to provide detailed visual analysis of each frame.

## Features

- **Video Frame Extraction**: Extract frames from MP4 videos at customizable intervals
- **AI-Powered Analysis**: Use GPT-4o Vision to analyze visual content with structured prompts
- **⚡ Parallel Processing**: Async batch processing for 3-5x faster analysis
- **🎯 Comprehensive Summary**: AI-generated video summary based on all frame analyses
- **Structured Output**: Save detailed frame analyses as JSON with metadata
- **Modular Design**: Clean separation between video processing, API interaction, and orchestration
- **Progress Tracking**: Real-time progress updates during frame analysis
- **Cost Optimization**: Configurable batch sizes and processing options
- **Error Handling**: Comprehensive error handling and validation

## Project Structure

```
visual-breakdown/
├── main.py              # Main orchestration script
├── video_utils.py       # Video processing and frame extraction
├── gpt_utils.py         # OpenAI API interaction utilities
├── requirements.txt     # Python dependencies
├── .env.example        # Environment variable template
├── README.md           # This file
└── outputs/            # Generated output directory
    ├── frames/         # Extracted video frames
    └── breakdown.json  # Analysis results
```

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set Up OpenAI API Key

1. Get your API key from [OpenAI Platform](https://platform.openai.com/api-keys)
2. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```
3. Edit `.env` and replace `your_openai_api_key_here` with your actual API key

### 3. Prepare Your Video

Ensure you have an MP4 video file ready for analysis.

## Usage

### Basic Usage

```bash
python main.py path/to/your/video.mp4
```

### Advanced Options

```bash
python main.py path/to/your/video.mp4 \
    --interval 2.0 \
    --batch-size 10 \
    --output-dir my_analysis \
    --api-key your_api_key_here
```

### Command Line Options

- `video_path`: Path to the input MP4 video file (required)
- `--interval`: Interval between extracted frames in seconds (default: 1.0)
- `--batch-size`: Number of frames to process in parallel (default: 5)
- `--output-dir`: Output directory for frames and results (default: "outputs")
- `--api-key`: OpenAI API key (optional if set in .env file)
- `--no-summary`: Skip generating comprehensive video summary
- `--test-api`: Test OpenAI API connection and exit

### Testing API Connection

Before processing a video, you can test your API connection:

```bash
python main.py --test-api
```

## Output Format

The tool generates a JSON file with the following structure:

```json
{
  "metadata": {
    "generated_at": "2024-01-15T10:30:00.000000",
    "video_file": "path/to/video.mp4",
    "video_info": {
      "fps": 30.0,
      "total_frames": 900,
      "duration_seconds": 30.0,
      "width": 1920,
      "height": 1080,
      "resolution": "1920x1080"
    },
    "processing_settings": {
      "frame_interval_seconds": 1.0,
      "total_frames_extracted": 30,
      "batch_size": 5,
      "processing_time_seconds": 45.2,
      "model_used": "gpt-4o"
    }
  },
  "frame_analyses": [
    {
      "timestamp": 0.0,
      "frame_path": "outputs/frames/frame_0.00s.jpg",
      "frame_number": 1,
      "success": true,
      "description": "**Scene Overview** – A person is...",
      "tokens_used": 245,
      "model": "gpt-4o"
    }
  ],
  "video_summary": {
    "success": true,
    "summary": "**Overall Video Summary** – This is a tutorial video...",
    "tokens_used": 456,
    "frames_analyzed": 30,
    "model": "gpt-4o"
  }
}
```

## Analysis Structure

Each frame is analyzed using the following structured approach:

1. **Scene Overview** – What's happening overall? Any visible action or focus?
2. **Key Visual Elements** – Important elements like people, objects, text, gestures, expressions
3. **Environment & Mood** – Indoor/outdoor, lighting, atmosphere, tone
4. **Possible Context or Purpose** – Inferred purpose based on visual clues

## Examples

### Example 1: Analyze a video with 2-second intervals

```bash
python main.py demo_video.mp4 --interval 2.0
```

### Example 2: Custom output directory

```bash
python main.py lecture_video.mp4 --output-dir lecture_analysis --interval 5.0
```

### Example 3: High-speed processing with large batches

```bash
python main.py presentation.mp4 --batch-size 15 --interval 3.0
```

### Example 4: Skip summary generation for faster processing

```bash
python main.py long_video.mp4 --no-summary --batch-size 10
```

## Performance & Cost Considerations

### Speed Improvements

- **Parallel Processing**: 3-5x faster than sequential processing
- **Configurable Batch Size**: Balance speed vs. API rate limits
- **Async Architecture**: Non-blocking I/O for optimal throughput

### Cost Management

- GPT-4o Vision API charges per token and image
- Each frame analysis typically uses 200-400 tokens
- Video summary adds ~300-600 tokens
- A 60-second video (60 frames at 1s intervals) costs approximately $1-2
- Use larger intervals (e.g., 5-10 seconds) for longer videos
- Use `--no-summary` to save ~25% on token costs

## Error Handling

The tool includes comprehensive error handling for:

- Invalid video files
- API connection issues
- Missing API keys
- File system errors
- Network timeouts

## Troubleshooting

### Common Issues

1. **"Could not open video file"**

   - Ensure the video file exists and is a valid MP4
   - Check file permissions

2. **"OpenAI API connection failed"**

   - Verify your API key is correct
   - Check your internet connection
   - Ensure you have sufficient API credits

3. **"No frames were extracted"**
   - Check if the video duration is longer than your interval
   - Verify the video file is not corrupted

### Debug Mode

For detailed debugging, you can modify the logging level in the source code or add print statements as needed.

## Requirements

- Python 3.7+
- OpenCV for video processing
- OpenAI Python library
- Valid OpenAI API key with GPT-4o access
- Sufficient API credits for your video length

## License

This project is open source. Feel free to modify and distribute as needed.

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests to improve the tool.
