import gradio as gr
import asyncio
import os
import sqlite3
from dotenv import load_dotenv
from agent import run_agent

load_dotenv()

def get_history():
    try:
        conn = sqlite3.connect("research.db")
        rows = conn.execute(
            "SELECT topic, timestamp FROM research ORDER BY timestamp DESC LIMIT 10"
        ).fetchall()
        conn.close()
        if not rows:
            return "No research history yet."
        return "\n".join([f"• **{r[0]}** — {r[1][:10]}" for r in rows])
    except:
        return "No history found."

def research(topic):
    if not topic.strip():
        return "Please enter a research topic."
    try:
        result = asyncio.run(run_agent(topic))
        return result
    except Exception as e:
        return f"Error: {str(e)}"

with gr.Blocks(theme=gr.themes.Soft(), title="Meridian Research Agent") as demo:
    gr.Markdown("""
    # 🔬 Meridian
    ### Autonomous Research Agent — powered by MCP + Groq + Tavily
    """)

    with gr.Row():
        with gr.Column(scale=3):
            topic_input = gr.Textbox(
                label="Research Topic",
                placeholder="e.g. Impact of AI agents on software jobs in 2026",
                lines=2
            )
            run_btn = gr.Button("🚀 Run Research", variant="primary", size="lg")
            output = gr.Markdown(label="Report", value="Your report will appear here...")

        with gr.Column(scale=1):
            gr.Markdown("### 📚 Research History")
            history = gr.Markdown(value=get_history())
            refresh_btn = gr.Button("🔄 Refresh History", size="sm")

    run_btn.click(fn=research, inputs=topic_input, outputs=output)
    refresh_btn.click(fn=get_history, outputs=history)

demo.launch(server_name="0.0.0.0", server_port=7860)
