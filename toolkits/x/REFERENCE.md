# X Toolkit


|             |                |
|-------------|----------------|
| Name        | x |
| Package     | arcade_x |
| Repository  | None   |
| Version     | 0.1.2      |
| Description | LLM tools for interacting with X (Twitter)  |
| Author      | dev@arcade-ai.com      |


| Tool Name   | Description                                                             |
|-------------|-------------------------------------------------------------------------|
| LookupSingleUserByUsername | Look up a user on X (Twitter) by their username. |
| PostTweet | Post a tweet to X (Twitter). |
| DeleteTweetById | Delete a tweet on X (Twitter). |
| SearchRecentTweetsByUsername | Search for recent tweets (last 7 days) on X (Twitter) by username. Includes replies and reposts. |
| SearchRecentTweetsByKeywords | Search for recent tweets (last 7 days) on X (Twitter) by required keywords and phrases. Includes replies and reposts |


### LookupSingleUserByUsername
Look up a user on X (Twitter) by their username.

#### Parameters
- `username`*(string, required)* The username of the X (Twitter) user to look up

---

### PostTweet
Post a tweet to X (Twitter).

#### Parameters
- `tweet_text`*(string, required)* The text content of the tweet you want to post

---

### DeleteTweetById
Delete a tweet on X (Twitter).

#### Parameters
- `tweet_id`*(string, required)* The ID of the tweet you want to delete

---

### SearchRecentTweetsByUsername
Search for recent tweets (last 7 days) on X (Twitter) by username. Includes replies and reposts.

#### Parameters
- `username`*(string, required)* The username of the X (Twitter) user to look up
- `max_results`*(integer, optional)* The maximum number of results to return. Cannot be less than 10

---

### SearchRecentTweetsByKeywords
Search for recent tweets (last 7 days) on X (Twitter) by required keywords and phrases. Includes replies and reposts
One of the following input parametersMUST be provided: keywords, phrases

#### Parameters
- `keywords`*(array, optional)* List of keywords that must be present in the tweet
- `phrases`*(array, optional)* List of phrases that must be present in the tweet
- `max_results`*(integer, optional)* The maximum number of results to return. Cannot be less than 10
