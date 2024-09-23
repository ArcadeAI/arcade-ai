from __future__ import annotations
from pydantic import BaseModel, Field
from typing import List, Union, Optional, Annotated, Literal
from enum import Enum


class Language(str, Enum):
    """
    Currently supported languages and their corresponding BCP 47 language identifier
    """

    AMHARIC = "am"
    GERMAN = "de"
    MALAYALAM = "ml"
    SLOVAK = "sk"
    ARABIC = "ar"
    GREEK = "el"
    MALDIVIAN = "dv"
    SLOVENIAN = "sl"
    ARMENIAN = "hy"
    GUJARATI = "gu"
    MARATHI = "mr"
    SORANI_KURDISH = "ckb"
    BASQUE = "eu"
    HAITIAN_CREOLE = "ht"
    NEPALI = "ne"
    SPANISH = "es"
    BENGALI = "bn"
    HEBREW = "iw"
    NORWEGIAN = "no"
    SWEDISH = "sv"
    BOSNIAN = "bs"
    HINDI = "hi"
    ORIYA = "or"
    TAGALOG = "tl"
    BULGARIAN = "bg"
    LATINIZED_HINDI = "hi-Latn"
    PANJABI = "pa"
    TAMIL = "ta"
    BURMESE = "my"
    HUNGARIAN = "hu"
    PASHTO = "ps"
    TELUGU = "te"
    CROATIAN = "hr"
    ICELANDIC = "is"
    PERSIAN = "fa"
    THAI = "th"
    CATALAN = "ca"
    INDONESIAN = "in"
    POLISH = "pl"
    TIBETAN = "bo"
    CZECH = "cs"
    ITALIAN = "it"
    PORTUGUESE = "pt"
    TRADITIONAL_CHINESE = "zh-TW"
    DANISH = "da"
    JAPANESE = "ja"
    ROMANIAN = "ro"
    TURKISH = "tr"
    DUTCH = "nl"
    KANNADA = "kn"
    RUSSIAN = "ru"
    UKRAINIAN = "uk"
    ENGLISH = "en"
    KHMER = "km"
    SERBIAN = "sr"
    URDU = "ur"
    ESTONIAN = "et"
    KOREAN = "ko"
    SIMPLIFIED_CHINESE = "zh-CN"
    UYGHUR = "ug"
    FINNISH = "fi"
    LAO = "lo"
    SINDHI = "sd"
    VIETNAMESE = "vi"
    FRENCH = "fr"
    LATVIAN = "lv"
    SINHALA = "si"
    WELSH = "cy"
    GEORGIAN = "ka"
    LITHUANIAN = "lt"

    def __str__(self):
        return self.value


class Operator(str, Enum):
    KEYWORD = "keyword"
    EMOJI = "emoji"
    EXACT_PHRASE = "exact phrase match"
    HASHTAG = "#"
    MENTION = "@"  # Matches any Post that mentions the given username
    CASHTAG = "$"  # Matches any Post that contains the specified ‘cashtag’
    FROM = "from:"
    TO = "to:"
    URL = "url:"
    RETWEETS_OF = "retweets_of:"
    IN_REPLY_TO_TWEET_ID = "in_reply_to_tweet_id:"
    RETWEETS_OF_TWEET_ID = "retweets_of_tweet_id:"
    QUOTES_OF_TWEET_ID = "quotes_of_tweet_id:"
    CONTEXT = "context:"
    ENTITY = "entity:"
    CONVERSATION_ID = "conversation_id:"
    LIST = "list:"
    PLACE = "place:"
    PLACE_COUNTRY = "place_country:"
    POINT_RADIUS = "point_radius:"
    BOUNDING_BOX = "bounding_box:"
    IS_RETWEET = "is:retweet"
    IS_REPLY = "is:reply"
    IS_QUOTE = "is:quote"
    IS_VERIFIED = "is:verified"
    IS_NULLCAST = "-is:nullcast"
    HAS_HASHTAGS = "has:hashtags"
    HAS_CASHTAGS = "has:cashtags"
    HAS_LINKS = "has:links"
    HAS_MENTIONS = "has:mentions"
    HAS_MEDIA = "has:media"
    HAS_IMAGES = "has:images"
    HAS_VIDEO_LINK = "has:video_link"
    HAS_GEO = "has:geo"
    LANG = "lang:"  # You can only pass a single BCP 47 language identifier per LANG operator

    def __str__(self):
        return self.value


class Expression(BaseModel):
    """Base class for all expressions."""

    type: str  # Discriminator field

    def __str__(self) -> str:
        """Converts the expression into a string for the Twitter API."""
        return ""


class Term(Expression):
    type: Literal["term"] = "term"
    value: str
    """The keyword or term to match in the search query.

    Example:
        value = "cat"
        Matches posts containing the term 'cat'.
    """

    def __str__(self) -> str:
        return self.value


class Phrase(Expression):
    type: Literal["phrase"] = "phrase"
    value: str
    """The exact phrase to match, including spaces and special characters.

    Example:
        value = "happy birthday"
        Matches posts containing the exact phrase 'happy birthday'.
    """

    def __str__(self) -> str:
        return f'"{self.value}"'


class OperatorExpression(Expression):
    type: Literal["operator"] = "operator"
    operator: Operator
    """The operator to apply, such as 'from:', 'has:', 'lang:', etc.

    Example:
        operator = Operator.FROM
    """
    operand: Optional[Union[str, Language]] = None
    """The operand for the operator. Can be a string or Language enum.

    Example:
        operand = "XDevelopers"
        When combined with operator 'from:', matches posts from '@XDevelopers'.
    """

    def __str__(self) -> str:
        if self.operand:
            if self.operator in {Operator.EXACT_PHRASE, Operator.URL, Operator.ENTITY}:
                operand_str = f'"{self.operand}"'
            elif self.operator == Operator.PLACE and " " in self.operand:
                operand_str = f'"{self.operand}"'
            else:
                operand_str = self.operand
        else:
            operand_str = ""

        if self.operator == Operator.EMOJI:
            operator_str = ""
        else:
            operator_str = self.operator.value

        return f"{operator_str}{operand_str}"


class BooleanOperator(str, Enum):
    AND = "AND"
    OR = "OR"


class NegatedExpression(Expression):
    type: Literal["negated"] = "negated"
    expression: ExpressionType
    """The expression to negate.

    Example:
        expression = Term(value="retweet")
        Matches posts that do NOT contain the term 'retweet'.
    """

    def __str__(self) -> str:
        return f"-{str(self.expression)}"


class BooleanExpression(Expression):
    type: Literal["boolean"] = "boolean"
    operator: BooleanOperator
    """The boolean operator to combine expressions.

    Example:
        operator = BooleanOperator.AND
        Combines expressions using logical 'AND'.
    """
    expressions: List[ExpressionType]
    """The list of expressions to combine.

    Example:
        expressions = [
            Term(value="cat"),
            OperatorExpression(operator=Operator.HAS_IMAGES)
        ]
        Represents the query 'cat has:images'.
    """

    def __str__(self) -> str:
        if self.operator == BooleanOperator.OR:
            op = f" {self.operator.value} "
        else:
            op = " "  # Twitter query language uses a space to represent AND
        expressions_str = op.join([str(expr) for expr in self.expressions])
        return expressions_str


class GroupedExpression(Expression):
    type: Literal["grouped"] = "grouped"
    expression: ExpressionType
    """The grouped expression.

    Example:
        expression = BooleanExpression(
            operator=BooleanOperator.OR,
            expressions=[Term(value="cat"), Term(value="dog")]
        )
        Represents the query '(cat OR dog)'.
    """

    def __str__(self) -> str:
        return f"({str(self.expression)})"


class SearchQuery(BaseModel):
    expression: ExpressionType
    """The root expression of the search query.

    Example:
        expression = BooleanExpression(
            operator=BooleanOperator.AND,
            expressions=[
                GroupedExpression(
                    expression=BooleanExpression(
                        operator=BooleanOperator.OR,
                        expressions=[Term(value="cat"), Term(value="dog")]
                    )
                ),
                OperatorExpression(operator=Operator.HAS_IMAGES)
            ]
        )
        Represents the query '(cat OR dog) has:images'.
    """

    def __str__(self) -> str:
        """Converts the search query into a string as the Twitter API expects.

        Example:
            str(search_query)  # Returns the query string
        """
        return str(self.expression)


ExpressionType = Annotated[
    Union[
        Term,
        Phrase,
        OperatorExpression,
        NegatedExpression,
        BooleanExpression,
        GroupedExpression,
    ],
    Field(discriminator="type"),
]

# # Resolve forward references for serialization
# NegatedExpression.model_rebuild()
# BooleanExpression.model_rebuild()
# GroupedExpression.model_rebuild()
# SearchQuery.model_rebuild()


search_query = SearchQuery(
    expression=BooleanExpression(
        operator=BooleanOperator.AND,
        expressions=[
            GroupedExpression(
                expression=BooleanExpression(
                    operator=BooleanOperator.OR,
                    expressions=[Term(value="cat"), Term(value="dog")],
                )
            ),
            OperatorExpression(operator=Operator.HAS_IMAGES, operand=""),
            OperatorExpression(operator=Operator.PLACE, operand="new york city"),
            NegatedExpression(
                expression=OperatorExpression(operator=Operator.IS_RETWEET, operand="")
            ),
        ],
    )
)

# print(str(search_query))

search_query = SearchQuery(
    expression=BooleanExpression(
        operator=BooleanOperator.AND,
        expressions=[
            Term(value="langchain"),
            GroupedExpression(
                expression=BooleanExpression(
                    operator=BooleanOperator.OR,
                    expressions=[Term(value="worst"), Term(value="sucks")],
                )
            ),
            Term(value="#langchainIsBooBoo"),
            OperatorExpression(operator=Operator.FROM, operand="ericgustin"),
            OperatorExpression(
                operator=Operator.LANG, operand=Language.ENGLISH
            ),  # Added language requirement
            OperatorExpression(
                operator=Operator.EMOJI, operand="😎"
            ),  # Added emoji requirement
            OperatorExpression(
                operator=Operator.MENTION, operand="elonmusk"
            ),  # Added mention requirement
            NegatedExpression(
                expression=OperatorExpression(operator=Operator.IS_RETWEET, operand="")
            ),
            NegatedExpression(
                expression=Phrase(
                    value="I'm not a developer"
                )  # Added negated phrase requirement
            ),
        ],
    )
)

# print(str(search_query))


"""

(cat OR dog) has:images place:"new york city" -is:retweet
langchain (worst OR sucks) #langchainIsBooBoo from:ericgustin lang:en 😎 @elonmusk -is:retweet -"I'm not a developer"


"""

# json_schema = json.dumps(SearchQuery.model_json_schema(), indent=4)
# print(json_schema)


"""
{
    "$defs": {
        "BooleanExpression": {
            "properties": {
                "type": {
                    "const": "boolean",
                    "default": "boolean",
                    "enum": [
                        "boolean"
                    ],
                    "title": "Type",
                    "type": "string"
                },
                "operator": {
                    "$ref": "#/$defs/BooleanOperator"
                },
                "expressions": {
                    "items": {
                        "discriminator": {
                            "mapping": {
                                "boolean": "#/$defs/BooleanExpression",
                                "grouped": "#/$defs/GroupedExpression",
                                "negated": "#/$defs/NegatedExpression",
                                "operator": "#/$defs/OperatorExpression",
                                "phrase": "#/$defs/Phrase",
                                "term": "#/$defs/Term"
                            },
                            "propertyName": "type"
                        },
                        "oneOf": [
                            {
                                "$ref": "#/$defs/Term"
                            },
                            {
                                "$ref": "#/$defs/Phrase"
                            },
                            {
                                "$ref": "#/$defs/OperatorExpression"
                            },
                            {
                                "$ref": "#/$defs/NegatedExpression"
                            },
                            {
                                "$ref": "#/$defs/BooleanExpression"
                            },
                            {
                                "$ref": "#/$defs/GroupedExpression"
                            }
                        ]
                    },
                    "title": "Expressions",
                    "type": "array"
                }
            },
            "required": [
                "operator",
                "expressions"
            ],
            "title": "BooleanExpression",
            "type": "object"
        },
        "BooleanOperator": {
            "enum": [
                "AND",
                "OR"
            ],
            "title": "BooleanOperator",
            "type": "string"
        },
        "GroupedExpression": {
            "properties": {
                "type": {
                    "const": "grouped",
                    "default": "grouped",
                    "enum": [
                        "grouped"
                    ],
                    "title": "Type",
                    "type": "string"
                },
                "expression": {
                    "discriminator": {
                        "mapping": {
                            "boolean": "#/$defs/BooleanExpression",
                            "grouped": "#/$defs/GroupedExpression",
                            "negated": "#/$defs/NegatedExpression",
                            "operator": "#/$defs/OperatorExpression",
                            "phrase": "#/$defs/Phrase",
                            "term": "#/$defs/Term"
                        },
                        "propertyName": "type"
                    },
                    "oneOf": [
                        {
                            "$ref": "#/$defs/Term"
                        },
                        {
                            "$ref": "#/$defs/Phrase"
                        },
                        {
                            "$ref": "#/$defs/OperatorExpression"
                        },
                        {
                            "$ref": "#/$defs/NegatedExpression"
                        },
                        {
                            "$ref": "#/$defs/BooleanExpression"
                        },
                        {
                            "$ref": "#/$defs/GroupedExpression"
                        }
                    ],
                    "title": "Expression"
                }
            },
            "required": [
                "expression"
            ],
            "title": "GroupedExpression",
            "type": "object"
        },
        "Language": {
            "description": "Currently supported languages and their corresponding BCP 47 language identifier",
            "enum": [
                "am",
                "de",
                "ml",
                "sk",
                "ar",
                "el",
                "dv",
                "sl",
                "hy",
                "gu",
                "mr",
                "ckb",
                "eu",
                "ht",
                "ne",
                "es",
                "bn",
                "iw",
                "no",
                "sv",
                "bs",
                "hi",
                "or",
                "tl",
                "bg",
                "hi-Latn",
                "pa",
                "ta",
                "my",
                "hu",
                "ps",
                "te",
                "hr",
                "is",
                "fa",
                "th",
                "ca",
                "in",
                "pl",
                "bo",
                "cs",
                "it",
                "pt",
                "zh-TW",
                "da",
                "ja",
                "ro",
                "tr",
                "nl",
                "kn",
                "ru",
                "uk",
                "en",
                "km",
                "sr",
                "ur",
                "et",
                "ko",
                "zh-CN",
                "ug",
                "fi",
                "lo",
                "sd",
                "vi",
                "fr",
                "lv",
                "si",
                "cy",
                "ka",
                "lt"
            ],
            "title": "Language",
            "type": "string"
        },
        "NegatedExpression": {
            "properties": {
                "type": {
                    "const": "negated",
                    "default": "negated",
                    "enum": [
                        "negated"
                    ],
                    "title": "Type",
                    "type": "string"
                },
                "expression": {
                    "discriminator": {
                        "mapping": {
                            "boolean": "#/$defs/BooleanExpression",
                            "grouped": "#/$defs/GroupedExpression",
                            "negated": "#/$defs/NegatedExpression",
                            "operator": "#/$defs/OperatorExpression",
                            "phrase": "#/$defs/Phrase",
                            "term": "#/$defs/Term"
                        },
                        "propertyName": "type"
                    },
                    "oneOf": [
                        {
                            "$ref": "#/$defs/Term"
                        },
                        {
                            "$ref": "#/$defs/Phrase"
                        },
                        {
                            "$ref": "#/$defs/OperatorExpression"
                        },
                        {
                            "$ref": "#/$defs/NegatedExpression"
                        },
                        {
                            "$ref": "#/$defs/BooleanExpression"
                        },
                        {
                            "$ref": "#/$defs/GroupedExpression"
                        }
                    ],
                    "title": "Expression"
                }
            },
            "required": [
                "expression"
            ],
            "title": "NegatedExpression",
            "type": "object"
        },
        "Operator": {
            "enum": [
                "keyword",
                "emoji",
                "exact phrase match",
                "#",
                "@",
                "$",
                "from:",
                "to:",
                "url:",
                "retweets_of:",
                "in_reply_to_tweet_id:",
                "retweets_of_tweet_id:",
                "quotes_of_tweet_id:",
                "context:",
                "entity:",
                "conversation_id:",
                "list:",
                "place:",
                "place_country:",
                "point_radius:",
                "bounding_box:",
                "is:retweet",
                "is:reply",
                "is:quote",
                "is:verified",
                "-is:nullcast",
                "has:hashtags",
                "has:cashtags",
                "has:links",
                "has:mentions",
                "has:media",
                "has:images",
                "has:video_link",
                "has:geo",
                "lang:"
            ],
            "title": "Operator",
            "type": "string"
        },
        "OperatorExpression": {
            "properties": {
                "type": {
                    "const": "operator",
                    "default": "operator",
                    "enum": [
                        "operator"
                    ],
                    "title": "Type",
                    "type": "string"
                },
                "operator": {
                    "$ref": "#/$defs/Operator"
                },
                "operand": {
                    "anyOf": [
                        {
                            "type": "string"
                        },
                        {
                            "$ref": "#/$defs/Language"
                        },
                        {
                            "type": "null"
                        }
                    ],
                    "default": null,
                    "title": "Operand"
                }
            },
            "required": [
                "operator"
            ],
            "title": "OperatorExpression",
            "type": "object"
        },
        "Phrase": {
            "properties": {
                "type": {
                    "const": "phrase",
                    "default": "phrase",
                    "enum": [
                        "phrase"
                    ],
                    "title": "Type",
                    "type": "string"
                },
                "value": {
                    "title": "Value",
                    "type": "string"
                }
            },
            "required": [
                "value"
            ],
            "title": "Phrase",
            "type": "object"
        },
        "Term": {
            "properties": {
                "type": {
                    "const": "term",
                    "default": "term",
                    "enum": [
                        "term"
                    ],
                    "title": "Type",
                    "type": "string"
                },
                "value": {
                    "title": "Value",
                    "type": "string"
                }
            },
            "required": [
                "value"
            ],
            "title": "Term",
            "type": "object"
        }
    },
    "properties": {
        "expression": {
            "discriminator": {
                "mapping": {
                    "boolean": "#/$defs/BooleanExpression",
                    "grouped": "#/$defs/GroupedExpression",
                    "negated": "#/$defs/NegatedExpression",
                    "operator": "#/$defs/OperatorExpression",
                    "phrase": "#/$defs/Phrase",
                    "term": "#/$defs/Term"
                },
                "propertyName": "type"
            },
            "oneOf": [
                {
                    "$ref": "#/$defs/Term"
                },
                {
                    "$ref": "#/$defs/Phrase"
                },
                {
                    "$ref": "#/$defs/OperatorExpression"
                },
                {
                    "$ref": "#/$defs/NegatedExpression"
                },
                {
                    "$ref": "#/$defs/BooleanExpression"
                },
                {
                    "$ref": "#/$defs/GroupedExpression"
                }
            ],
            "title": "Expression"
        }
    },
    "required": [
        "expression"
    ],
    "title": "SearchQuery",
    "type": "object"
}
"""


# @tool(requires_auth=X(scopes=["tweet.read", "users.read"]))
# def search_recent_tweets_by_query(
#     context: ToolContext,
#     query: Annotated[
#         SearchQuery,
#         "The search query to match tweets. Queries are made up of operators that are used to match on a variety of Post attributes",
#     ],
#     max_results: Annotated[int, "The maximum number of results to return"] = 10,
# ) -> Annotated[str, "JSON string of the search results"]:
#     """
#     Search for recent tweets on X (Twitter) by query. A query is made up of operators that are used to match on a variety of Post attributes.
#     """

#     headers = {
#         "Authorization": f"Bearer {context.authorization.token}",
#         "Content-Type": "application/json",
#     }
#     params = {
#         "query": str(query),  # max 512 character query for non enterprise X accounts
#         "max_results": max_results,
#     }

#     response = requests.get(
#         "https://api.x.com/2/tweets/search/recent?expansions=author_id&user.fields=id,name,username",
#         headers=headers,
#         params=params,
#     )

#     if response.status_code != 200:
#         raise ToolExecutionError(
#             f"Failed to search recent tweets during execution of '{search_recent_tweets_by_query.__name__}' tool. Request returned an error: {response.status_code} {response.text}"
#         )

#     # TODO: Write utility function to parse tweets
#     tweets_data = json.loads(response.text)
#     for tweet in tweets_data["data"]:
#         tweet["tweet_url"] = get_tweet_url(tweet["id"])

#     return json.dumps(tweets_data)
