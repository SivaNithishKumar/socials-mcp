import os
import sys
import time
import random
from typing import List, Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload

# If modifying these SCOPES, delete the token.json file.
SCOPES = [
    # Upload videos, read basic channel/video info, read analytics
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.readonly",
    "https://www.googleapis.com/auth/yt-analytics.readonly",
    "https://www.googleapis.com/auth/youtube.force-ssl",
]

CLIENT_SECRETS_FILE = os.path.join(os.path.dirname(__file__), "client_secret.json")
TOKEN_FILE = os.path.join(os.path.dirname(__file__), "youtube_token.json")


class YouTubeUploader:
    """Simple wrapper around the YouTube Data API v3 for uploading videos."""

    def __init__(self):
        self.youtube = self._get_authenticated_service()

    def _get_authenticated_service(self):
        """Authenticate the user via OAuth and return an authorized YouTube service."""
        creds: Optional[Credentials] = None

        # Load saved credentials, if they exist
        if os.path.exists(TOKEN_FILE):
            creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not os.path.exists(CLIENT_SECRETS_FILE):
                    raise FileNotFoundError(
                        f"OAuth client configuration not found: {CLIENT_SECRETS_FILE}. "
                        "Please create a Project in Google Cloud Console, enable the YouTube Data API, "
                        "and download the OAuth 2.0 Client ID JSON file as client_secret.json."
                    )
                flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS_FILE, SCOPES)
                try:
                    if hasattr(flow, "run_local_server"):
                        # Attempt browser-based flow on a fixed port that you must also whitelist
                        # in the OAuth client's Authorized redirect URIs (e.g., http://localhost:8080/).
                        creds = flow.run_local_server(port=8080, prompt="consent")
                    else:
                        raise AttributeError("run_local_server not available")
                except (Exception, AttributeError) as auth_err:
                    # Fallback to console-based flow if local server fails (e.g., redirect_uri_mismatch)
                    print(
                        "Could not complete browser-based OAuth flow (" + str(auth_err) + ").\n"
                        "Falling back to console-based authorization. You will need to copy\n"
                        "and paste a verification code from your browser."
                    )
                    creds = flow.run_console()
            # Save credentials for the next run
            with open(TOKEN_FILE, "w") as token:
                token.write(creds.to_json())

        return build("youtube", "v3", credentials=creds, cache_discovery=False)

    def upload_video(
        self,
        file_path: str,
        title: str,
        description: str = "",
        tags: Optional[List[str]] = None,
        category_id: str = "22",
        privacy_status: str = "private",
    ) -> dict:
        """Uploads a video to the authenticated user's channel.

        Args:
            file_path: Path to the video file.
            title: Video title.
            description: Video description.
            tags: List of tags.
            category_id: Numeric YouTube category ID. Defaults to 22 (People & Blogs).
            privacy_status: one of "public", "private", "unlisted".

        Returns:
            The API response with the newly created video resource.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Video file not found: {file_path}")

        if privacy_status not in {"public", "private", "unlisted"}:
            raise ValueError("privacy_status must be one of public, private, unlisted")

        body = {
            "snippet": {
                "title": title,
                "description": description,
                "tags": tags or [],
                "categoryId": category_id,
            },
            "status": {"privacyStatus": privacy_status},
        }

        media_body = MediaFileUpload(file_path, chunksize=-1, resumable=True)

        request = self.youtube.videos().insert(
            part=",".join(body.keys()),
            body=body,
            media_body=media_body,
        )

        print("Initiating upload...")
        response = None
        while response is None:
            try:
                status, response = request.next_chunk()
                if status:
                    progress = int(status.progress() * 100)
                    print(f"Upload progress: {progress}%")
            except HttpError as err:
                if err.resp.status in {500, 502, 503, 504}:
                    print(f"Retriable HTTP error {err.resp.status}: {err.content}. Retrying...")
                    time.sleep(random.random() * 5 + 1)
                else:
                    raise

        print(f"Upload complete. Video ID: {response.get('id')}")
        return response

    # --------------------------------------------
    # Additional helper methods
    # --------------------------------------------

    def search_videos(self, query: str, max_results: int = 10) -> list:
        """Search YouTube videos by a query string."""
        response = (
            self.youtube.search()
            .list(q=query, part="id,snippet", type="video", maxResults=max_results)
            .execute()
        )
        return response.get("items", [])

    def get_video_details(self, video_id: str) -> dict:
        """Retrieve detailed metadata for a single video.

        Returns the full item dict. Raises ValueError if the video is not found
        or if the response does not include the requested parts.
        """
        response = (
            self.youtube.videos()
            .list(id=video_id, part="snippet,statistics,contentDetails,status")
            .execute()
        )

        items = response.get("items", [])
        if not items:
            raise ValueError(f"Video '{video_id}' not found or unavailable in API response.")

        item = items[0]
        # Ensure statistics are present; if not, this usually indicates the channel disabled stats
        if "statistics" not in item:
            # Populate empty statistics object so code accessing item["statistics"] doesn't crash
            item["statistics"] = {}

        return item

    def get_channel_info(self, channel_id: Optional[str] = None, for_username: Optional[str] = None, mine: bool = False) -> dict:
        """Fetch channel information by ID, username, or the authenticated user's channel (mine=True)."""
        if sum(bool(x) for x in [channel_id, for_username, mine]) != 1:
            raise ValueError("Provide exactly one of channel_id, for_username, or set mine=True")

        params = {"part": "snippet,statistics,brandingSettings"}
        if channel_id:
            params["id"] = channel_id
        elif for_username:
            params["forUsername"] = for_username
        else:
            params["mine"] = True

        response = self.youtube.channels().list(**params).execute()
        return response.get("items", [None])[0] if response.get("items") else {}

    def list_comments(self, video_id: str, max_results: int = 20) -> list:
        """Retrieve top-level comments (threads) for a video."""
        response = (
            self.youtube.commentThreads()
            .list(videoId=video_id, part="snippet,replies", maxResults=max_results)
            .execute()
        )
        return response.get("items", [])

    def delete_video(self, video_id: str) -> None:
        """Permanently delete a video owned by the authenticated user."""
        self.youtube.videos().delete(id=video_id).execute()
        print(f"Deleted video {video_id}.")

    # ------------------ Analytics ------------------
    def _get_analytics_service(self):
        """Lazily build a YouTube Analytics API client using existing creds."""
        if not hasattr(self, "_yt_analytics"):
            self._yt_analytics = build("youtubeAnalytics", "v2", credentials=self.youtube._http.credentials, cache_discovery=False)
        return self._yt_analytics

    def get_analytics_report(
        self,
        metrics: str,
        start_date: str,
        end_date: str,
        dimensions: str = "day",
        ids: str = "channel==MINE",
        filters: Optional[str] = None,
        max_results: int = 100
    ) -> dict:
        """Query YouTube Analytics. Dates must be YYYY-MM-DD."""
        analytics = self._get_analytics_service()
        query_params = {
            "ids": ids,
            "metrics": metrics,
            "dimensions": dimensions,
            "startDate": start_date,
            "endDate": end_date,
            "maxResults": max_results,
        }
        if filters:
            query_params["filters"] = filters
        return analytics.reports().query(**query_params).execute()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Upload a video to YouTube.")
    parser.add_argument("--file",  help="Path to the video file to upload")
    parser.add_argument("--title", default="Test Title", help="Video title")
    parser.add_argument("--description", default="Test Description", help="Video description")
    parser.add_argument("--keywords", default="", help="Comma-separated list of video tags")
    parser.add_argument(
        "--category",
        default="22",
        help="Numeric video category ID. Run https://developers.google.com/youtube/v3/docs/videoCategories/list for options",
    )
    parser.add_argument(
        "--privacy",
        default="private",
        choices=["public", "private", "unlisted"],
        help="Video privacy status",
    )

    args = parser.parse_args()

    tags_list = [tag.strip() for tag in args.keywords.split(",") if tag.strip()]

    uploader = YouTubeUploader()
    try:
        uploader.upload_video(
            file_path="Base APIs/media/AI Marketer.mp4",
            title=args.title,
            description=args.description,
            tags=tags_list,
            category_id=args.category,
            privacy_status=args.privacy,
        )
    except HttpError as e:
        print(f"An HTTP error {e.resp.status} occurred: {e.content}")
