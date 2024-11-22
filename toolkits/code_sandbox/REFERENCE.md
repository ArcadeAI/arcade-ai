# Code_sandbox Toolkit


|             |                |
|-------------|----------------|
| Name        | code_sandbox |
| Package     | arcade_code_sandbox |
| Repository  | None   |
| Version     | 0.1.0      |
| Description | LLM tools for running code in a sandbox  |
| Author      | dev@arcade-ai.com      |


| Tool Name   | Description                                                             |
|-------------|-------------------------------------------------------------------------|
| RunCode | Run code in a sandbox and return the output. |
| CreateStaticMatplotlibChart | Run the provided Python code to generate a static matplotlib chart. The resulting chart is returned as a base64 encoded image. |


### RunCode
Run code in a sandbox and return the output.

#### Parameters
- `code`*(string, required)* The code to run
- `language`*(string, optional)* The language of the code, Valid values are 'python', 'js', 'r', 'java', 'bash'

---

### CreateStaticMatplotlibChart
Run the provided Python code to generate a static matplotlib chart. The resulting chart is returned as a base64 encoded image.

#### Parameters
- `code`*(string, required)* The Python code to run
