## Complete Agent Flow Breakdown

### Sales Manager → Email Manager Workflow


__Step 1: Sales Manager Initialization__

- Sales Manager receives user request: "Send a cold sales email addressed to Dear CEO from Alice"
- Has access to 3 sales agent tools and 1 handoff (Email Manager)


__Step 2: Draft Generation Phase__

- Sales Manager calls all 3 sales agent tools in parallel:
  - `sales_agent1` (Professional) → generates professional email draft
  - `sales_agent2` (Engaging) → generates humorous email draft  
  - `sales_agent3` (Busy) → generates concise email draft
- Each agent tool returns a complete email draft


__Step 3: Evaluation and Selection__

- Sales Manager evaluates all 3 drafts
- Selects the single best email based on effectiveness criteria
- Does NOT send the email itself


__Step 4: Handoff to Email Manager__

- Sales Manager hands off the winning email draft to Email Manager agent
- Control transfers completely to Email Manager
- Email Manager receives the raw email body text


__Step 5: Email Manager Processing__

- Email Manager calls `subject_writer` tool → generates compelling subject line
- Email Manager calls `html_converter` tool → converts text body to HTML format
- Email Manager calls `send_html_email` function tool → sends formatted email


__Step 6: Final Execution__

- `send_html_email` function uses Python SMTP to send the email
- Returns success/error status
- Complete automated SDR (Sales Development Representative) workflow finished


#### Key Architecture Points

- __Separation of Concerns__: Sales Manager focuses on content, Email Manager handles delivery
- __Tool Chain__: Agent tools → Function tools → External services
- __Error Handling__: Each step can return status for debugging
- __Traceability__: Full workflow visible in OpenAI traces


### Agentic Design Patterns Used

- __Multi-agent collaboration__
- __Tool-based function calling__
- __Agent handoffs for delegation__
