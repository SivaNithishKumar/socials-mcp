import requests
import time
import os

# --- ImageKit Upload Functionality ---
def upload_to_imagekit(file_path, imagekit_private_key, imagekit_public_key, imagekit_url_endpoint):
    """
    Uploads a local image to ImageKit.io and returns the public URL.
    """
    url = "https://upload.imagekit.io/api/v1/files/upload"
    with open(file_path, 'rb') as f:
        files = {'file': f}
        data = {
            'fileName': os.path.basename(file_path),
            'publicKey': 'public_ZqbLqgivgJLf20hHkNa9ImSYdxI=',
            'useUniqueFileName': 'true',
        }
        response = requests.post(url, files=files, data=data, auth=(imagekit_private_key, ''))
    if response.status_code == 200:
        result = response.json()
        return result['url']
    else:
        print('Failed to upload to ImageKit:', response.text)
        return None

# Fill these with your own values or prompt the user
ACCESS_TOKEN = 'EAAKcZBszUwtwBO9wUkZCTo104TjSVecbRm60E24RRIuCzAioO6ZCZC9SSOnf5150mfYvA82Vx5KnYWCPJywtqVDyXNjZB4KrzbAWbUdZCzTBsynZA1YaQZBgBoiyS5GbACek2a8YHyo9nRzzM30had0u6RuDr4mgR4UxeuKktlU1DhDjOP6GsYBlsbGhjOT0kJaHY0SwkhjSbvvMbpUfF0rIZALQ7Pu1YkM4H'
INSTAGRAM_ACCOUNT_ID = 17841475454727947

# --- Prompt for ImageKit credentials and image file ---
imagekit_private_key = 'private_KCsGLka74kV1xLn2G106h+gT+kE='
imagekit_public_key = 'public_ZqbLqgivgJLf20hHkNa9ImSYdxI='
imagekit_url_endpoint = 'https://ik.imagekit.io/knekyuh5x'

choice = input("Do you want to create, continue, delete, comment, or delete_comment? (create/continue/delete/comment/delete_comment): ").strip().lower()

if choice == 'create':
    file_path = input("Enter the local path to the image you want to upload: ").strip()
    # Upload to ImageKit and get the public URL
    IMAGE_URL = upload_to_imagekit(file_path, imagekit_private_key, imagekit_public_key, imagekit_url_endpoint)
    if not IMAGE_URL:
        print("Image upload failed. Exiting.")
        exit(1)
    CAPTION = input("Enter the caption for your Instagram post: ").strip()
    post_type = input("Do you want to post directly or post in container? (direct/container): ").strip().lower()
    # Step 1: Create a media object (container)
    create_media_url = f'https://graph.facebook.com/v19.0/{INSTAGRAM_ACCOUNT_ID}/media'
    media_payload = {
        'image_url': IMAGE_URL,
        'caption': CAPTION,
        'access_token': ACCESS_TOKEN
    }
    media_response = requests.post(create_media_url, data=media_payload)
    media_result = media_response.json()
    print('Media creation response:', media_result)

    if 'id' in media_result:
        container_id = media_result['id']
        print(f"Media container created. Container ID: {container_id}")
        if post_type == 'direct':
            # Step 2: Publish the media object
            publish_url = f'https://graph.facebook.com/v19.0/{INSTAGRAM_ACCOUNT_ID}/media_publish'
            publish_payload = {
                'creation_id': container_id,
                'access_token': ACCESS_TOKEN
            }
            for i in range(10):
                publish_response = requests.post(publish_url, data=publish_payload)
                publish_result = publish_response.json()
                print('Publish attempt', i+1, ':', publish_result)
                if 'id' in publish_result:
                    print('Post published successfully! Post ID:', publish_result['id'])
                    break
                time.sleep(2)
            else:
                print('Failed to publish post after several attempts.')
        elif post_type == 'container':
            print('Image is only uploaded to the container and not published.')
        else:
            print("Invalid post type. Please enter 'direct' or 'container'.")
    else:
        print('Failed to create media container.')

elif choice == 'continue':
    container_id = input("Enter the existing Instagram media container ID to publish: ").strip()
    publish_url = f'https://graph.facebook.com/v19.0/{INSTAGRAM_ACCOUNT_ID}/media_publish'
    publish_payload = {
        'creation_id': container_id,
        'access_token': ACCESS_TOKEN
    }
    for i in range(10):
        publish_response = requests.post(publish_url, data=publish_payload)
        publish_result = publish_response.json()
        print('Publish attempt', i+1, ':', publish_result)
        if 'id' in publish_result:
            print('Post published successfully! Post ID:', publish_result['id'])
            break
        time.sleep(2)
    else:
        print('Failed to publish post after several attempts.')

elif choice == 'delete':
    print("Note: You can only delete containers that have NOT been published. Published posts must be deleted manually in the Instagram app.")
    container_id = input("Enter the Instagram media container ID to delete (unpublished only): ").strip()
    delete_url = f'https://graph.facebook.com/v19.0/{container_id}'
    delete_payload = {
        'access_token': ACCESS_TOKEN
    }
    delete_response = requests.delete(delete_url, params=delete_payload)
    try:
        delete_result = delete_response.json()
    except Exception:
        print("Failed to parse delete response. Raw response:", delete_response.text)
        exit(1)
    print('Delete response:', delete_result)
    if delete_result.get('success'):
        print('Container deleted successfully!')
    else:
        print('Failed to delete the container. This may be because the container was already published, expired, or you lack permissions. If this is a published post, it cannot be deleted via the API. See: https://developers.facebook.com/docs/instagram-api/reference/media#delete')

elif choice == 'comment':
    media_id = input("Enter the Instagram media (post) ID to comment on: ").strip()
    comment_text = input("Enter your comment: ").strip()
    comment_url = f'https://graph.facebook.com/v19.0/{media_id}/comments'
    comment_payload = {
        'message': comment_text,
        'access_token': ACCESS_TOKEN
    }
    comment_response = requests.post(comment_url, data=comment_payload)
    comment_result = comment_response.json()
    print('Comment response:', comment_result)
    if 'id' in comment_result:
        print('Comment posted successfully! Comment ID:', comment_result['id'])
    else:
        print('Failed to post comment.')

elif choice == 'delete_comment':
    comment_id = input("Enter the comment ID to delete: ").strip()
    delete_comment_url = f'https://graph.facebook.com/v19.0/{comment_id}'
    delete_comment_payload = {
        'access_token': ACCESS_TOKEN
    }
    delete_comment_response = requests.delete(delete_comment_url, params=delete_comment_payload)
    try:
        delete_comment_result = delete_comment_response.json()
    except Exception:
        print("Failed to parse delete comment response. Raw response:", delete_comment_response.text)
        exit(1)
    print('Delete comment response:', delete_comment_result)
    if delete_comment_result.get('success'):
        print('Comment deleted successfully!')
    else:
        print('Failed to delete the comment. Make sure the comment ID is correct and you have permission to delete it.')
else:
    print("Invalid choice. Please enter 'create', 'continue', 'delete', 'comment', or 'delete_comment'.")
