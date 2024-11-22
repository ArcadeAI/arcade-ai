# Github Toolkit


|             |                |
|-------------|----------------|
| Name        | github |
| Package     | arcade_github |
| Repository  | None   |
| Version     | 0.1.2      |
| Description | LLM tools for interacting with Github  |
| Author      | dev@arcade-ai.com      |


| Tool Name   | Description                                                             |
|-------------|-------------------------------------------------------------------------|
| CreateIssue | Create an issue in a GitHub repository. |
| CreateIssueComment | Create a comment on an issue in a GitHub repository. |
| SetStarred | Star or un-star a GitHub repository. |
| ListStargazers | List the stargazers for a GitHub repository. |
| CountStargazers | Count the number of stargazers (stars) for a GitHub repository. |
| ListOrgRepositories | List repositories for the specified organization. |
| GetRepository | Get a repository. |
| ListRepositoryActivities | List repository activities. |
| ListReviewCommentsInARepository | List review comments in a GitHub repository. |
| ListPullRequests | List pull requests in a GitHub repository. |
| GetPullRequest | Get details of a pull request in a GitHub repository. |
| UpdatePullRequest | Update a pull request in a GitHub repository. |
| ListPullRequestCommits | List commits (from oldest to newest) on a pull request in a GitHub repository. |
| CreateReplyForReviewComment | Create a reply to a review comment for a pull request. |
| ListReviewCommentsOnPullRequest | List review comments on a pull request in a GitHub repository. |
| CreateReviewComment | Create a review comment for a pull request in a GitHub repository. |


### CreateIssue
Create an issue in a GitHub repository.

Example:
```
create_issue(owner="octocat", repo="Hello-World", title="Found a bug", body="I'm having a problem with this.", assignees=["octocat"], milestone=1, labels=["bug"])
```

#### Parameters
- `owner`*(string, required)* The account owner of the repository. The name is not case sensitive.
- `repo`*(string, required)* The name of the repository without the .git extension. The name is not case sensitive.
- `title`*(string, required)* The title of the issue.
- `body`*(string, optional)* The contents of the issue.
- `assignees`*(array, optional)* Logins for Users to assign to this issue.
- `milestone`*(integer, optional)* The number of the milestone to associate this issue with.
- `labels`*(array, optional)* Labels to associate with this issue.
- `include_extra_data`*(boolean, optional)* If true, return all the data available about the pull requests. This is a large payload and may impact performance - use with caution.

---

### CreateIssueComment
Create a comment on an issue in a GitHub repository.

Example:
```
create_issue_comment(owner="octocat", repo="Hello-World", issue_number=1347, body="Me too")
```

#### Parameters
- `owner`*(string, required)* The account owner of the repository. The name is not case sensitive.
- `repo`*(string, required)* The name of the repository without the .git extension. The name is not case sensitive.
- `issue_number`*(integer, required)* The number that identifies the issue.
- `body`*(string, required)* The contents of the comment.
- `include_extra_data`*(boolean, optional)* If true, return all the data available about the pull requests. This is a large payload and may impact performance - use with caution.

---

### SetStarred
Star or un-star a GitHub repository.
For example, to star microsoft/vscode, you would use:
```
set_starred(owner="microsoft", name="vscode", starred=True)
```

#### Parameters
- `owner`*(string, required)* The owner of the repository
- `name`*(string, required)* The name of the repository
- `starred`*(boolean, required)* Whether to star the repository or not

---

### ListStargazers
List the stargazers for a GitHub repository.

#### Parameters
- `owner`*(string, required)* The owner of the repository
- `repo`*(string, required)* The name of the repository
- `limit`*(integer, optional)* The maximum number of stargazers to return. If not provided, all stargazers will be returned.

---

### CountStargazers
Count the number of stargazers (stars) for a GitHub repository.
For example, to count the number of stars for microsoft/vscode, you would use:
```
count_stargazers(owner="microsoft", name="vscode")
```

#### Parameters
- `owner`*(string, required)* The owner of the repository
- `name`*(string, required)* The name of the repository

---

### ListOrgRepositories
List repositories for the specified organization.

#### Parameters
- `org`*(string, required)* The organization name. The name is not case sensitive
- `repo_type`*(string, optional)* The types of repositories you want returned., Valid values are 'all', 'public', 'private', 'forks', 'sources', 'member'
- `sort`*(string, optional)* The property to sort the results by, Valid values are 'created', 'updated', 'pushed', 'full_name'
- `sort_direction`*(string, optional)* The order to sort by, Valid values are 'asc', 'desc'
- `per_page`*(integer, optional)* The number of results per page
- `page`*(integer, optional)* The page number of the results to fetch
- `include_extra_data`*(boolean, optional)* If true, return all the data available about the pull requests. This is a large payload and may impact performance - use with caution.

---

### GetRepository
Get a repository.

Retrieves detailed information about a repository using the GitHub API.

Example:
```
get_repository(owner="octocat", repo="Hello-World")
```

#### Parameters
- `owner`*(string, required)* The account owner of the repository. The name is not case sensitive.
- `repo`*(string, required)* The name of the repository without the .git extension. The name is not case sensitive.
- `include_extra_data`*(boolean, optional)* If true, return all the data available about the pull requests. This is a large payload and may impact performance - use with caution.

---

### ListRepositoryActivities
List repository activities.

Retrieves a detailed history of changes to a repository, such as pushes, merges, force pushes, and branch changes,
and associates these changes with commits and users.

Example:
```
list_repository_activities(
    owner="octocat",
    repo="Hello-World",
    per_page=10,
    activity_type="force_push"
)
```

#### Parameters
- `owner`*(string, required)* The account owner of the repository. The name is not case sensitive.
- `repo`*(string, required)* The name of the repository without the .git extension. The name is not case sensitive.
- `direction`*(string, optional)* The direction to sort the results by., Valid values are 'asc', 'desc'
- `per_page`*(integer, optional)* The number of results per page (max 100).
- `before`*(string, optional)* A cursor (unique identifier, e.g., a SHA of a commit) to search for results before this cursor.
- `after`*(string, optional)* A cursor (unique identifier, e.g., a SHA of a commit) to search for results after this cursor.
- `ref`*(string, optional)* The Git reference for the activities you want to list. The ref for a branch can be formatted either as refs/heads/BRANCH_NAME or BRANCH_NAME, where BRANCH_NAME is the name of your branch.
- `actor`*(string, optional)* The GitHub username to filter by the actor who performed the activity.
- `time_period`*(string, optional)* The time period to filter by., Valid values are 'day', 'week', 'month', 'quarter', 'year'
- `activity_type`*(string, optional)* The activity type to filter by., Valid values are 'push', 'force_push', 'branch_creation', 'branch_deletion', 'pr_merge', 'merge_queue_merge'
- `include_extra_data`*(boolean, optional)* If true, return all the data available about the pull requests. This is a large payload and may impact performance - use with caution.

---

### ListReviewCommentsInARepository
List review comments in a GitHub repository.

Example:
```
list_review_comments(owner="octocat", repo="Hello-World", sort="created", direction="asc")
```

#### Parameters
- `owner`*(string, required)* The account owner of the repository. The name is not case sensitive.
- `repo`*(string, required)* The name of the repository without the .git extension. The name is not case sensitive.
- `sort`*(string, optional)* Can be one of: created, updated., Valid values are 'created', 'updated'
- `direction`*(string, optional)* The direction to sort results. Ignored without sort parameter. Can be one of: asc, desc., Valid values are 'asc', 'desc'
- `since`*(string, optional)* Only show results that were last updated after the given time. This is a timestamp in ISO 8601 format: YYYY-MM-DDTHH:MM:SSZ.
- `per_page`*(integer, optional)* The number of results per page (max 100).
- `page`*(integer, optional)* The page number of the results to fetch.
- `include_extra_data`*(boolean, optional)* If true, return all the data available about the pull requests. This is a large payload and may impact performance - use with caution.

---

### ListPullRequests
List pull requests in a GitHub repository.

Example:
```
list_pull_requests(owner="octocat", repo="Hello-World", state=PRState.OPEN, sort=PRSort.UPDATED)
```

#### Parameters
- `owner`*(string, required)* The account owner of the repository. The name is not case sensitive.
- `repo`*(string, required)* The name of the repository without the .git extension. The name is not case sensitive.
- `state`*(string, optional)* The state of the pull requests to return., Valid values are 'open', 'closed', 'all'
- `head`*(string, optional)* Filter pulls by head user or head organization and branch name in the format of user:ref-name or organization:ref-name.
- `base`*(string, optional)* Filter pulls by base branch name.
- `sort`*(string, optional)* The property to sort the results by., Valid values are 'created', 'updated', 'popularity', 'long-running'
- `direction`*(string, optional)* The direction of the sort., Valid values are 'asc', 'desc'
- `per_page`*(integer, optional)* The number of results per page (max 100).
- `page`*(integer, optional)* The page number of the results to fetch.
- `include_extra_data`*(boolean, optional)* If true, return all the data available about the pull requests. This is a large payload and may impact performance - use with caution.

---

### GetPullRequest
Get details of a pull request in a GitHub repository.

Example:
```
get_pull_request(owner="octocat", repo="Hello-World", pull_number=1347)
```

#### Parameters
- `owner`*(string, required)* The account owner of the repository. The name is not case sensitive.
- `repo`*(string, required)* The name of the repository without the .git extension. The name is not case sensitive.
- `pull_number`*(integer, required)* The number that identifies the pull request.
- `include_diff_content`*(boolean, optional)* If true, return the diff content of the pull request.
- `include_extra_data`*(boolean, optional)* If true, return all the data available about the pull requests. This is a large payload and may impact performance - use with caution.

---

### UpdatePullRequest
Update a pull request in a GitHub repository.

Example:
```
update_pull_request(owner="octocat", repo="Hello-World", pull_number=1347, title="new title", body="updated body")
```

#### Parameters
- `owner`*(string, required)* The account owner of the repository. The name is not case sensitive.
- `repo`*(string, required)* The name of the repository without the .git extension. The name is not case sensitive.
- `pull_number`*(integer, required)* The number that identifies the pull request.
- `title`*(string, optional)* The title of the pull request.
- `body`*(string, optional)* The contents of the pull request.
- `state`*(string, optional)* State of this Pull Request. Either open or closed., Valid values are 'open', 'closed', 'all'
- `base`*(string, optional)* The name of the branch you want your changes pulled into.
- `maintainer_can_modify`*(boolean, optional)* Indicates whether maintainers can modify the pull request.

---

### ListPullRequestCommits
List commits (from oldest to newest) on a pull request in a GitHub repository.

Example:
```
list_pull_request_commits(owner="octocat", repo="Hello-World", pull_number=1347)
```

#### Parameters
- `owner`*(string, required)* The account owner of the repository. The name is not case sensitive.
- `repo`*(string, required)* The name of the repository without the .git extension. The name is not case sensitive.
- `pull_number`*(integer, required)* The number that identifies the pull request.
- `per_page`*(integer, optional)* The number of results per page (max 100).
- `page`*(integer, optional)* The page number of the results to fetch.
- `include_extra_data`*(boolean, optional)* If true, return all the data available about the pull requests. This is a large payload and may impact performance - use with caution.

---

### CreateReplyForReviewComment
Create a reply to a review comment for a pull request.

Example:
```
create_reply_for_review_comment(owner="octocat", repo="Hello-World", pull_number=1347, comment_id=42, body="Looks good to me!")
```

#### Parameters
- `owner`*(string, required)* The account owner of the repository. The name is not case sensitive.
- `repo`*(string, required)* The name of the repository without the .git extension. The name is not case sensitive.
- `pull_number`*(integer, required)* The number that identifies the pull request.
- `comment_id`*(integer, required)* The unique identifier of the comment.
- `body`*(string, required)* The text of the review comment.

---

### ListReviewCommentsOnPullRequest
List review comments on a pull request in a GitHub repository.

Example:
```
list_review_comments_on_pull_request(owner="octocat", repo="Hello-World", pull_number=1347)
```

#### Parameters
- `owner`*(string, required)* The account owner of the repository. The name is not case sensitive.
- `repo`*(string, required)* The name of the repository without the .git extension. The name is not case sensitive.
- `pull_number`*(integer, required)* The number that identifies the pull request.
- `sort`*(string, optional)* The property to sort the results by. Can be one of: created, updated., Valid values are 'created', 'updated'
- `direction`*(string, optional)* The direction to sort results. Can be one of: asc, desc., Valid values are 'asc', 'desc'
- `since`*(string, optional)* Only show results that were last updated after the given time. This is a timestamp in ISO 8601 format: YYYY-MM-DDTHH:MM:SSZ.
- `per_page`*(integer, optional)* The number of results per page (max 100).
- `page`*(integer, optional)* The page number of the results to fetch.
- `include_extra_data`*(boolean, optional)* If true, return all the data available about the pull requests. This is a large payload and may impact performance - use with caution.

---

### CreateReviewComment
Create a review comment for a pull request in a GitHub repository.

If the subject_type is not 'file', then the start_line and end_line parameters are required.
If the subject_type is 'file', then the start_line and end_line parameters are ignored.
If the commit_id is not provided, the latest commit SHA of the PR's base branch will be used.

Example:
```
create_review_comment(owner="octocat", repo="Hello-World", pull_number=1347, body="Great stuff!", commit_id="6dcb09b5b57875f334f61aebed695e2e4193db5e", path="file1.txt", line=2, side="RIGHT")
```

#### Parameters
- `owner`*(string, required)* The account owner of the repository. The name is not case sensitive.
- `repo`*(string, required)* The name of the repository without the .git extension. The name is not case sensitive.
- `pull_number`*(integer, required)* The number that identifies the pull request.
- `body`*(string, required)* The text of the review comment.
- `path`*(string, required)* The relative path to the file that necessitates a comment.
- `commit_id`*(string, optional)* The SHA of the commit needing a comment. If not provided, the latest commit SHA of the PR's base branch will be used.
- `start_line`*(integer, optional)* The start line of the range of lines in the pull request diff that the comment applies to. Required unless 'subject_type' is 'file'.
- `end_line`*(integer, optional)* The end line of the range of lines in the pull request diff that the comment applies to. Required unless 'subject_type' is 'file'.
- `side`*(string, optional)* The side of the diff that the pull request's changes appear on. Use LEFT for deletions that appear in red. Use RIGHT for additions that appear in green or unchanged lines that appear in white and are shown for context, Valid values are 'LEFT', 'RIGHT'
- `start_side`*(string, optional)* The starting side of the diff that the comment applies to.
- `subject_type`*(string, optional)* The type of subject that the comment applies to. Can be one of: file, hunk, or line., Valid values are 'file', 'line'
- `include_extra_data`*(boolean, optional)* If true, return all the data available about the review comment. This is a large payload and may impact performance - use with caution.
