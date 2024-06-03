import os

from github import Github
from github.ContentFile import ContentFile

from utility import get_updated_readme_content, update_readme_and_create_pr


def main():
    # Initialize GitHub API with token
    g = Github(os.getenv("GITHUB_TOKEN"))

    # Get the repo path and PR number from the environment variables
    repo_path = os.environ["REPO_PATH"]
    pull_request_number = int(os.environ["PR_NUMBER"])

    api_key = os.environ["OPENAI_API_KEY"]

    # Get the repo object
    repo = g.get_repo(repo_path)

    # Fetch README content (assuming README.md)
    readme_content = repo.get_contents("README.md")
    if not isinstance(readme_content, ContentFile):
        raise ValueError("The content is not a ContentFile object.")

    # print(readme_content)
    # Fetch pull request by number
    pull_request = repo.get_pull(pull_request_number)

    # Get the diffs of the pull request
    pull_request_diffs: list[dict[str, str]] = [
        {"filename": file.filename, "patch": file.patch}
        for file in pull_request.get_files()
    ]

    # Get the commit messages associated with the pull request
    commit_messages = [commit.commit.message for commit in pull_request.get_commits()]

    # Call OpenAI to generate the updated README content
    updated_readme = get_updated_readme_content(
        pull_request_diffs, readme_content, commit_messages, api_key
    )

    # Create PR for Updated PR
    update_readme_and_create_pr(repo, updated_readme, readme_content.sha)


if __name__ == "__main__":
    main()
