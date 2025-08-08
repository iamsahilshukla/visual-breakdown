import base64
import os
import asyncio
from typing import Dict, Any, List
from openai import AsyncOpenAI, OpenAI


# The structured prompt for frame analysis
FRAME_ANALYSIS_PROMPT = """
You are an AI assistant analyzing individual frames from a video. Each frame is provided to you as an image.

Your task is to describe each frame in rich detail using the following structure:

1. **Scene Overview** – What's happening overall? Is there any visible action or focus?
2. **Key Visual Elements** – List and describe any important elements in the frame (e.g. people, objects, background details, text on screen, gestures, facial expressions).
3. **Environment & Mood** – Is it indoors or outdoors? What does the lighting feel like (e.g., bright, dim, moody, warm, natural)? Describe the tone or atmosphere (e.g., relaxed, tense, professional, friendly).
4. **Possible Context or Purpose** – Based on visual clues, infer the purpose of this moment (e.g. part of a tutorial, vlog intro, dramatic moment, product demo, conversation scene, public setting, etc.).

Instructions:
- Avoid generic phrases like "This is a picture of..." — be direct and descriptive.
- Keep the response well-structured and easy to read.
- Be concise but insightful, and only describe what is visible in the image.

Do not speculate about anything not present in the frame.
"""


class GPTVisionAnalyzer:
    """
    A class to handle OpenAI GPT-4o Vision API interactions for frame analysis.
    """
    
    def __init__(self, api_key: str = None):
        """
        Initialize the GPT Vision Analyzer.
        
        Args:
            api_key (str, optional): OpenAI API key. If None, will use OPENAI_API_KEY env var.
        """
        if api_key:
            self.client = OpenAI(api_key=api_key)
            self.async_client = AsyncOpenAI(api_key=api_key)
        else:
            # Will use OPENAI_API_KEY environment variable
            self.client = OpenAI()
            self.async_client = AsyncOpenAI()
    
    def encode_image_to_base64(self, image_path: str) -> str:
        """
        Encode an image file to base64 string.
        
        Args:
            image_path (str): Path to the image file
            
        Returns:
            str: Base64 encoded image string
        """
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image file not found: {image_path}")
        
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    
    def analyze_frame(self, image_path: str, custom_prompt: str = None) -> Dict[str, Any]:
        """
        Analyze a single frame using GPT-4o Vision.
        
        Args:
            image_path (str): Path to the image file
            custom_prompt (str, optional): Custom prompt for analysis. Uses default if None.
            
        Returns:
            Dict[str, Any]: Analysis result with description and metadata
        """
        try:
            # Encode image to base64
            base64_image = self.encode_image_to_base64(image_path)
            
            # Use custom prompt or default
            prompt = custom_prompt if custom_prompt else FRAME_ANALYSIS_PROMPT
            
            # Make API call to GPT-4o Vision
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": prompt
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=1000
            )
            
            # Extract the analysis result
            analysis = response.choices[0].message.content
            
            return {
                "success": True,
                "description": analysis,
                "tokens_used": response.usage.total_tokens,
                "model": "gpt-4o"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "description": f"Error analyzing frame: {str(e)}"
            }
    
    def analyze_multiple_frames(self, frame_data: list, progress_callback=None) -> list:
        """
        Analyze multiple frames in sequence.
        
        Args:
            frame_data (list): List of (timestamp, frame_path) tuples
            progress_callback (callable, optional): Function to call with progress updates
            
        Returns:
            list: List of analysis results
        """
        results = []
        total_frames = len(frame_data)
        
        for i, (timestamp, frame_path) in enumerate(frame_data):
            print(f"Analyzing frame {i+1}/{total_frames}: {frame_path}")
            
            # Analyze the frame
            analysis_result = self.analyze_frame(frame_path)
            
            # Add metadata
            result = {
                "timestamp": timestamp,
                "frame_path": frame_path,
                "frame_number": i + 1,
                **analysis_result
            }
            
            results.append(result)
            
            # Call progress callback if provided
            if progress_callback:
                progress_callback(i + 1, total_frames, result)
            
            # Print brief status
            if analysis_result["success"]:
                print(f"✓ Frame {i+1} analyzed successfully")
            else:
                print(f"✗ Frame {i+1} analysis failed: {analysis_result['error']}")
        
        return results
    
    async def analyze_frame_async(self, image_path: str, custom_prompt: str = None) -> Dict[str, Any]:
        """
        Analyze a single frame using GPT-4o Vision asynchronously.
        
        Args:
            image_path (str): Path to the image file
            custom_prompt (str, optional): Custom prompt for analysis. Uses default if None.
            
        Returns:
            Dict[str, Any]: Analysis result with description and metadata
        """
        try:
            # Encode image to base64
            base64_image = self.encode_image_to_base64(image_path)
            
            # Use custom prompt or default
            prompt = custom_prompt if custom_prompt else FRAME_ANALYSIS_PROMPT
            
            # Make async API call to GPT-4o Vision
            response = await self.async_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": prompt
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=1000
            )
            
            # Extract the analysis result
            analysis = response.choices[0].message.content
            
            return {
                "success": True,
                "description": analysis,
                "tokens_used": response.usage.total_tokens,
                "model": "gpt-4o"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "description": f"Error analyzing frame: {str(e)}"
            }
    
    async def analyze_multiple_frames_async(self, frame_data: list, batch_size: int = 5, progress_callback=None) -> list:
        """
        Analyze multiple frames in parallel batches asynchronously.
        
        Args:
            frame_data (list): List of (timestamp, frame_path) tuples
            batch_size (int): Number of frames to process in parallel (default: 5)
            progress_callback (callable, optional): Function to call with progress updates
            
        Returns:
            list: List of analysis results
        """
        results = []
        total_frames = len(frame_data)
        
        # Process frames in batches
        for i in range(0, total_frames, batch_size):
            batch = frame_data[i:i + batch_size]
            batch_tasks = []
            
            # Create async tasks for the batch
            for j, (timestamp, frame_path) in enumerate(batch):
                task = self.analyze_frame_async(frame_path)
                batch_tasks.append((timestamp, frame_path, i + j, task))
            
            # Wait for all tasks in the batch to complete
            print(f"Processing batch {i//batch_size + 1}/{(total_frames + batch_size - 1)//batch_size} "
                  f"(frames {i+1}-{min(i+batch_size, total_frames)})")
            
            batch_results = await asyncio.gather(*[task for _, _, _, task in batch_tasks])
            
            # Process results and add metadata
            for (timestamp, frame_path, frame_idx, _), analysis_result in zip(batch_tasks, batch_results):
                result = {
                    "timestamp": timestamp,
                    "frame_path": frame_path,
                    "frame_number": frame_idx + 1,
                    **analysis_result
                }
                
                results.append(result)
                
                # Call progress callback if provided
                if progress_callback:
                    progress_callback(frame_idx + 1, total_frames, result)
                
                # Print brief status
                if analysis_result["success"]:
                    print(f"✓ Frame {frame_idx + 1} analyzed successfully")
                else:
                    print(f"✗ Frame {frame_idx + 1} analysis failed: {analysis_result['error']}")
        
        return results
    
    async def generate_comprehensive_summary(self, frame_analyses: List[Dict[str, Any]], video_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a comprehensive summary of the entire video based on all frame analyses.
        
        Args:
            frame_analyses (List[Dict]): List of individual frame analysis results
            video_info (Dict): Video metadata information
            
        Returns:
            Dict[str, Any]: Comprehensive summary of the video
        """
        # Extract successful descriptions
        successful_descriptions = [
            f"Frame {result['frame_number']} ({result['timestamp']:.1f}s): {result['description']}"
            for result in frame_analyses
            if result['success']
        ]
        
        if not successful_descriptions:
            return {
                "success": False,
                "error": "No successful frame analyses to summarize"
            }
        
        # Create summary prompt
        summary_prompt = f"""
You are an AI assistant tasked with creating a comprehensive summary of a video based on frame-by-frame analyses.

Video Information:
- Duration: {video_info['duration_seconds']:.1f} seconds
- Resolution: {video_info['resolution']}
- FPS: {video_info['fps']:.1f}
- Total frames analyzed: {len(successful_descriptions)}

Below are the detailed analyses of individual frames from the video:

{chr(10).join(successful_descriptions)}

Based on these frame analyses, provide a comprehensive summary of the video using the following structure:

1. **Overall Video Summary** – What is this video about? What's the main content, purpose, or narrative?

2. **Key Themes and Topics** – What are the main themes, subjects, or topics covered throughout the video?

3. **Visual Progression** – How does the visual content evolve throughout the video? Are there distinct segments or scenes?

4. **Notable Moments** – Highlight any particularly interesting, important, or distinctive moments in the video.

5. **Technical Observations** – Comment on visual quality, lighting changes, camera work, or production style.

6. **Content Classification** – What type of video is this? (e.g., tutorial, vlog, presentation, entertainment, documentary, etc.)

7. **Key Takeaways** – What are the main points or messages someone would get from watching this video?

Instructions:
- Be concise but comprehensive
- Focus on patterns and overall narrative rather than repeating individual frame details
- Highlight transitions, changes, and progression throughout the video
- Identify the video's purpose and target audience
- Keep the summary well-structured and easy to read
"""

        try:
            # Generate summary using GPT-4o
            response = await self.async_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "user",
                        "content": summary_prompt
                    }
                ],
                max_tokens=1500
            )
            
            summary = response.choices[0].message.content
            
            return {
                "success": True,
                "summary": summary,
                "tokens_used": response.usage.total_tokens,
                "frames_analyzed": len(successful_descriptions),
                "model": "gpt-4o"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "summary": f"Error generating summary: {str(e)}"
            }


def test_api_connection(api_key: str = None) -> bool:
    """
    Test if the OpenAI API connection is working.
    
    Args:
        api_key (str, optional): OpenAI API key to test
        
    Returns:
        bool: True if connection successful, False otherwise
    """
    try:
        analyzer = GPTVisionAnalyzer(api_key)
        # Make a simple API call to test connection
        response = analyzer.client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": "Hello, this is a test."}],
            max_tokens=10
        )
        print("✓ OpenAI API connection successful")
        return True
    except Exception as e:
        print(f"✗ OpenAI API connection failed: {e}")
        return False 