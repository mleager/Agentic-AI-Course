from ui import ui
from dotenv import load_dotenv

load_dotenv(override=True)


if __name__ == "__main__":
    ui.launch(inbrowser=True)


# import gradio as gr
# from dotenv import load_dotenv
# from manager import ManagerAgent

# load_dotenv(override=True)

# manager_agent = ManagerAgent()


# async def run(query: str):
#     async for chunk in manager_agent.run(query):
#         yield chunk


# with gr.Blocks(theme=gr.Theme(primary_hue="sky")) as ui:
#     gr.Markdown("# Deep Research")
#     query_textbox = gr.Textbox(label="What topic would you like to research?")
#     run_button = gr.Button("Run", variant="primary")
#     report = gr.Markdown(label="Report")

#     run_button.click(fn=run, inputs=query_textbox, outputs=report)
#     query_textbox.submit(fn=run, inputs=query_textbox, outputs=report)

#     # Asks Clarifying Questions - But No Way to Have Questions be Used as Input,
#     # because the "Run button" calls the "run" function, not "ask_clarifying_questions".

#     # Create a new interface to answer the questions

# if __name__ == "__main__":
#     ui.launch(inbrowser=True)
