# Week 2 Day 2: Agentic AI Framework Notes

Building a simple Agent system for generating cold sales outreach emails using:

- Agent workflows
- Function tools
- Agent collaboration via Tools and Handoffs


## Key Components


### 1. Agent Workflow

Three specialized sales agents with different personalities:

- __Professional Agent__: Serious, professional cold emails
- __Engaging Agent__: Humorous, witty emails likely to get responses
- __Busy Agent__: Concise, to-the-point emails


### 2. Function Tools

- __`@function_tool` decorator__: Automatically converts functions into tools with JSON boilerplate
- __Email sending functions__: `send_gmail()` and `send_html_email()`
- __Agent-as-tool conversion__: `agent.as_tool()` method


### 3. Agent Collaboration Patterns

#### Tools vs Handoffs

- __Tools__: Control passes back to calling agent
- __Handoffs__: Control passes across to another agent


#### Sales Manager Architecture

- Uses multiple sales agent tools to generate drafts
- Evaluates and selects best email
- Either sends directly or hands off to Email Manager


### 4. Advanced Features

- __Subject Writer Agent__: Generates compelling email subjects
- __HTML Converter Agent__: Converts text emails to HTML format
- __Email Manager Agent__: Handles formatting and sending via handoff


## Commercial Applications

- Sales automation
- End-to-end business process automation
- Customer service workflows
- Any process requiring conversational AI with tools


## Technical Notes

- __Tracing__: Available at https://platform.openai.com/traces
- __SSL Issues__: May require `certifi` upgrade and certificate configuration
- __Alternative__: Resend Email implementation available in community
