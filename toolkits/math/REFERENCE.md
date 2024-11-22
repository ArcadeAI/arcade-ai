# Math Toolkit


|             |                |
|-------------|----------------|
| Name        | math |
| Package     | arcade_math |
| Repository  | None   |
| Version     | 0.1.2      |
| Description | Math toolkit for Arcade  |
| Author      | dev@arcade-ai.com      |


| Tool Name   | Description                                                             |
|-------------|-------------------------------------------------------------------------|
| Add | Add two numbers together |
| Subtract | Subtract two numbers |
| Multiply | Multiply two numbers together |
| Divide | Divide two numbers |
| Sqrt | Get the square root of a number |
| SumList | Sum all numbers in a list |
| SumRange | Sum all numbers from start through end |
| GenerateRandomInt | Generate a random integer between min_value and max_value (inclusive). |
| GenerateRandomFloat | Generate a random float between min_value and max_value. |


### Add
Add two numbers together

#### Parameters
- `a`*(integer, required)* The first number
- `b`*(integer, required)* The second number

---

### Subtract
Subtract two numbers

#### Parameters
- `a`*(integer, required)* The first number
- `b`*(integer, required)* The second number

---

### Multiply
Multiply two numbers together

#### Parameters
- `a`*(integer, required)* The first number
- `b`*(integer, required)* The second number

---

### Divide
Divide two numbers

#### Parameters
- `a`*(integer, required)* The first number
- `b`*(integer, required)* The second number

---

### Sqrt
Get the square root of a number

#### Parameters
- `a`*(integer, required)* The number to square root

---

### SumList
Sum all numbers in a list

#### Parameters
- `numbers`*(array, required)* The list of numbers

---

### SumRange
Sum all numbers from start through end

#### Parameters
- `start`*(integer, required)* The start of the range to sum
- `end`*(integer, required)* The end of the range to sum

---

### GenerateRandomInt
Generate a random integer between min_value and max_value (inclusive).

#### Parameters
- `min_value`*(integer, required)* The minimum value of the random integer
- `max_value`*(integer, required)* The maximum value of the random integer
- `seed`*(integer, optional)* The seed for the random number generator. If None, the current system time is used.

---

### GenerateRandomFloat
Generate a random float between min_value and max_value.

#### Parameters
- `min_value`*(number, required)* The minimum value of the random float
- `max_value`*(number, required)* The maximum value of the random float
- `seed`*(integer, optional)* The seed for the random number generator. If None, the current system time is used.
