import {{ package_name }}
from {{ package_name }}.tools.hello import say_hello

from arcade.sdk import ToolCatalog
from arcade.sdk.eval import (
    EvalRubric,
    EvalSuite,
    SimilarityCritic,
    tool_eval,
)

# Evaluation rubric
rubric = EvalRubric(
    fail_threshold=0.85,
    warn_threshold=0.95,
)


catalog = ToolCatalog()
catalog.add_module({{ package_name }})


@tool_eval()
def {{ toolkit_name }}_eval_suite() -> EvalSuite:  # type: ignore[no-any-unimported]
    suite = EvalSuite(
        name="{{ toolkit_name }} Tools Evaluation",
        system_message="You are an AI assistant with access to {{ toolkit_name }} tools. Use them to help the user with their tasks.",
        catalog=catalog,
        rubric=rubric,
    )

    suite.add_case(
        name="Saying hello",
        user_message="He's actually right here, say hi to him!",
        expected_tool_calls=[
            (
                say_hello,
                {
                    "name": "John Doe"
                }
            )
        ],
        rubric=rubric,
        critics=[
            SimilarityCritic(critic_field="name", weight=0.5),
        ],
        additional_messages=[
            { "role": "user", "content": "My friend's name is John Doe." },
            { "role": "assistant", "content": "It is great that you have a friend named John Doe!" },
        ]
    )

    return suite