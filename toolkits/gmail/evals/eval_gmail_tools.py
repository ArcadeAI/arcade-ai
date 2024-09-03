from arcade_gmail.tools.gmail import (
    DateRange,
    get_emails,
    search_emails_by_header,
    write_draft,
)

from arcade.sdk.eval import (
    BinaryCritic,
    EvalRubric,
    EvalSuite,
    NumericCritic,
    SimilarityCritic,
    tool_eval,
)

# Evaluation rubric
rubric = EvalRubric(
    name="Gmail Tools Rubric",
    fail_threshold=0.7,
    warn_threshold=0.9,
)


@tool_eval("gpt-3.5-turbo", "gpt-4o")
def gmail_eval_suite():
    suite = EvalSuite(
        name="Gmail Tools Evaluation",
        system="You are an AI assistant with access to Gmail tools. Use them to help the user with their email-related tasks.",
    )

    # Register the Gmail tools
    suite.register_tool(write_draft)
    suite.register_tool(search_emails_by_header)
    suite.register_tool(get_emails)

    # Write Draft Scenarios
    suite.add_case(
        user_message="Draft and email to john@example.com asking if we can meet tomorrow at 2 PM",
        expected_tool="WriteDraft",
        expected_tool_args={
            "recipient": "john@example.com",
            "subject": "Meeting Tomorrow",
            "body": "Hi John, Can we meet tomorrow at 2 PM? Thanks, Alice",
        },
        rubric=rubric,
        critics=[
            BinaryCritic(critic_field="recipient", weight=0.5),
            SimilarityCritic(critic_field="subject", weight=0.2),
            SimilarityCritic(critic_field="body", weight=0.3),
        ],
    )

    # Search Emails by Header Scenarios
    suite.add_case(
        user_message="Find emails from alice@example.com sent last week",
        expected_tool="SearchEmailsByHeader",
        expected_tool_args={
            "sender": "alice@example.com",
            "date_range": DateRange.LAST_7_DAYS,
            "limit": 25,
        },
        rubric=rubric,
        critics=[
            BinaryCritic(critic_field="sender", weight=0.5),
            BinaryCritic(critic_field="date_range", weight=0.4),
            NumericCritic(critic_field="limit", weight=0.1, value_range=(1, 100)),
        ],
    )

    suite.add_case(
        user_message="Search for emails with 'Urgent' in the subject from the last 30 days",
        expected_tool="SearchEmailsByHeader",
        expected_tool_args={
            "subject": "Urgent",
            "date_range": DateRange.LAST_30_DAYS,
            "limit": 25,
        },
        rubric=rubric,
        critics=[
            SimilarityCritic(critic_field="subject", weight=0.4),
            BinaryCritic(critic_field="date_range", weight=0.4),
            NumericCritic(critic_field="limit", weight=0.2, value_range=(1, 100)),
        ],
    )

    suite.extend_case(
        user_message="show me more of those",
        expected_tool_args={
            "subject": "Urgent",
            "date_range": DateRange.LAST_30_DAYS,
            "limit": 50,
        },
    )

    suite.add_case(
        user_message="Retrieve the last 10 emails in my inbox",
        expected_tool="GetEmails",
        expected_tool_args={"n_emails": 10},
        rubric=rubric,
        critics=[
            BinaryCritic(critic_field="n_emails", weight=0.8),
            NumericCritic(critic_field="n_emails", weight=0.2, value_range=(1, 20)),
        ],
    )

    return suite
