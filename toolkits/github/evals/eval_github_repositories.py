import arcade_github
from arcade_github.tools.repositories import (
    count_stargazers,
    get_repository,
    list_org_repositories,
    list_repository_activities,
    list_review_comments_in_a_repository,
    search_issues,
)

from arcade.core.catalog import ToolCatalog
from arcade.sdk.eval import (
    BinaryCritic,
    EvalRubric,
    EvalSuite,
    tool_eval,
)

# Evaluation rubric
rubric = EvalRubric(
    fail_threshold=0.8,
    warn_threshold=0.9,
)

catalog = ToolCatalog()
# Register the GitHub tools
catalog.add_module(arcade_github)


@tool_eval()
def github_repositories_eval_suite() -> EvalSuite:
    """Evaluation suite for GitHub Repositories tools."""
    suite = EvalSuite(
        name="GitHub Repositories Tools Evaluation Suite",
        system_message="You are an AI assistant that helps users interact with GitHub repositories using the provided tools.",
        catalog=catalog,
        rubric=rubric,
    )

    # Search Issues
    suite.add_case(
        name="Search issues in a repository",
        user_message="Search for open issues in the 'ArcadeAI/test' repo with the query 'bug'.",
        expected_tool_calls=[
            (
                search_issues,
                {
                    "owner": "ArcadeAI",
                    "name": "test",
                    "query": "bug",
                    "limit": 10,
                },
            )
        ],
        critics=[
            BinaryCritic(critic_field="owner", weight=0.3),
            BinaryCritic(critic_field="name", weight=0.3),
            BinaryCritic(critic_field="query", weight=0.3),
        ],
    )

    # Count Stargazers
    suite.add_case(
        name="Count stargazers of a repository",
        user_message="How many stargazers does the ArcadeAI/test repo have?",
        expected_tool_calls=[
            (
                count_stargazers,
                {
                    "owner": "ArcadeAI",
                    "name": "test",
                },
            )
        ],
        critics=[
            BinaryCritic(critic_field="owner", weight=0.5),
            BinaryCritic(critic_field="name", weight=0.5),
        ],
    )

    # List an Organization's Repositories
    suite.add_case(
        name="List repositories in an organization",
        user_message="List all repos in the ArcadeAI org, sorted by creation date in descending order.",
        expected_tool_calls=[
            (
                list_org_repositories,
                {
                    "org": "ArcadeAI",
                    "repo_type": "all",
                    "sort": "created",
                    "sort_direction": "desc",
                },
            )
        ],
        critics=[
            BinaryCritic(critic_field="org", weight=0.1),
            BinaryCritic(critic_field="repo_type", weight=0.1),
            BinaryCritic(critic_field="sort", weight=0.1),
            BinaryCritic(critic_field="sort_direction", weight=0.1),
        ],
    )

    # Get Repository
    suite.add_case(
        name="Get details of a repository",
        user_message="Tell me about the test repo owned by ArcadeAI.",
        expected_tool_calls=[
            (
                get_repository,
                {
                    "owner": "ArcadeAI",
                    "repo": "test",
                    "include_extra_data": False,
                },
            )
        ],
        critics=[
            BinaryCritic(critic_field="owner", weight=0.3),
            BinaryCritic(critic_field="repo", weight=0.3),
        ],
    )

    # List Repository Activities
    suite.add_case(
        name="List activities in a repository",
        user_message="List all PR merges in the 'ArcadeAI/test' repository that were performed by TestUser in the last month",
        expected_tool_calls=[
            (
                list_repository_activities,
                {
                    "owner": "ArcadeAI",
                    "repo": "test",
                    "direction": "desc",
                    "per_page": 30,
                    "actor": "TestUser",
                    "time_period": "month",
                    "activity_type": "pr_merge",
                    "include_extra_data": False,
                },
            )
        ],
        critics=[
            BinaryCritic(critic_field="owner", weight=0.1),
            BinaryCritic(critic_field="repo", weight=0.1),
            BinaryCritic(critic_field="direction", weight=0.1),
            BinaryCritic(critic_field="actor", weight=0.1),
            BinaryCritic(critic_field="time_period", weight=0.1),
            BinaryCritic(critic_field="activity_type", weight=0.1),
        ],
    )

    # List Review Comments in a Repository
    suite.add_case(
        name="List review comments in a repository",
        user_message="List all review comments in the 'ArcadeAI/test' repository, sorted by creation date in descending order.",
        expected_tool_calls=[
            (
                list_review_comments_in_a_repository,
                {
                    "owner": "ArcadeAI",
                    "repo": "test",
                    "sort": "created",
                    "direction": "desc",
                    "per_page": 30,
                    "page": 1,
                    "include_extra_data": False,
                },
            )
        ],
        critics=[
            BinaryCritic(critic_field="owner", weight=0.2),
            BinaryCritic(critic_field="repo", weight=0.2),
            BinaryCritic(critic_field="sort", weight=0.1),
            BinaryCritic(critic_field="direction", weight=0.1),
        ],
    )

    return suite
