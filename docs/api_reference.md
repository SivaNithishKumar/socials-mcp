# API Reference – MVP (script-level)

> These APIs are currently exposed as **Python helper classes / functions** inside `Base_APIs/`.  In the upcoming server versions they will be wrapped behind REST endpoints, but you can already import and use them directly.

## Table of Contents
1. [YouTube](#youtube)
2. [Twitter / X](#twitter--x)
3. [Facebook Page](#facebook-page)
4. [Instagram Graph](#instagram-graph)
5. [LinkedIn](#linkedin)

---

## YouTube
Location: `Base_APIs/youtube.py`

| Method                 | Description |
| ---------------------- | ----------- |
| `upload_video()`       | OAuth 2.0 flow + resumable upload. Supports title, description, tags, category, privacy, progress indicator. |
| `search_videos()`      | Simple keyword search (`videos.search` endpoint). |
| `get_video_details()`  | Retrieve snippet, statistics, content details for a single video. |
| `get_channel_info()`   | Channel metadata by ID, username, or `mine=True`. |
| `list_comments()`      | Top-level comments (threads) for a video. Requires `youtube.force-ssl` scope. |
| `delete_video()`       | Permanently delete an owned video. |
| `get_analytics_report()` | Wrapper around YouTube Analytics **v2** report endpoint. |

**Scopes required**: `youtube.upload`, `youtube.readonly`, `youtube.force-ssl`, `yt-analytics.readonly` *(see code)*.

---

## Twitter / X
Location: `Base_APIs/twitter.py` (+ `twitter_rate_limits.py`)

| Method | Description |
| ------ | ----------- |
| `create_tweet()` | Post plain-text tweet (optionally media IDs). |
| `delete_tweet()` | Remove tweet by ID. |
| `upload_media_simple()` | Non-chunked media upload for images/GIFs <5 MB. |
| `upload_media_chunked()` | Chunked upload for larger media (video). |
| `create_tweet_with_media()` | Convenience helper: upload then tweet in one call. |

`twitter_rate_limits.py` wraps the same endpoints but auto-handles **429** with exponential back-off + slice-wise quotas.

---

## Facebook Page
Location: `Base_APIs/facebook_post.py`

| Function | Description |
| -------- | ----------- |
| `post_to_facebook()` | Publish text post to a Page. |
| `post_local_image_to_facebook()` | Upload local image with caption. |
| `delete_facebook_post()` | Delete Page post. |
| `comment_on_post()` | Add comment on post. |
| `delete_facebook_comment()` | Delete comment by ID. |

Requires a **Page access token** with `pages_manage_posts` and `pages_read_engagement` permissions.

---

## Instagram Graph
Location: `Base_APIs/insta_post.py`

Features (Business / Creator accounts only):

* Upload local image to ImageKit then create **Media Container** (`/media`).
* Publish container immediately or leave it scheduled.
* Continue an existing container (publish later).
* Delete unpublished container.
* Create / delete comments.

Environment variables: `ACCESS_TOKEN`, `INSTAGRAM_ACCOUNT_ID`, ImageKit credentials.

---

## LinkedIn
Location: `Base_APIs/LinkedIn_post.py`

| Function | Description |
| -------- | ----------- |
| `create_post()` | UGC (User Generated Content) API – publish a text post to member feed. |
| `delete_post()` | Delete post by URN. |

Needs **`w_member_social`** permission and v2 auth token.

---

## Future REST Endpoints
The FastAPI server (see `src/mcp/`) will expose REST wrappers that internally call these helpers, following the pattern:

```
POST /v1/youtube/videos
POST /v1/twitter/tweets
...
```

Track progress in `docs/architecture.md`. 