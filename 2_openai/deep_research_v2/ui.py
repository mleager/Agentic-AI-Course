import gradio as gr
from agents import Runner
from manager import ManagerAgent
from clarifier import ClarifierAgent
from updater import TopicUpdaterAgent
from dotenv import load_dotenv
from textwrap import dedent

load_dotenv(override=True)


manager_agent = ManagerAgent()
clarifier_agent = ClarifierAgent()
updater_agent = TopicUpdaterAgent()


class ResearchState:
    def __init__(self):
        self.original_topic = ""
        self.questions = None
        self.updated_topic = ""

state = ResearchState()


async def submit_topic(topic: str) -> tuple[dict, dict, str]:
    """Run the Clarifier Agent to generate clarifying questions for the topic.
    Gets the topic from the first Textbox input.
    Returns 2 Event Listeners to affect gr.Group visibility & the questions to be displayed."""

    state.original_topic = topic
    
    # Generate clarifying questions using the Clarifier Agent
    result = await Runner.run(clarifier_agent, topic)
    questions = result.final_output
    state.questions = questions
    
    return gr.update(visible=False), gr.update(visible=True), dedent(f"""
        Please answer these clarifying questions:

        1. Scope: {questions.scope}
        2. Focus: {questions.focus}
        3. Audience: {questions.audience}""")


async def submit_answers(scope_answer: str, focus_answer: str, audience_answer: str) -> tuple[str, dict]:
    """Run the Updater Agent to update the topic based on the answers provided.
    Then calls the Manager Agent to run off the updated topic.
    Returns the final report & Event Listener to hide clarifying questions Group."""

    if not state.original_topic:
        return "Error: No original topic or questions found", gr.update(visible=True)
    
    if not state.questions:
        return "No questions found, please use the original topic", gr.update(visible=True)
    
    # Format the answers
    answers = dedent(f"""Scope: {scope_answer}
        Focus: {focus_answer}
        Audience: {audience_answer}""")

    # Update the topic using the Updater Agent
    result = await Runner.run(updater_agent, f"Topic: {state.original_topic}\nClarifying Questions: {answers}")
    updated_topic = result.final_output
    state.updated_topic = updated_topic

    #####################################################################

    # # Start the research process (streaming)
    # report = ""
    # async for chunk in manager_agent.run(updated_topic):
    #     report = chunk

    # Start the research process (standard)
    report = await manager_agent.run(updated_topic)

    # INFO: Or should ManagerAgent be a Handoff from TopicUpdaterAgent?
    # -----------------------------------------------------------------

    return report, gr.update(visible=False)


with gr.Blocks(theme=gr.Theme(primary_hue="sky")) as ui:
    gr.Markdown("# Deep Research")

    with gr.Group() as topic_group:
        query_textbox = gr.Textbox(
            label="What topic would you like to research?",
            placeholder="Enter your research topic here..."
        )
        topic_submit = gr.Button("Submit Topic", variant="primary")

    with gr.Group(visible=False) as questions_group:
        questions_display = gr.Markdown()
        scope_answer = gr.Textbox(
            label="Answer for Scope",
            placeholder="Enter your answer about the scope..."
        )
        focus_answer = gr.Textbox(
            label="Answer for Focus",
            placeholder="Enter your answer about the focus..."
        )
        audience_answer = gr.Textbox(
            label="Answer for Audience",
            placeholder="Enter your answer about the target audience..."
        )
        answers_submit = gr.Button("Submit Answers & Start Research", variant="primary")

    report = gr.Markdown(label="Research Report")

    # Set up the interaction flow
    topic_submit.click(
        fn=submit_topic,
        inputs=[query_textbox],
        outputs=[
            topic_group,
            questions_group,
            questions_display
        ]
    )

    answers_submit.click(
        fn=submit_answers,
        inputs=[scope_answer, focus_answer, audience_answer],
        outputs=[report, questions_group]
    )


if __name__ == "__main__":
    ui.launch(inbrowser=True)
