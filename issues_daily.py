import requests
import datetime
import os
import subprocess
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# GitHub API token
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
HEADERS = {
    'Authorization': f'token {GITHUB_TOKEN}',
    'Accept': 'application/vnd.github.v3+json'
}

# Query parameters
LABELS = ["documentation", "good first issue", "help wanted", "duplicate", "question"]
LANGUAGES = ["python", "javascript"]
CREATED_AFTER = "2024-10-01"  # Only include issues created on or after this date
ISSUES_PER_DAY = 20

def fetch_issues():
    issues = []
    for label in LABELS:
        for language in LANGUAGES:
            # GitHub API search query with additional filters for forks and stars
            query = f"label:{label} language:{language} is:issue is:open created:>={CREATED_AFTER} stars:>10 forks:>10"
            url = f"https://api.github.com/search/issues?q={query}&per_page={ISSUES_PER_DAY}"
            
            response = requests.get(url, headers=HEADERS)
            if response.status_code == 200:
                results = response.json().get('items', [])
                issues.extend(results)
            else:
                print(f"Failed to fetch issues for label '{label}' and language '{language}'. Status code: {response.status_code}")
    return issues[:ISSUES_PER_DAY]  # Return only up to ISSUES_PER_DAY issues

def save_issues_to_md(issues):
    # Ensure the issues directory exists
    issues_dir = "issues"
    if not os.path.exists(issues_dir):
        os.makedirs(issues_dir)
    
    # Create a new MD file with date and time in the filename
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = os.path.join(issues_dir, f"issues_{timestamp}.md")
    with open(filename, "w") as file:
        file.write(f"# GitHub Issues for {timestamp}\n\n")
        for issue in issues:
            title = issue.get('title', 'No Title')
            url = issue.get('html_url', 'No URL')
            repo = issue.get('repository_url', 'No Repository').replace("https://api.github.com/repos/", "")
            labels = ', '.join([label['name'] for label in issue.get('labels', [])])
            description = issue.get('body')[:200] if issue.get('body') else "No description provided."
            
            file.write(f"## [{title}]({url})\n")
            file.write(f"Repository: [{repo}](https://github.com/{repo})\n\n")
            file.write(f"Labels: {labels}\n\n")
            file.write(f"Description: {description}...\n\n")
            file.write("---\n\n")
    print(f"Issues saved to {filename}")
    return filename

def commit_to_repo(filename):
    # Create a timestamp and details for the commit message
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    labels_str = ', '.join(LABELS)
    languages_str = ', '.join(LANGUAGES)
    
    # Detailed commit message
    commit_message = (
        f"Added issues collected on {timestamp}\n\n"
        f"Filters applied:\n"
        f"  - Labels: {labels_str}\n"
        f"  - Languages: {languages_str}\n"
        f"  - Created after: {CREATED_AFTER}\n\n"
        f"Filename: {filename}"
    )
    
    # Configure Git
    subprocess.run(["git", "config", "--global", "user.name", "github-actions[bot]"])
    subprocess.run(["git", "config", "--global", "user.email", "github-actions[bot]@users.noreply.github.com"])

    # Add, commit, and push the file
    subprocess.run(["git", "add", filename])
    subprocess.run(["git", "commit", "-m", commit_message])
    subprocess.run(["git", "push"])

def main():
    print("Fetching issues...")
    issues = fetch_issues()
    filename = save_issues_to_md(issues)
    commit_to_repo(filename)

if __name__ == "__main__":
    main()
