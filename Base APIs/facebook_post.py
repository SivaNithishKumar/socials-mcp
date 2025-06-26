import requests

def post_to_facebook(text, page_access_token, page_id):
    """
    Posts a text message to a Facebook Page.
    Args:
        text (str): The message to post.
        page_access_token (str): The Page Access Token.
        page_id (str): The Facebook Page ID.
    Returns:
        dict: The response from the Facebook Graph API.
    """
    url = f"https://graph.facebook.com/{page_id}/feed"
    payload = {
        'message': text,
        'access_token': page_access_token
    }
    response = requests.post(url, data=payload)
    return response.json()

def post_local_image_to_facebook(caption, image_path, page_access_token, page_id):
    url = f"https://graph.facebook.com/{page_id}/photos"
    payload = {
        'caption': caption,
        'access_token': page_access_token
    }
    files = {
        'source': open(image_path, 'rb')
    }
    response = requests.post(url, data=payload, files=files)
    return response.json()

def delete_facebook_post(post_id, page_access_token):
    """
    Deletes a post from a Facebook Page.
    Args:
        post_id (str): The ID of the post to delete.
        page_access_token (str): The Page Access Token.
    Returns:
        dict: The response from the Facebook Graph API.
    """
    url = f"https://graph.facebook.com/{post_id}"
    payload = {
        'access_token': page_access_token
    }
    response = requests.delete(url, params=payload)
    return response.json()

def comment_on_post(post_id, comment_text, page_access_token):
    url = f"https://graph.facebook.com/{post_id}/comments"
    payload = {
        'message': comment_text,
        'access_token': page_access_token
    }
    response = requests.post(url, data=payload)
    return response.json()

def delete_facebook_comment(comment_id, page_access_token):
    """
    Deletes a comment from a Facebook Page post.
    Args:
        comment_id (str): The ID of the comment to delete.
        page_access_token (str): The Page Access Token.
    Returns:
        dict: The response from the Facebook Graph API.
    """
    url = f"https://graph.facebook.com/{comment_id}"
    payload = {
        'access_token': page_access_token
    }
    response = requests.delete(url, params=payload)
    return response.json()

if __name__ == "__main__":
    # Example usage
    PAGE_ACCESS_TOKEN = "ACCESS_TOKEN"
    PAGE_ID = "PAGE_ID"
    MESSAGE = "Hello, Facebook! This is a test post from the API."
    IMAGE_PATH = r"IMAGE_PATH"

    print("Choose an action:")
    print("1. Create a post with image")
    print("2. Delete a post by ID")
    print("3. Comment on a post by ID")
    print("4. Delete a comment by ID")
    choice = input("Enter 1, 2, 3, or 4: ").strip()

    if choice == "1":
        result = post_local_image_to_facebook(MESSAGE, IMAGE_PATH, PAGE_ACCESS_TOKEN, PAGE_ID)
        print("Post creation result:", result)
        if 'id' in result:
            print(f"Post created successfully! Post ID: {result['id']}")
        else:
            print("Failed to create post.")
    elif choice == "2":
        post_id = input("Enter the Post ID to delete: ").strip()
        delete_result = delete_facebook_post(post_id, PAGE_ACCESS_TOKEN)
        print('Delete result:', delete_result)
    elif choice == "3":
        post_id = input("Enter the Post ID to comment on: ").strip()
        comment_text = input("Enter your comment: ").strip()
        comment_result = comment_on_post(post_id, comment_text, PAGE_ACCESS_TOKEN)
        print("Comment result:", comment_result)
    elif choice == "4":
        comment_id = input("Enter the Comment ID to delete: ").strip()
        delete_comment_result = delete_facebook_comment(comment_id, PAGE_ACCESS_TOKEN)
        print('Delete comment result:', delete_comment_result)
    else:
        print("Invalid choice. Exiting.")