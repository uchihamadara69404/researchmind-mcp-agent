import asyncio
import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent

load_dotenv()

SYSTEM_PROMPT = """You are Meridian, an autonomous research agent. 

When given a research topic, you MUST follow these steps in order:
1. Call get_past_research to check if we have covered this before
2. Call web_search at least 3 times with different specific queries to gather comprehensive information
3. Call save_research to store your findings in the database
4. Call generate_report to produce the final formatted report

Be thorough. Each web search should use a different angle on the topic.
Always cite your sources in the final report."""

async def run_agent(topic: str):
    client = MultiServerMCPClient({
        "researchmind": {
            "command": "python3",
            "args": ["src/mcp_server.py"],
            "transport": "stdio",
        }
    })

    tools = await client.get_tools()

    llm = ChatGroq(
        model="llama-3.3-70b-versatile",
        api_key=os.getenv("GROQ_API_KEY"),
        temperature=0.1
    )

    agent = create_react_agent(llm, tools, prompt=SYSTEM_PROMPT)

    print(f"\n Meridian starting research on: {topic}\n")
    print("=" * 50)

    result = await agent.ainvoke({
        "messages": [{"role": "user", "content": f"Research this topic thoroughly: {topic}"}]
    })

    final_message = result["messages"][-1].content
    return final_message

if __name__ == "__main__":
    topic = input("Enter research topic: ")
    result = asyncio.run(run_agent(topic))
    print("\n" + result)
