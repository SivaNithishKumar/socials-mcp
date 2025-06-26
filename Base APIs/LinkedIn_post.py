import requests
import time
import urllib.parse

# Fill these with your own values
ACCESS_TOKEN = 'ACCESS_TOKEN'  # Get this from LinkedIn Developer Portal
USER_URN = 'urn:li:person:ID'  # e.g., 'urn:li:person:abc123...'

# LinkedIn API endpoints
POST_URL = 'https://api.linkedin.com/v2/ugcPosts'
DELETE_URL_TEMPLATE = 'https://api.linkedin.com/v2/ugcPosts/{post_id}'

# Headers for LinkedIn API
headers = {
    'Authorization': f'Bearer {ACCESS_TOKEN}',
    'X-Restli-Protocol-Version': '2.0.0',
    'Content-Type': 'application/json',
}

def create_post():
    post_data = {
        "author": USER_URN,
        "lifecycleState": "PUBLISHED",
        "specificContent": {
            "com.linkedin.ugc.ShareContent": {
                "shareCommentary": {
                    "text": "Hey there!!!, this is a test post from the LinkedIn API!"
                },
                "shareMediaCategory": "NONE"
            }
        },
        "visibility": {
            "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
        }
    }
    response = requests.post(POST_URL, headers=headers, json=post_data)
    if response.status_code == 201:
        post_urn = response.headers.get('x-restli-id')
        print(f"Post created successfully! Post URN: {post_urn}")
        return post_urn
    else:
        print(f"Failed to create post: {response.status_code} {response.text}")
        return None

def delete_post(post_urn):
    encoded_urn = urllib.parse.quote(post_urn, safe='')
    delete_url = DELETE_URL_TEMPLATE.format(post_id=encoded_urn)
    response = requests.delete(delete_url, headers=headers)
    if response.status_code == 204:
        print("Post deleted successfully!")
    else:
        print(f"Failed to delete post: {response.status_code} {response.text}")

if __name__ == "__main__":
    post_urn = create_post()
    if post_urn:
        print("Waiting 15 seconds before deleting the post...")
        time.sleep(15)
        delete_post(post_urn)
