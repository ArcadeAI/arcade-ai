from crewai import Agent, Crew, Task
from crewai.llm import LLM
from crewai_arcade import ArcadeToolManager
import dotenv
import litellm

dotenv.load_dotenv()

manager = ArcadeToolManager(default_user_id="user@example.com") 
tools = manager.get_tools(tools=["Search.GetStockSummary"])

crew_agent = Agent(
    role="Main Agent",
    backstory="You are a helpful assistant",
    goal="Help the user with their requests",
    tools=tools,
    allow_delegation=False,
    verbose=True,
    llm=LLM(model="gpt-4o"),
)

task = Task(
    description="Get me the stock summary for top 10 stock between 2023 and 2024",
    expected_output="A bulleted list with a one sentence summary of each stock including the stock price, volume, and market cap",
    agent=crew_agent,
    tools=crew_agent.tools,
)

crew = Crew(
    agents=[crew_agent],
    tasks=[task],
    verbose=True,
    memory=True,
)

# litellm._turn_on_debug()

result = crew.kickoff()

print("\n\n\n ------------ Result ------------ \n\n\n")
print(result)
