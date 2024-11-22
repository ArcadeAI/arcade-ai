# Slack Toolkit


|             |                |
|-------------|----------------|
| Name        | slack |
| Package     | arcade_slack |
| Repository  | None   |
| Version     | 0.1.2      |
| Description | Slack tools for LLMs  |
| Author      | dev@arcade-ai.com      |


| Tool Name   | Description                                                             |
|-------------|-------------------------------------------------------------------------|
| SendDmToUser | Send a direct message to a user in Slack. |
| SendMessageToChannel | Send a message to a channel in Slack. |


### SendDmToUser
Send a direct message to a user in Slack.

#### Parameters
- `user_name`*(string, required)* The Slack username of the person you want to message. Slack usernames are ALWAYS lowercase.
- `message`*(string, required)* The message you want to send

---

### SendMessageToChannel
Send a message to a channel in Slack.

#### Parameters
- `channel_name`*(string, required)* The Slack channel name where you want to send the message. Slack channel names are ALWAYS lowercase.
- `message`*(string, required)* The message you want to send
