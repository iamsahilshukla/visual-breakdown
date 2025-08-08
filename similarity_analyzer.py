#!/usr/bin/env python3
"""
Video Similarity Analyzer

This module provides functionality to analyze similarities between multiple video breakdowns
using OpenAI's GPT models.
"""

import json
from typing import List, Dict, Any, Optional
from openai import AsyncOpenAI, OpenAI


class VideoSimilarityAnalyzer:
    """
    A class to analyze similarities between multiple video breakdowns using LLM.
    """
    
    def __init__(self, api_key: str = None):
        """
        Initialize the similarity analyzer.
        
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
    
    def prepare_video_summaries(self, video_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Prepare video summaries for similarity analysis.
        
        Args:
            video_results (List[Dict]): List of video analysis results
            
        Returns:
            List[Dict]: Processed video summaries
        """
        summaries = []
        
        for i, video_result in enumerate(video_results):
            if not video_result.get('breakdown_success', False):
                continue
            
            breakdown = video_result.get('breakdown_data', {})
            metadata = breakdown.get('metadata', {})
            frame_analyses = breakdown.get('frame_analyses', [])
            video_summary = breakdown.get('video_summary', {})
            
            # Extract key information
            video_info = {
                'video_index': i + 1,
                'url': video_result.get('url', 'Unknown'),
                'title': video_result.get('info', {}).get('title', 'Unknown Title'),
                'duration_analyzed': metadata.get('video_info', {}).get('duration_seconds', 0),
                'frames_analyzed': len(frame_analyses),
                'summary': video_summary.get('summary', '') if video_summary.get('success') else '',
                'frame_descriptions': []
            }
            
            # Add frame descriptions
            for frame in frame_analyses:
                if frame.get('success'):
                    video_info['frame_descriptions'].append({
                        'timestamp': frame.get('timestamp', 0),
                        'description': frame.get('description', '')
                    })
            
            summaries.append(video_info)
        
        return summaries
    
    async def analyze_similarities_async(self, video_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze similarities between multiple video breakdowns asynchronously.
        
        Args:
            video_results (List[Dict]): List of video analysis results
            
        Returns:
            Dict[str, Any]: Similarity analysis results
        """
        # Prepare summaries
        summaries = self.prepare_video_summaries(video_results)
        
        if len(summaries) < 2:
            return {
                'success': False,
                'error': 'Need at least 2 successfully analyzed videos for comparison',
                'videos_analyzed': len(summaries)
            }
        
        # Create comprehensive prompt for similarity analysis
        prompt = self._create_similarity_prompt(summaries)
        
        try:
            response = await self.async_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=2000
            )
            
            analysis = response.choices[0].message.content
            
            return {
                'success': True,
                'analysis': analysis,
                'tokens_used': response.usage.total_tokens,
                'videos_compared': len(summaries),
                'video_titles': [s['title'] for s in summaries],
                'model': 'gpt-4o'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'videos_compared': len(summaries)
            }
    
    def analyze_similarities(self, video_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze similarities between multiple video breakdowns synchronously.
        
        Args:
            video_results (List[Dict]): List of video analysis results
            
        Returns:
            Dict[str, Any]: Similarity analysis results
        """
        # Prepare summaries
        summaries = self.prepare_video_summaries(video_results)
        
        if len(summaries) < 2:
            return {
                'success': False,
                'error': 'Need at least 2 successfully analyzed videos for comparison',
                'videos_analyzed': len(summaries)
            }
        
        # Create comprehensive prompt for similarity analysis
        prompt = self._create_similarity_prompt(summaries)
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=2000
            )
            
            analysis = response.choices[0].message.content
            
            return {
                'success': True,
                'analysis': analysis,
                'tokens_used': response.usage.total_tokens,
                'videos_compared': len(summaries),
                'video_titles': [s['title'] for s in summaries],
                'model': 'gpt-4o'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'videos_compared': len(summaries)
            }
    
    def _create_similarity_prompt(self, summaries: List[Dict[str, Any]]) -> str:
        """
        Create a comprehensive prompt for similarity analysis.
        
        Args:
            summaries (List[Dict]): Video summaries to compare
            
        Returns:
            str: Formatted prompt
        """
        prompt = f"""
You are an AI assistant specialized in analyzing and comparing video content. I will provide you with detailed breakdowns of {len(summaries)} different videos, and you need to analyze their similarities and differences.

Each video has been analyzed frame-by-frame for the first 20 seconds, with detailed descriptions and comprehensive summaries.

Here are the video breakdowns:

"""
        
        # Add each video's information
        for i, summary in enumerate(summaries, 1):
            prompt += f"""
=== VIDEO {i}: {summary['title']} ===
URL: {summary['url']}
Duration Analyzed: {summary['duration_analyzed']:.1f} seconds
Frames Analyzed: {summary['frames_analyzed']}

COMPREHENSIVE SUMMARY:
{summary['summary']}

FRAME-BY-FRAME DESCRIPTIONS:
"""
            
            for frame in summary['frame_descriptions'][:10]:  # Limit to first 10 frames for prompt size
                prompt += f"• {frame['timestamp']:.1f}s: {frame['description'][:200]}{'...' if len(frame['description']) > 200 else ''}\n"
            
            prompt += "\n"
        
        prompt += f"""
Based on these {len(summaries)} video analyses, provide a comprehensive comparison using the following structure:

## 1. OVERALL SIMILARITY ASSESSMENT
- Rate the overall similarity between these videos on a scale of 1-10 (1 = completely different, 10 = nearly identical)
- Provide a brief explanation of your rating

## 2. COMMON THEMES AND PATTERNS
- What themes, topics, or subjects appear across multiple videos?
- Are there any recurring visual elements, settings, or styles?
- Do the videos share similar purposes or target audiences?

## 3. CONTENT CATEGORIES AND CLASSIFICATION
- How would you categorize each video? (e.g., tutorial, entertainment, documentary, vlog, etc.)
- Are there videos that belong to the same category?
- What are the primary content types represented?

## 4. VISUAL AND PRODUCTION SIMILARITIES
- Are there similarities in production quality, filming style, or visual presentation?
- Do any videos share similar environments, lighting, or camera work?
- Are there common visual elements or aesthetics?

## 5. THEMATIC CLUSTERING
- Can you group these videos into clusters based on similarity?
- Which videos are most similar to each other and why?
- Which videos are outliers or unique compared to the rest?

## 6. KEY DIFFERENCES AND UNIQUE ASPECTS
- What makes each video unique or different from the others?
- Are there videos that stand out as particularly different?
- What are the main differentiating factors?

Please be specific and reference the actual video content in your analysis. Use video numbers (Video 1, Video 2, etc.) when making comparisons.
"""
        
        return prompt
    
    async def generate_pairwise_comparisons(self, video_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate pairwise similarity comparisons between all videos.
        
        Args:
            video_results (List[Dict]): List of video analysis results
            
        Returns:
            Dict[str, Any]: Pairwise comparison results
        """
        summaries = self.prepare_video_summaries(video_results)
        
        if len(summaries) < 2:
            return {
                'success': False,
                'error': 'Need at least 2 successfully analyzed videos for comparison'
            }
        
        comparisons = []
        
        # Generate all pairwise combinations
        for i in range(len(summaries)):
            for j in range(i + 1, len(summaries)):
                video1 = summaries[i]
                video2 = summaries[j]
                
                prompt = f"""
Compare these two videos and rate their similarity on a scale of 1-10:

VIDEO A: {video1['title']}
Summary: {video1['summary'][:500]}...

VIDEO B: {video2['title']}
Summary: {video2['summary'][:500]}...

Provide:
1. Similarity score (1-10)
2. Brief explanation (2-3 sentences)
3. Main similarities
4. Main differences

Format: Score: X/10. Explanation: [your analysis]
"""
                
                try:
                    response = await self.async_client.chat.completions.create(
                        model="gpt-4o",
                        messages=[{"role": "user", "content": prompt}],
                        max_tokens=300
                    )
                    
                    comparison_result = response.choices[0].message.content
                    
                    comparisons.append({
                        'video1_index': i + 1,
                        'video2_index': j + 1,
                        'video1_title': video1['title'],
                        'video2_title': video2['title'],
                        'comparison': comparison_result,
                        'tokens_used': response.usage.total_tokens
                    })
                    
                except Exception as e:
                    comparisons.append({
                        'video1_index': i + 1,
                        'video2_index': j + 1,
                        'video1_title': video1['title'],
                        'video2_title': video2['title'],
                        'comparison': f"Error: {str(e)}",
                        'tokens_used': 0
                    })
        
        total_tokens = sum(c.get('tokens_used', 0) for c in comparisons)
        
        return {
            'success': True,
            'pairwise_comparisons': comparisons,
            'total_pairs': len(comparisons),
            'total_tokens_used': total_tokens,
            'videos_analyzed': len(summaries)
        }


def save_similarity_results(results: Dict[str, Any], output_path: str):
    """
    Save similarity analysis results to a JSON file.
    
    Args:
        results (Dict[str, Any]): Similarity analysis results
        output_path (str): Path to save the results
    """
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"Similarity analysis saved to: {output_path}")