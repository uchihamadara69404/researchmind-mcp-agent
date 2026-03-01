import asyncio
import json
import sqlite3
import os
from datetime import datetime
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types
from tavily import TavilyClient
from dotenv import load_dotenv

load_dotenv()

app = Server("researchmind")
tavily = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))

def init_db():
    conn = sqlite3.connect("research.db")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS research (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            topic TEXT,
            content TEXT,
            sources TEXT,
            timestamp TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()

@app.list_tools()
async def list_tools():
    return [
        types.Tool(
            name="web_search",
            description="Search the web for recent information on a topic. Use multiple times with different queries for thorough research.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"},
                    "max_results": {"type": "integer", "default": 5}
                },
                "required": ["query"]
            }
        ),
        types.Tool(
            name="save_research",
            description="Save research findings to the local database for memory across sessions.",
            inputSchema={
                "type": "object",
                "properties": {
                    "topic": {"type": "string"},
                    "content": {"type": "string"},
                    "sources": {"type": "array", "items": {"type": "string"}}
                },
                "required": ["topic", "content"]
            }
        ),
        types.Tool(
            name="get_past_research",
            description="Check if we have already researched this topic before.",
            inputSchema={
                "type": "object",
                "properties": {
                    "topic": {"type": "string"}
                },
                "required": ["topic"]
            }
        ),
        types.Tool(
            name="generate_report",
            description="Format the final research into a clean markdown report.",
            inputSchema={
                "type": "object",
                "properties": {
                    "topic": {"type": "string"},
                    "findings": {"type": "string"},
                    "sources": {"type": "array", "items": {"type": "string"}}
                },
                "required": ["topic", "findings"]
            }
        )
    ]

@app.call_tool()
async def call_tool(name: str, arguments: dict):
    if name == "web_search":
        try:
            results = tavily.search(
                arguments["query"],
                max_results=arguments.get("max_results", 5)
            )
            simplified = [
                {"title": r.get("title"), "url": r.get("url"), "content": r.get("content")}
                for r in results.get("results", [])
            ]
            return [types.TextContent(type="text", text=json.dumps(simplified, indent=2))]
        except Exception as e:
            return [types.TextContent(type="text", text=f"Search error: {str(e)}")]

    elif name == "save_research":
        try:
            conn = sqlite3.connect("research.db")
            conn.execute(
                "INSERT INTO research (topic, content, sources, timestamp) VALUES (?, ?, ?, ?)",
                (
                    arguments["topic"],
                    arguments["content"],
                    json.dumps(arguments.get("sources", [])),
                    datetime.now().isoformat()
                )
            )
            conn.commit()
            conn.close()
            return [types.TextContent(type="text", text="Research saved to database successfully.")]
        except Exception as e:
            return [types.TextContent(type="text", text=f"DB error: {str(e)}")]

    elif name == "get_past_research":
        try:
            conn = sqlite3.connect("research.db")
            rows = conn.execute(
                "SELECT topic, content, sources, timestamp FROM research WHERE topic LIKE ? ORDER BY timestamp DESC LIMIT 3",
                (f"%{arguments['topic']}%",)
            ).fetchall()
            conn.close()
            if not rows:
                return [types.TextContent(type="text", text="No past research found on this topic.")]
            result = [{"topic": r[0], "content": r[1], "sources": r[2], "timestamp": r[3]} for r in rows]
            return [types.TextContent(type="text", text=json.dumps(result, indent=2))]
        except Exception as e:
            return [types.TextContent(type="text", text=f"DB error: {str(e)}")]

    elif name == "generate_report":
        topic = arguments["topic"]
        findings = arguments["findings"]
        sources = arguments.get("sources", [])
        timestamp = datetime.now().strftime("%B %d, %Y")

        sources_md = "\n".join([f"- {s}" for s in sources]) if sources else "- Sources embedded in findings"

        report = f"""# 📊 Meridian Research Report
## {topic}
*Generated by ResearchMind Agent — {timestamp}*

---

## Key Findings

{findings}

---

## Sources

{sources_md}

---
*Powered by Meridian MCP Agent | Built with LangGraph + Groq + Tavily*
"""
        return [types.TextContent(type="text", text=report)]

if __name__ == "__main__":
    asyncio.run(stdio_server(app))
