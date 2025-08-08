#!/usr/bin/env python3
"""
YouTube Video Utilities

This module provides functionality to download YouTube videos and extract 
the first N seconds for analysis.
"""

import os
import re
import tempfile
import yt_dlp
from typing import List, Dict, Optional, Tuple
from pathlib import Path


class YouTubeDownloader:
    """
    A class to handle YouTube video downloading and processing.
    """
    
    def __init__(self, temp_dir: str = None):
        """
        Initialize the YouTube downloader.
        
        Args:
            temp_dir (str, optional): Directory for temporary files. Uses system temp if None.
        """
        self.temp_dir = temp_dir or tempfile.gettempdir()
        self.downloads_dir = os.path.join(self.temp_dir, "youtube_downloads")
        os.makedirs(self.downloads_dir, exist_ok=True)

        # Optional cookies support for age/region-gated videos
        # Either provide a file path via YT_DLP_COOKIEFILE, or raw Netscape cookies text via YT_DLP_COOKIES
        self.cookiefile: Optional[str] = None
        cookiefile_env = os.getenv("YT_DLP_COOKIEFILE")
        cookies_inline_env = os.getenv("YT_DLP_COOKIES")
        if cookiefile_env and os.path.exists(cookiefile_env):
            self.cookiefile = cookiefile_env
        elif cookies_inline_env:
            # Persist inline cookies into a temp file
            cookie_path = os.path.join(self.temp_dir, "yt_cookies.txt")
            with open(cookie_path, "w", encoding="utf-8") as f:
                f.write(cookies_inline_env)
            self.cookiefile = cookie_path

    # ----------------------
    # URL utilities
    # ----------------------
    @staticmethod
    def extract_video_id(url: str) -> Optional[str]:
        """Extract YouTube video id from various URL formats including Shorts."""
        # Try standard watch
        m = re.search(r"[?&]v=([\w-]{6,})", url)
        if m:
            return m.group(1)
        # Short youtu.be
        m = re.search(r"youtu\.be/([\w-]{6,})", url)
        if m:
            return m.group(1)
        # Shorts
        m = re.search(r"/shorts/([\w-]{6,})", url)
        if m:
            return m.group(1)
        # Embed
        m = re.search(r"/embed/([\w-]{6,})", url)
        if m:
            return m.group(1)
        # Legacy /v/
        m = re.search(r"/v/([\w-]{6,})", url)
        if m:
            return m.group(1)
        return None

    @classmethod
    def normalize_to_watch_url(cls, url: str) -> str:
        """Normalize any supported YouTube URL to a watch?v= form.
        This helps avoid occasional Shorts-specific access issues on headless hosts.
        """
        vid = cls.extract_video_id(url)
        return f"https://www.youtube.com/watch?v={vid}" if vid else url

    # ----------------------
    # yt-dlp options builder
    # ----------------------
    def _build_yt_dlp_opts(self, outtmpl: Optional[str] = None, duration_seconds: Optional[int] = None) -> Dict:
        opts: Dict = {
            'quiet': True,
            'no_warnings': True,
            'noplaylist': True,
            'geo_bypass': True,
            'geo_bypass_country': 'US',
            'user_agent': (
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                'AppleWebKit/537.36 (KHTML, like Gecko) '
                'Chrome/126.0.0.0 Safari/537.36'
            ),
            'http_headers': {
                'User-Agent': (
                    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                    'AppleWebKit/537.36 (KHTML, like Gecko) '
                    'Chrome/126.0.0.0 Safari/537.36'
                ),
                'Accept-Language': 'en-US,en;q=0.9',
                'Referer': 'https://www.youtube.com/'
            },
            # Prefer mp4
            'format': 'best[ext=mp4]/best',
        }

        if self.cookiefile:
            opts['cookiefile'] = self.cookiefile

        if outtmpl:
            opts['outtmpl'] = outtmpl

        if duration_seconds and duration_seconds > 0:
            # Limit duration via ffmpeg postprocessor
            opts['postprocessor_args'] = ['-t', str(duration_seconds)]
            opts['postprocessors'] = [{
                'key': 'FFmpegVideoConvertor',
                'preferedformat': 'mp4',
            }]

        return opts
    
    def is_valid_youtube_url(self, url: str) -> bool:
        """
        Check if the provided URL is a valid YouTube URL.
        
        Args:
            url (str): URL to validate
            
        Returns:
            bool: True if valid YouTube URL, False otherwise
        """
        youtube_patterns = [
            r'(?:https?://)?(?:www\.)?youtube\.com/watch\?v=[\w-]+',
            r'(?:https?://)?(?:www\.)?youtu\.be/[\w-]+',
            r'(?:https?://)?(?:www\.)?youtube\.com/embed/[\w-]+',
            r'(?:https?://)?(?:www\.)?youtube\.com/v/[\w-]+',
            r'(?:https?://)?(?:www\.)?youtube\.com/shorts/[\w-]+',
        ]
        
        return any(re.match(pattern, url) for pattern in youtube_patterns)
    
    def validate_urls(self, urls: List[str]) -> Tuple[List[str], List[str]]:
        """
        Validate a list of YouTube URLs.
        
        Args:
            urls (List[str]): List of URLs to validate
            
        Returns:
            Tuple[List[str], List[str]]: (valid_urls, invalid_urls)
        """
        valid_urls = []
        invalid_urls = []
        
        for url in urls:
            if self.is_valid_youtube_url(url):
                valid_urls.append(url)
            else:
                invalid_urls.append(url)
        
        return valid_urls, invalid_urls
    
    def get_video_info(self, url: str) -> Optional[Dict]:
        """
        Get video information without downloading.
        
        Args:
            url (str): YouTube video URL
            
        Returns:
            Optional[Dict]: Video info dict or None if failed
        """
        # Try original URL first
        try_urls = [url]
        # Add normalized watch URL as fallback (helps for Shorts)
        normalized = self.normalize_to_watch_url(url)
        if normalized != url:
            try_urls.append(normalized)

        for attempt_url in try_urls:
            try:
                with yt_dlp.YoutubeDL(self._build_yt_dlp_opts()) as ydl:
                    info = ydl.extract_info(attempt_url, download=False)
                    return {
                        'id': info.get('id'),
                        'title': info.get('title'),
                        'duration': info.get('duration'),
                        'uploader': info.get('uploader'),
                        'view_count': info.get('view_count'),
                        'upload_date': info.get('upload_date'),
                        'url': attempt_url
                    }
            except Exception as e:
                print(f"Error getting info for {attempt_url}: {e}")
                continue

        return None
    
    def download_video(self, url: str, duration_seconds: int = 20) -> Optional[str]:
        """
        Download a YouTube video, limiting to specified duration.
        
        Args:
            url (str): YouTube video URL
            duration_seconds (int): Maximum duration to download (default: 20)
            
        Returns:
            Optional[str]: Path to downloaded video file or None if failed
        """
        # Get video info first
        info = self.get_video_info(url)
        if not info:
            return None
        
        video_id = info['id']
        safe_title = re.sub(r'[<>:"/\\|?*]', '_', info['title'][:50])
        output_filename = f"{video_id}_{safe_title}.%(ext)s"
        output_path = os.path.join(self.downloads_dir, output_filename)
        
        # Configure yt-dlp options
        ydl_opts = self._build_yt_dlp_opts(outtmpl=output_path, duration_seconds=duration_seconds)
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                print(f"Downloading: {info['title']} (first {duration_seconds}s)")
                # Always prefer normalized watch URL for actual download
                normalized_download_url = self.normalize_to_watch_url(url)
                ydl.download([normalized_download_url])
                
                # Find the downloaded file
                for file in os.listdir(self.downloads_dir):
                    if file.startswith(video_id):
                        downloaded_path = os.path.join(self.downloads_dir, file)
                        print(f"✓ Downloaded: {downloaded_path}")
                        return downloaded_path
                
                print(f"✗ Could not find downloaded file for {video_id}")
                return None
                
        except Exception as e:
            print(f"✗ Error downloading {url}: {e}")
            return None
    
    def download_multiple_videos(self, urls: List[str], duration_seconds: int = 20, max_videos: int = 10) -> List[Dict]:
        """
        Download multiple YouTube videos.
        
        Args:
            urls (List[str]): List of YouTube URLs
            duration_seconds (int): Maximum duration per video (default: 20)
            max_videos (int): Maximum number of videos to download (default: 10)
            
        Returns:
            List[Dict]: List of download results with metadata
        """
        # Validate URLs first
        valid_urls, invalid_urls = self.validate_urls(urls)
        
        if invalid_urls:
            print(f"Warning: {len(invalid_urls)} invalid URLs found:")
            for url in invalid_urls:
                print(f"  - {url}")
        
        # Limit to max_videos
        if len(valid_urls) > max_videos:
            print(f"Limiting to first {max_videos} videos (got {len(valid_urls)})")
            valid_urls = valid_urls[:max_videos]
        
        results = []
        
        for i, url in enumerate(valid_urls, 1):
            print(f"\n[{i}/{len(valid_urls)}] Processing: {url}")
            
            # Get video info
            info = self.get_video_info(url)
            if not info:
                results.append({
                    'url': url,
                    'success': False,
                    'error': 'Failed to get video info',
                    'video_path': None,
                    'info': None
                })
                continue
            
            # Download video
            video_path = self.download_video(url, duration_seconds)
            
            result = {
                'url': url,
                'success': video_path is not None,
                'video_path': video_path,
                'info': info,
                'duration_limited_to': duration_seconds
            }
            
            if not video_path:
                result['error'] = 'Download failed'
            
            results.append(result)
        
        # Print summary
        successful = sum(1 for r in results if r['success'])
        print(f"\nDownload Summary:")
        print(f"  Total URLs: {len(urls)}")
        print(f"  Valid URLs: {len(valid_urls)}")
        print(f"  Successfully downloaded: {successful}")
        print(f"  Failed downloads: {len(valid_urls) - successful}")
        
        return results
    
    def cleanup_downloads(self):
        """
        Clean up downloaded video files.
        """
        try:
            import shutil
            if os.path.exists(self.downloads_dir):
                shutil.rmtree(self.downloads_dir)
                print(f"Cleaned up downloads directory: {self.downloads_dir}")
        except Exception as e:
            print(f"Error cleaning up downloads: {e}")


def extract_video_id_from_url(url: str) -> Optional[str]:
    """
    Extract YouTube video ID from URL.
    
    Args:
        url (str): YouTube URL
        
    Returns:
        Optional[str]: Video ID or None if not found
    """
    patterns = [
        r'(?:v=|\/)([0-9A-Za-z_-]{11}).*',
        r'(?:embed\/)([0-9A-Za-z_-]{11})',
        r'(?:youtu\.be\/)([0-9A-Za-z_-]{11})',
        r'(?:shorts\/)([0-9A-Za-z_-]{11})',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    
    return None


def validate_youtube_urls(urls: List[str]) -> Dict[str, List[str]]:
    """
    Validate a list of YouTube URLs and categorize them.
    
    Args:
        urls (List[str]): List of URLs to validate
        
    Returns:
        Dict[str, List[str]]: Dictionary with 'valid' and 'invalid' URL lists
    """
    downloader = YouTubeDownloader()
    valid_urls, invalid_urls = downloader.validate_urls(urls)
    
    return {
        'valid': valid_urls,
        'invalid': invalid_urls
    }