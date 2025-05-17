# A conversation where a user asks for the structure of a space,
# and an LLM calls a tool to get the structure.
get_space_hierarchy_1 = [
    {"role": "system", "content": "Today is 2025-05-16, Friday."},
    {"role": "user", "content": "get structure of 98308"},
    {
        "role": "assistant",
        "content": "",
        "tool_calls": [
            {
                "id": "call_exyK4LmJEHSDn1Xw5oVfS9Xx",
                "type": "function",
                "function": {
                    "name": "Confluence_GetSpaceHierarchy",
                    "arguments": '{"space_identifier":"98308"}',
                },
            }
        ],
    },
    {
        "role": "tool",
        "content": '{"98418":{"children":[{"children":[],"id":"4653060","parent_id":"98418","parent_type":"TODO","title":"Mydb","type":"database","url":"https://ericconfluence.atlassian.net/wiki/spaces/testspace/database/4653060"},{"children":[{"children":[],"id":"4685837","parent_id":"4653064","parent_type":"TODO","title":"10-03-98","type":"page","url":"https://ericconfluence.atlassian.net/wiki/spaces/testspace/pages/4685837/10-03-98"}],"id":"4653064","parent_id":"98418","parent_type":"TODO","title":"DailyNotes","type":"folder","url":null},{"children":[{"children":[],"id":"5242883","parent_id":"5275650","parent_type":"TODO","title":"To be or not tobe","type":"page","url":"https://ericconfluence.atlassian.net/wiki/spaces/testspace/pages/5242883/To+be+or+not+to+be"},{"children":[],"id":"5275653","parent_id":"5275650","parent_type":"TODO","title":"Two roadsdiverged","type":"page","url":"https://ericconfluence.atlassian.net/wiki/spaces/testspace/pages/edit-v2/5275653"},{"children":[],"id":"5242903","parent_id":"5275650","parent_type":"TODO","title":"Eternity","type":"page","url":"https://ericconfluence.atlassian.net/wiki/spaces/testspace/pages/5242903/Eternity"},{"children":[],"id":"5242913","parent_id":"5275650","parent_type":"TODO","title":"BlackHole","type":"page","url":"https://ericconfluence.atlassian.net/wiki/spaces/testspace/pages/5242913/Black+Hole"}],"id":"5275650","parent_id":"98418","parent_type":"TODO","title":"Poetry","type":"folder","url":null},{"children":[],"id":"5275676","parent_id":"98418","parent_type":"TODO","title":"Drawings","type":"whiteboard","url":"https://ericconfluence.atlassian.net/wiki/spaces/testspace/whiteboard/5275676"}],"id":"98418","parent_id":null,"parent_type":null,"title":"testspace Home","type":"page","url":"https://ericconfluence.atlassian.net/wiki/spaces/testspace/overview"}}',  # noqa: E501
        "tool_call_id": "call_exyK4LmJEHSDn1Xw5oVfS9Xx",
        "name": "Confluence_GetSpaceHierarchy",
    },
    {
        "role": "assistant",
        "content": 'Here is the structure for the space with the identifier 98308:\n\n- **testspace Home** [Page](https://ericconfluence.atlassian.net/wiki/spaces/testspace/overview)\n  - **My db** [Database](https://ericconfluence.atlassian.net/wiki/spaces/testspace/database/4653060)\n  - **Daily Notes** (Folder)\n    - [10-03-98](https://ericconfluence.atlassian.net/wiki/spaces/testspace/pages/4685837/10-03-98) (Page)\n  - **Poetry** (Folder)\n    - [To be or not to be](https://ericconfluence.atlassian.net/wiki/spaces/testspace/pages/5242883/To+be+or+not+to+be) (Page)\n    - [Two roads diverged](https://ericconfluence.atlassian.net/wiki/spaces/testspace/pages/edit-v2/5275653) (Page)\n    - [Eternity](https://ericconfluence.atlassian.net/wiki/spaces/testspace/pages/5242903/Eternity) (Page)\n    - [Black Hole](https://ericconfluence.atlassian.net/wiki/spaces/testspace/pages/5242913/Black+Hole) (Page)\n  - **Drawings** [Whiteboard](https://ericconfluence.atlassian.net/wiki/spaces/testspace/whiteboard/5275676)\n\nThis structure includes various elements such as pages, a database, folders, and a whiteboard within the "testspace" space.',  # noqa: E501
    },
]


create_page_1 = [
    {
        "role": "user",
        "content": "make a new page within the testspace space under the 4653064 folder. WEithin is, make alist of all the TODOs for the day which are 1. Write a blog 2. Walk the dog",  # noqa: E501
    },
    {
        "role": "assistant",
        "content": "",
        "tool_calls": [
            {
                "id": "call_xuvOuXpLAmX57RO1zj5hqQ1r",
                "type": "function",
                "function": {
                    "name": "Confluence_CreatePage",
                    "arguments": '{"space_identifier":"testspace","title":"TODOs forToday","content":"<h1>TODOs for Today</h1><ol><li>Write a blog</li><li>Walk thedog</li></ol>","parent_id":"4653064"}',  # noqa: E501
                },
            }
        ],
    },
    {
        "role": "tool",
        "content": '{"page":{"authorId":"712020:93b309a8-e9af-4615-b289-07bf23e6f13f","body":{"storage":{"representation":"storage","value":"\\u003ch1\\u003eTODOs for Today\\u003c/h1\\u003e\\u003col\\u003e\\u003cli\\u003eWrite a blog\\u003c/li\\u003e\\u003cli\\u003eWalk the dog\\u003c/li\\u003e\\u003c/ol\\u003e"}},"createdAt":"2025-05-16T22:29:59.969Z","id":"5439489","lastOwnerId":null,"ownerId":"712020:93b309a8-e9af-4615-b289-07bf23e6f13f","parentId":"4653064","parentType":"folder","position":1675,"spaceId":"98308","status":"current","title":"TODOs for Today","url":"https://ericconfluence.atlassian.net/wiki/spaces/testspace/pages/5439489/TODOs+for+Today","version":{"authorId":"712020:93b309a8-e9af-4615-b289-07bf23e6f13f","createdAt":"2025-05-16T22:29:59.969Z","message":"","minorEdit":false,"ncsStepVersion":"1","number":1}}}',  # noqa: E501
        "tool_call_id": "call_xuvOuXpLAmX57RO1zj5hqQ1r",
        "name": "Confluence_CreatePage",
    },
    {
        "role": "assistant",
        "content": 'I have created a new page titled "TODOs for Today" in the "testspace" space, under the folder with ID 4653064. The list of your tasks for the day is included:\n\n1. Write a blog\n2. Walk the dog\n\nYou can view the page [here](https://ericconfluence.atlassian.net/wiki/spaces/testspace/pages/5439489/TODOs+for+Today).',  # noqa: E501
    },
]
