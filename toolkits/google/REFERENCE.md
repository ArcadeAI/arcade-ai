# Google Toolkit


|             |                |
|-------------|----------------|
| Name        | google |
| Package     | arcade_google |
| Repository  | None   |
| Version     | 0.1.2      |
| Description | Arcade tools for the entire google suite  |
| Author      | dev@arcade-ai.com      |


| Tool Name   | Description                                                             |
|-------------|-------------------------------------------------------------------------|
| GetDocumentById | Get the latest version of the specified Google Docs document. |
| InsertTextAtEndOfDocument | Updates an existing Google Docs document using the batchUpdate API endpoint. |
| CreateBlankDocument | Create a blank Google Docs document with the specified title. |
| CreateDocumentFromText | Create a Google Docs document with the specified title and text content. |
| CreateEvent | Create a new event/meeting/sync/meetup in the specified calendar. |
| ListEvents | List events from the specified calendar within the given datetime range. |
| UpdateEvent | Update an existing event in the specified calendar with the provided details. |
| DeleteEvent | Delete an event from Google Calendar. |
| SendEmail | Send an email using the Gmail API. |
| SendDraftEmail | Send a draft email using the Gmail API. |
| WriteDraftEmail | Compose a new email draft using the Gmail API. |
| UpdateDraftEmail | Update an existing email draft using the Gmail API. |
| DeleteDraftEmail | Delete a draft email using the Gmail API. |
| TrashEmail | Move an email to the trash folder using the Gmail API. |
| ListDraftEmails | Lists draft emails in the user's draft mailbox using the Gmail API. |
| ListEmailsByHeader | Search for emails by header using the Gmail API. |
| ListEmails | Read emails from a Gmail account and extract plain text content. |
| SearchThreads | Search for threads in the user's mailbox |
| ListThreads | List threads in the user's mailbox. |
| GetThread | Get the specified thread by ID. |
| ListDocuments | List documents in the user's Google Drive. Excludes documents that are in the trash. |


### GetDocumentById
Get the latest version of the specified Google Docs document.

#### Parameters
- `document_id`*(string, required)* The ID of the document to retrieve.

---

### InsertTextAtEndOfDocument
Updates an existing Google Docs document using the batchUpdate API endpoint.

#### Parameters
- `document_id`*(string, required)* The ID of the document to update.
- `text_content`*(string, required)* The text content to insert into the document

---

### CreateBlankDocument
Create a blank Google Docs document with the specified title.

#### Parameters
- `title`*(string, required)* The title of the blank document to create

---

### CreateDocumentFromText
Create a Google Docs document with the specified title and text content.

#### Parameters
- `title`*(string, required)* The title of the document to create
- `text_content`*(string, required)* The text content to insert into the document

---

### CreateEvent
Create a new event/meeting/sync/meetup in the specified calendar.

#### Parameters
- `summary`*(string, required)* The title of the event
- `start_datetime`*(string, required)* The datetime when the event starts in ISO 8601 format, e.g., '2024-12-31T15:30:00'.
- `end_datetime`*(string, required)* The datetime when the event ends in ISO 8601 format, e.g., '2024-12-31T17:30:00'.
- `calendar_id`*(string, optional)* The ID of the calendar to create the event in, usually 'primary'.
- `description`*(string, optional)* The description of the event
- `location`*(string, optional)* The location of the event
- `visibility`*(string, optional)* The visibility of the event, Valid values are 'default', 'public', 'private', 'confidential'
- `attendee_emails`*(array, optional)* The list of attendee emails. Must be valid email addresses e.g., username@domain.com.

---

### ListEvents
List events from the specified calendar within the given datetime range.

min_end_datetime serves as the lower bound (exclusive) for an event's end time.
max_start_datetime serves as the upper bound (exclusive) for an event's start time.

For example:
If min_end_datetime is set to 2024-09-15T09:00:00 and max_start_datetime is set to 2024-09-16T17:00:00,
the function will return events that:
1. End after 09:00 on September 15, 2024 (exclusive)
2. Start before 17:00 on September 16, 2024 (exclusive)
This means an event starting at 08:00 on September 15 and ending at 10:00 on September 15 would be included,
but an event starting at 17:00 on September 16 would not be included.

#### Parameters
- `min_end_datetime`*(string, required)* Filter by events that end on or after this datetime in ISO 8601 format, e.g., '2024-09-15T09:00:00'.
- `max_start_datetime`*(string, required)* Filter by events that start before this datetime in ISO 8601 format, e.g., '2024-09-16T17:00:00'.
- `calendar_id`*(string, optional)* The ID of the calendar to list events from
- `max_results`*(integer, optional)* The maximum number of events to return

---

### UpdateEvent
Update an existing event in the specified calendar with the provided details.
Only the provided fields will be updated; others will remain unchanged.

`updated_start_datetime` and `updated_end_datetime` are independent and can be provided separately.

#### Parameters
- `event_id`*(string, required)* The ID of the event to update
- `updated_start_datetime`*(string, optional)* The updated datetime that the event starts in ISO 8601 format, e.g., '2024-12-31T15:30:00'.
- `updated_end_datetime`*(string, optional)* The updated datetime that the event ends in ISO 8601 format, e.g., '2024-12-31T17:30:00'.
- `updated_calendar_id`*(string, optional)* The updated ID of the calendar containing the event.
- `updated_summary`*(string, optional)* The updated title of the event
- `updated_description`*(string, optional)* The updated description of the event
- `updated_location`*(string, optional)* The updated location of the event
- `updated_visibility`*(string, optional)* The visibility of the event, Valid values are 'default', 'public', 'private', 'confidential'
- `attendee_emails_to_add`*(array, optional)* The list of attendee emails to add. Must be valid email addresses e.g., username@domain.com.
- `attendee_emails_to_remove`*(array, optional)* The list of attendee emails to remove. Must be valid email addresses e.g., username@domain.com.
- `send_updates`*(string, optional)* Should attendees be notified of the update? (none, all, external_only), Valid values are 'none', 'all', 'externalOnly'

---

### DeleteEvent
Delete an event from Google Calendar.

#### Parameters
- `event_id`*(string, required)* The ID of the event to delete
- `calendar_id`*(string, optional)* The ID of the calendar containing the event
- `send_updates`*(string, optional)* Specifies which attendees to notify about the deletion, Valid values are 'none', 'all', 'externalOnly'

---

### SendEmail
Send an email using the Gmail API.

#### Parameters
- `subject`*(string, required)* The subject of the email
- `body`*(string, required)* The body of the email
- `recipient`*(string, required)* The recipient of the email
- `cc`*(array, optional)* CC recipients of the email
- `bcc`*(array, optional)* BCC recipients of the email

---

### SendDraftEmail
Send a draft email using the Gmail API.

#### Parameters
- `email_id`*(string, required)* The ID of the draft to send

---

### WriteDraftEmail
Compose a new email draft using the Gmail API.

#### Parameters
- `subject`*(string, required)* The subject of the draft email
- `body`*(string, required)* The body of the draft email
- `recipient`*(string, required)* The recipient of the draft email
- `cc`*(array, optional)* CC recipients of the draft email
- `bcc`*(array, optional)* BCC recipients of the draft email

---

### UpdateDraftEmail
Update an existing email draft using the Gmail API.

#### Parameters
- `draft_email_id`*(string, required)* The ID of the draft email to update.
- `subject`*(string, required)* The subject of the draft email
- `body`*(string, required)* The body of the draft email
- `recipient`*(string, required)* The recipient of the draft email
- `cc`*(array, optional)* CC recipients of the draft email
- `bcc`*(array, optional)* BCC recipients of the draft email

---

### DeleteDraftEmail
Delete a draft email using the Gmail API.

#### Parameters
- `draft_email_id`*(string, required)* The ID of the draft email to delete

---

### TrashEmail
Move an email to the trash folder using the Gmail API.

#### Parameters
- `email_id`*(string, required)* The ID of the email to trash

---

### ListDraftEmails
Lists draft emails in the user's draft mailbox using the Gmail API.

#### Parameters
- `n_drafts`*(integer, optional)* Number of draft emails to read

---

### ListEmailsByHeader
Search for emails by header using the Gmail API.
At least one of the following parameters MUST be provided: sender, recipient, subject, body.

#### Parameters
- `sender`*(string, optional)* The name or email address of the sender of the email
- `recipient`*(string, optional)* The name or email address of the recipient
- `subject`*(string, optional)* Words to find in the subject of the email
- `body`*(string, optional)* Words to find in the body of the email
- `date_range`*(string, optional)* The date range of the email, Valid values are 'today', 'yesterday', 'last_7_days', 'last_30_days', 'this_month', 'last_month', 'this_year'
- `limit`*(integer, optional)* The maximum number of emails to return

---

### ListEmails
Read emails from a Gmail account and extract plain text content.

#### Parameters
- `n_emails`*(integer, optional)* Number of emails to read

---

### SearchThreads
Search for threads in the user's mailbox

#### Parameters
- `page_token`*(string, optional)* Page token to retrieve a specific page of results in the list
- `max_results`*(integer, optional)* The maximum number of threads to return
- `include_spam_trash`*(boolean, optional)* Whether to include spam and trash in the results
- `label_ids`*(array, optional)* The IDs of labels to filter by
- `sender`*(string, optional)* The name or email address of the sender of the email
- `recipient`*(string, optional)* The name or email address of the recipient
- `subject`*(string, optional)* Words to find in the subject of the email
- `body`*(string, optional)* Words to find in the body of the email
- `date_range`*(string, optional)* The date range of the email, Valid values are 'today', 'yesterday', 'last_7_days', 'last_30_days', 'this_month', 'last_month', 'this_year'

---

### ListThreads
List threads in the user's mailbox.

#### Parameters
- `page_token`*(string, optional)* Page token to retrieve a specific page of results in the list
- `max_results`*(integer, optional)* The maximum number of threads to return
- `include_spam_trash`*(boolean, optional)* Whether to include spam and trash in the results

---

### GetThread
Get the specified thread by ID.

#### Parameters
- `thread_id`*(string, required)* The ID of the thread to retrieve
- `metadata_headers`*(array, optional)* When given and format is METADATA, only include headers specified.

---

### ListDocuments
List documents in the user's Google Drive. Excludes documents that are in the trash.

#### Parameters
- `corpora`*(string, optional)* The source of files to list, Valid values are 'user', 'domain', 'drive', 'allDrives'
- `title_keywords`*(array, optional)* Keywords or phrases that must be in the document title
- `order_by`*(string, optional)* Sort order. Defaults to listing the most recently modified documents first, Valid values are 'createdTime', 'createdTime desc', 'folder', 'folder desc', 'modifiedByMeTime', 'modifiedByMeTime desc', 'modifiedTime', 'modifiedTime desc', 'name', 'name desc', 'name_natural', 'name_natural desc', 'quotaBytesUsed', 'quotaBytesUsed desc', 'recency', 'recency desc', 'sharedWithMeTime', 'sharedWithMeTime desc', 'starred', 'starred desc', 'viewedByMeTime', 'viewedByMeTime desc'
- `supports_all_drives`*(boolean, optional)* Whether the requesting application supports both My Drives and shared drives
- `limit`*(integer, optional)* The number of documents to list
