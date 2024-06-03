import base64
import os
from textwrap import dedent

from github.ContentFile import ContentFile
from github.PullRequest import PullRequest
from github.Repository import Repository
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.pydantic_v1 import BaseModel, Field, SecretStr


def get_updated_readme_content(
    diffs: list[dict[str, str]],
    readme_content: ContentFile,
    commit_messages: list[str],
    api_key: str,
) -> str:
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                dedent(
                    """
                        You are a senior software devloper.
                        You are working on a project with a team of developers.
                        Your task is to update the README file of the project, according to the changes made in a pull request.
                        You will be provided with
                        1. A list of changed files in the pull request, including the file name and the changes made.
                        2. The current content of the README file.
                        3. The commit messages associated with the pull request.
                        You need to generate the updated README file content based on the provided information.
                        You also need to provide a reason for your changes in the README file.
                    """
                ),
            ),
            (
                "human",
                "File changes:\n{diffs}\n\nReadme Content:\n{readme_content}\n\nCommit Messages:\n{commit_messages}",
            ),
        ]
    )

    formatted_diffs = "\n".join(
        [f"File: {diff['filename']}\nChanges:\n{diff['patch']}\n" for diff in diffs]
    )

    decoded_readme = base64.b64decode(readme_content.content).decode("utf-8")

    formatted_commit_messages = "\n".join(commit_messages)

    chat_model = ChatOpenAI(
        model="gpt-3.5-turbo", api_key=SecretStr(api_key), temperature=0
    )
    structured_llm = chat_model.with_structured_output(PromptResponse)

    prompt_with_input = prompt.invoke(
        {
            "diffs": formatted_diffs,
            "readme_content": decoded_readme,
            "commit_messages": formatted_commit_messages,
        }
    )
    print(f"Prompt with input: {prompt_with_input}")

    response = structured_llm.invoke(prompt_with_input)
    print(f"Received response: {response}")
    if not isinstance(response, PromptResponse):
        raise ValueError("The response is not a PromptResponse object.")
    return response.updated_readme


def update_readme_and_create_pr(
    repo: Repository, updated_readme: str, readme_sha: str
) -> PullRequest:
    commit_message = "AI Commit: Proposed README update based on recent code changes"

    commit_sha = os.environ["COMMIT_SHA"]
    main_branch = repo.get_branch("main")
    new_branch_name = f"update-readme-{commit_sha[:7]}"
    repo.create_git_ref(ref=f"refs/heads/{new_branch_name}", sha=main_branch.commit.sha)

    repo.update_file(
        path="README.md",
        message=commit_message,
        content=updated_readme,
        sha=readme_sha,
        branch=new_branch_name,
    )

    pr_title = "AI PR: Proposed README update based on recent code changes"
    pr_body = (
        "This PR proposes an update to the README file based on recent code changes."
    )
    pull_request = repo.create_pull(
        title=pr_title, body=pr_body, head=new_branch_name, base="main"
    )
    return pull_request


class PromptResponse(BaseModel):
    updated_readme: str = Field(description="The updated README content")
    reason: str = Field(description="The reason for the changes made in the README")
