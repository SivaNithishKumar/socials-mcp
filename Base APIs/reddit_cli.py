import os
import sys
import praw
import getpass
import json

# Helper to get credentials from env or prompt

def get_credential(env_name, prompt, secret=False):
    value = os.environ.get(env_name)
    if value:
        return value
    if secret:
        return getpass.getpass(prompt)
    return input(prompt)

CONFIG_FILE = os.path.expanduser('~/.reddit_cli_config.json')

def setup_credentials():
    print("\nCredential Setup:")
    creds = {}
    creds['client_id'] = input('Client ID: ')
    creds['client_secret'] = getpass.getpass('Client Secret: ')
    creds['username'] = input('Reddit Username: ')
    creds['password'] = getpass.getpass('Reddit Password: ')
    with open(CONFIG_FILE, 'w') as f:
        json.dump(creds, f)
    print(f"Credentials saved to {CONFIG_FILE}")

def load_credentials():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            creds = json.load(f)
        return creds
    return None

def get_reddit_instance():
    creds = load_credentials()
    if creds:
        client_id = creds['client_id']
        client_secret = creds['client_secret']
        username = creds['username']
        password = creds['password']
    else:
        print("Enter your Reddit API credentials (or set as environment variables):")
        client_id = get_credential('REDDIT_CLIENT_ID', 'Client ID: ')
        client_secret = get_credential('REDDIT_CLIENT_SECRET', 'Client Secret: ', secret=True)
        username = get_credential('REDDIT_USERNAME', 'Reddit Username: ')
        password = get_credential('REDDIT_PASSWORD', 'Reddit Password: ', secret=True)
    user_agent = f"RedditCLI by /u/{username}"
    try:
        reddit = praw.Reddit(
            client_id=client_id,
            client_secret=client_secret,
            username=username,
            password=password,
            user_agent=user_agent
        )
        # Test authentication
        _ = reddit.user.me()
        return reddit
    except Exception as e:
        print(f"Authentication failed: {e}")
        sys.exit(1)

def print_menu():
    print("\nReddit CLI Menu:")
    print("1. Credential setup (save credentials)")
    print("2. Get authenticated user information")
    print("3. List user's subscribed subreddits")
    print("4. List saved, upvoted, or downvoted posts/comments")
    print("5. List or browse posts in a subreddit")
    print("6. Search posts in a subreddit (Reddit Tools)")
    print("7. List posts by a user (Reddit Tools)")
    print("8. Get subreddit information")
    print("9. List recent comments in a subreddit")
    print("10. Submit a post to a subreddit (Reddit Tools)")
    print("11. Submit a comment to a post (Reddit Tools)")
    print("12. Vote on a post or comment (Reddit Tools)")
    print("13. Save or unsave a post or comment")
    print("14. Delete a post or comment")
    print("0. Exit")

def get_user_info(reddit):
    try:
        user = reddit.user.me()
        print(f"\nUsername: {user.name}")
        print(f"Link Karma: {user.link_karma}")
        print(f"Comment Karma: {user.comment_karma}")
    except Exception as e:
        print(f"Error: {e}")

def list_subscribed_subreddits(reddit):
    try:
        print("\nSubscribed subreddits:")
        for sub in reddit.user.subreddits(limit=20):
            print(f"- {sub.display_name}")
    except Exception as e:
        print(f"Error: {e}")

def list_user_activity(reddit):
    print("\nSelect activity type:")
    print("1. Saved")
    print("2. Upvoted")
    print("3. Downvoted")
    choice = input("Enter choice: ")
    try:
        if choice == '1':
            print("\nSaved items:")
            for item in reddit.user.me().saved(limit=10):
                print(f"- {item}")
        elif choice == '2':
            print("\nUpvoted items:")
            for item in reddit.user.me().upvoted(limit=10):
                print(f"- {item}")
        elif choice == '3':
            print("\nDownvoted items:")
            for item in reddit.user.me().downvoted(limit=10):
                print(f"- {item}")
        else:
            print("Invalid choice.")
    except Exception as e:
        print(f"Error: {e}")

def get_reddit_item(reddit, item_id):
    """Helper to get a Reddit submission or comment by ID."""
    if item_id.startswith('t1_'):
        return reddit.comment(id=item_id[3:])
    elif item_id.startswith('t3_'):
        return reddit.submission(id=item_id[3:])
    else:
        try:
            return reddit.submission(id=item_id)
        except:
            return reddit.comment(id=item_id)

def list_or_browse_subreddit(reddit):
    sub = input("Enter subreddit name: ")
    print("Sort by: 1. hot 2. new 3. top 4. rising")
    sort = input("Enter choice: ")
    try:
        subreddit = reddit.subreddit(sub)
        if sort == '1':
            posts = subreddit.hot(limit=10)
        elif sort == '2':
            posts = subreddit.new(limit=10)
        elif sort == '3':
            posts = subreddit.top(limit=10)
        elif sort == '4':
            posts = subreddit.rising(limit=10)
        else:
            print("Invalid sort.")
            return
        print(f"\nPosts in r/{sub}:")
        for post in posts:
            print(f"- [{post.id}] {post.title} (score: {post.score})")
    except Exception as e:
        print(f"Error: {e}")

def get_subreddit_info(reddit):
    sub = input("Enter subreddit name: ")
    try:
        subreddit = reddit.subreddit(sub)
        print(f"\nName: {subreddit.display_name}")
        print(f"Title: {subreddit.title}")
        print(f"Description: {subreddit.public_description}")
        print(f"Subscribers: {subreddit.subscribers}")
        print(f"NSFW: {subreddit.over18}")
    except Exception as e:
        print(f"Error: {e}")

def list_recent_comments(reddit):
    sub = input("Enter subreddit name: ")
    try:
        subreddit = reddit.subreddit(sub)
        print(f"\nRecent comments in r/{sub}:")
        for comment in subreddit.comments(limit=10):
            print(f"- [{comment.id}] {comment.author}: {comment.body[:80]}...")
    except Exception as e:
        print(f"Error: {e}")

def submit_post(reddit):
    sub = input("Enter subreddit name: ")
    title = input("Enter post title: ")
    text = input("Enter post text: ")
    try:
        subreddit = reddit.subreddit(sub)
        post = subreddit.submit(title, selftext=text)
        print(f"Post submitted: https://reddit.com{post.permalink}")
    except Exception as e:
        print(f"Error: {e}")

def submit_comment(reddit):
    post_id = input("Enter post ID: ")
    text = input("Enter comment text: ")
    try:
        submission = reddit.submission(id=post_id)
        comment = submission.reply(text)
        print(f"Comment submitted: https://reddit.com{comment.permalink}")
    except Exception as e:
        print(f"Error: {e}")

def vote_item(reddit):
    item_id = input("Enter post or comment ID: ")
    print("1. Upvote 2. Downvote")
    vote = input("Enter choice: ")
    try:
        item = get_reddit_item(reddit, item_id)
        if vote == '1':
            item.upvote()
            print("Upvoted.")
        elif vote == '2':
            item.downvote()
            print("Downvoted.")
        else:
            print("Invalid choice.")
    except Exception as e:
        print(f"Error: {e}")

def save_unsave_item(reddit):
    item_id = input("Enter post or comment ID: ")
    print("1. Save 2. Unsave")
    action = input("Enter choice: ")
    try:
        item = get_reddit_item(reddit, item_id)
        if action == '1':
            item.save()
            print("Saved.")
        elif action == '2':
            item.unsave()
            print("Unsaved.")
        else:
            print("Invalid choice.")
    except Exception as e:
        print(f"Error: {e}")

def delete_item(reddit):
    item_id = input("Enter post or comment ID: ")
    try:
        item = get_reddit_item(reddit, item_id)
        item.delete()
        print("Deleted (if permitted).")
    except Exception as e:
        print(f"Error: {e}")

def search_subreddit_posts(reddit):
    sub = input("Enter subreddit name: ")
    query = input("Enter search query: ")
    try:
        subreddit = reddit.subreddit(sub)
        print(f"\nSearch results in r/{sub} for '{query}':")
        for post in subreddit.search(query, limit=10):
            print(f"- [{post.id}] {post.title} (score: {post.score})")
    except Exception as e:
        print(f"Error: {e}")

def list_user_posts(reddit):
    user = input("Enter Reddit username: ")
    try:
        redditor = reddit.redditor(user)
        print(f"\nPosts by u/{user}:")
        for post in redditor.submissions.new(limit=10):
            print(f"- [{post.id}] {post.title} (score: {post.score}) in r/{post.subreddit}")
    except Exception as e:
        print(f"Error: {e}")

def main():
    reddit = None
    while True:
        print_menu()
        choice = input("Select a task by number: ")
        if choice == '1':
            setup_credentials()
            reddit = None
        else:
            if reddit is None:
                reddit = get_reddit_instance()
            if choice == '2':
                get_user_info(reddit)
            elif choice == '3':
                list_subscribed_subreddits(reddit)
            elif choice == '4':
                list_user_activity(reddit)
            elif choice == '5':
                list_or_browse_subreddit(reddit)
            elif choice == '6':
                search_subreddit_posts(reddit)
            elif choice == '7':
                list_user_posts(reddit)
            elif choice == '8':
                get_subreddit_info(reddit)
            elif choice == '9':
                list_recent_comments(reddit)
            elif choice == '10':
                submit_post(reddit)
            elif choice == '11':
                submit_comment(reddit)
            elif choice == '12':
                vote_item(reddit)
            elif choice == '13':
                save_unsave_item(reddit)
            elif choice == '14':
                delete_item(reddit)
            elif choice == '0':
                print("Goodbye!")
                break
            else:
                print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main() 