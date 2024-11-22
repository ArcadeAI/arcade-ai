# Zoom Toolkit


|             |                |
|-------------|----------------|
| Name        | zoom |
| Package     | arcade_zoom |
| Repository  | None   |
| Version     | 0.1.2      |
| Description | Arcade tools for Zoom  |
| Author      | dev@arcade-ai.com      |


| Tool Name   | Description                                                             |
|-------------|-------------------------------------------------------------------------|
| ListUpcomingMeetings | List a Zoom user's upcoming meetings within the next 24 hours. |
| GetMeetingInvitation | Retrieve the invitation note for a specific Zoom meeting. |


### ListUpcomingMeetings
List a Zoom user's upcoming meetings within the next 24 hours.

#### Parameters
- `user_id`*(string, optional)* The user's user ID or email address. Defaults to 'me' for the current user.

---

### GetMeetingInvitation
Retrieve the invitation note for a specific Zoom meeting.

#### Parameters
- `meeting_id`*(string, required)* The meeting's numeric ID (as a string).
