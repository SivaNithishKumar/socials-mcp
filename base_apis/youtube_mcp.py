from typing import Any, List, Optional
import json
from mcp.server.fastmcp import FastMCP
from youtube import YouTubeUploader

# Initialize FastMCP server
mcp = FastMCP("youtube")

# Global YouTube uploader instance
youtube_uploader = None

def get_youtube_uploader():
    """Get or create YouTube uploader instance."""
    global youtube_uploader
    if youtube_uploader is None:
        youtube_uploader = YouTubeUploader()
    return youtube_uploader

def format_video_search_results(videos: List[dict]) -> str:
    """Format video search results into a readable string."""
    if not videos:
        return "No videos found."
    
    formatted_results = []
    for video in videos:
        snippet = video.get("snippet", {})
        video_id = video.get("id", {}).get("videoId", "Unknown")
        title = snippet.get("title", "No title")
        channel = snippet.get("channelTitle", "Unknown channel")
        description = snippet.get("description", "No description")[:200] + "..." if len(snippet.get("description", "")) > 200 else snippet.get("description", "No description")
        published = snippet.get("publishedAt", "Unknown date")
        
        formatted_results.append(f"""
Video ID: {video_id}
Title: {title}
Channel: {channel}
Published: {published}
Description: {description}
URL: https://www.youtube.com/watch?v={video_id}
""")
    
    return "\n---\n".join(formatted_results)

def format_video_details(video: dict) -> str:
    """Format video details into a readable string."""
    snippet = video.get("snippet", {})
    statistics = video.get("statistics", {})
    content_details = video.get("contentDetails", {})
    status = video.get("status", {})
    
    return f"""
Video ID: {video.get("id", "Unknown")}
Title: {snippet.get("title", "No title")}
Channel: {snippet.get("channelTitle", "Unknown channel")}
Published: {snippet.get("publishedAt", "Unknown date")}
Duration: {content_details.get("duration", "Unknown")}
Privacy Status: {status.get("privacyStatus", "Unknown")}
View Count: {statistics.get("viewCount", "0")}
Like Count: {statistics.get("likeCount", "0")}
Comment Count: {statistics.get("commentCount", "0")}
Description: {snippet.get("description", "No description")}
Tags: {", ".join(snippet.get("tags", []))}
Category ID: {snippet.get("categoryId", "Unknown")}
"""

def format_channel_info(channel: dict) -> str:
    """Format channel information into a readable string."""
    if not channel:
        return "Channel not found."
    
    snippet = channel.get("snippet", {})
    statistics = channel.get("statistics", {})
    branding = channel.get("brandingSettings", {})
    
    return f"""
Channel ID: {channel.get("id", "Unknown")}
Title: {snippet.get("title", "No title")}
Description: {snippet.get("description", "No description")}
Country: {snippet.get("country", "Unknown")}
Published: {snippet.get("publishedAt", "Unknown date")}
Subscriber Count: {statistics.get("subscriberCount", "Hidden")}
Video Count: {statistics.get("videoCount", "0")}
View Count: {statistics.get("viewCount", "0")}
Keywords: {branding.get("channel", {}).get("keywords", "None")}
"""

def format_comments(comments: List[dict]) -> str:
    """Format comments into a readable string."""
    if not comments:
        return "No comments found."
    
    formatted_comments = []
    for comment_thread in comments:
        top_comment = comment_thread.get("snippet", {}).get("topLevelComment", {}).get("snippet", {})
        author = top_comment.get("authorDisplayName", "Unknown author")
        text = top_comment.get("textDisplay", "No text")
        published = top_comment.get("publishedAt", "Unknown date")
        likes = top_comment.get("likeCount", 0)
        
        formatted_comments.append(f"""
Author: {author}
Published: {published}
Likes: {likes}
Comment: {text}
""")
    
    return "\n---\n".join(formatted_comments)

@mcp.tool()
async def upload_video(
    file_path: str,
    title: str,
    description: str = "",
    tags: str = "",
    category_id: str = "22",
    privacy_status: str = "private"
) -> str:
    """Upload a video to YouTube.

    Args:
        file_path: Path to the video file
        title: Video title
        description: Video description
        tags: Comma-separated list of tags
        category_id: YouTube category ID (default: 22 for People & Blogs)
        privacy_status: Privacy status (public, private, unlisted)
    """
    try:
        uploader = get_youtube_uploader()
        tags_list = [tag.strip() for tag in tags.split(",") if tag.strip()] if tags else []
        
        response = uploader.upload_video(
            file_path=file_path,
            title=title,
            description=description,
            tags=tags_list,
            category_id=category_id,
            privacy_status=privacy_status
        )
        
        video_id = response.get("id", "Unknown")
        return f"""
Upload successful!
Video ID: {video_id}
Title: {title}
Privacy Status: {privacy_status}
YouTube URL: https://www.youtube.com/watch?v={video_id}
"""
    except Exception as e:
        return f"Upload failed: {str(e)}"

@mcp.tool()
async def search_videos(query: str, max_results: int = 10) -> str:
    """Search for YouTube videos.

    Args:
        query: Search query string
        max_results: Maximum number of results to return (default: 10)
    """
    try:
        uploader = get_youtube_uploader()
        videos = uploader.search_videos(query, max_results)
        return format_video_search_results(videos)
    except Exception as e:
        return f"Search failed: {str(e)}"

@mcp.tool()
async def get_video_details(video_id: str) -> str:
    """Get detailed information about a specific YouTube video.

    Args:
        video_id: YouTube video ID
    """
    try:
        uploader = get_youtube_uploader()
        video = uploader.get_video_details(video_id)
        return format_video_details(video)
    except Exception as e:
        return f"Failed to get video details: {str(e)}"

@mcp.tool()
async def get_channel_info(
    channel_id: Optional[str] = None,
    username: Optional[str] = None,
    mine: bool = False
) -> str:
    """Get information about a YouTube channel.

    Args:
        channel_id: YouTube channel ID
        username: YouTube username (legacy)
        mine: Set to true to get info for authenticated user's channel
    """
    try:
        uploader = get_youtube_uploader()
        channel = uploader.get_channel_info(
            channel_id=channel_id,
            for_username=username,
            mine=mine
        )
        return format_channel_info(channel)
    except Exception as e:
        return f"Failed to get channel info: {str(e)}"

@mcp.tool()
async def list_video_comments(video_id: str, max_results: int = 20) -> str:
    """Get comments for a YouTube video.

    Args:
        video_id: YouTube video ID
        max_results: Maximum number of comments to return (default: 20)
    """
    try:
        uploader = get_youtube_uploader()
        comments = uploader.list_comments(video_id, max_results)
        return format_comments(comments)
    except Exception as e:
        return f"Failed to get comments: {str(e)}"

@mcp.tool()
async def delete_video(video_id: str) -> str:
    """Delete a YouTube video (must be owned by authenticated user).

    Args:
        video_id: YouTube video ID to delete
    """
    try:
        uploader = get_youtube_uploader()
        uploader.delete_video(video_id)
        return f"Successfully deleted video: {video_id}"
    except Exception as e:
        return f"Failed to delete video: {str(e)}"

@mcp.tool()
async def get_analytics_report(
    metrics: str,
    start_date: str,
    end_date: str,
    dimensions: str = "day",
    ids: str = "channel==MINE",
    filters: Optional[str] = None,
    max_results: int = 100
) -> str:
    """Get YouTube Analytics report.

    Args:
        metrics: Comma-separated list of metrics (e.g., "views,estimatedMinutesWatched")
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        dimensions: Dimensions for the report (default: "day")
        ids: Channel or content owner ID (default: "channel==MINE")
        filters: Optional filters for the report
        max_results: Maximum number of results (default: 100)
    """
    try:
        uploader = get_youtube_uploader()
        report = uploader.get_analytics_report(
            metrics=metrics,
            start_date=start_date,
            end_date=end_date,
            dimensions=dimensions,
            ids=ids,
            filters=filters,
            max_results=max_results
        )
        
        # Format the analytics report
        headers = report.get("columnHeaders", [])
        rows = report.get("rows", [])
        
        if not rows:
            return "No analytics data found for the specified period."
        
        # Create a formatted table
        formatted_report = "Analytics Report:\n\n"
        
        # Add headers
        header_names = [header.get("name", "") for header in headers]
        formatted_report += " | ".join(header_names) + "\n"
        formatted_report += "-" * (len(" | ".join(header_names))) + "\n"
        
        # Add data rows
        for row in rows:
            formatted_report += " | ".join([str(cell) for cell in row]) + "\n"
        
        return formatted_report
        
    except Exception as e:
        return f"Failed to get analytics report: {str(e)}"

if __name__ == "__main__":
    # Initialize and run the server
    mcp.run(transport='stdio') 