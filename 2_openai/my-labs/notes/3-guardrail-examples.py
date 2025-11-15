from agents import Agent,  Runner, trace, function_tool, input_guardrail, output_guardrail, GuardrailFunctionOutput
from pydantic import BaseModel
import asyncio

## Content Saftey Guardrail

class ContentSafetyOutput(BaseModel):
    contains_inappropriate_content: bool
    content_type: str
    severity_level: int  # 1-5 scale

content_safety_agent = Agent(
    name="Content Safety Checker",
    instructions="Analyze the message for inappropriate content including profanity, hate speech, or harmful requests. Rate severity 1-5.",
    output_type=ContentSafetyOutput,
    model="gpt-4o-mini"
)

@input_guardrail
async def content_safety_guardrail(ctx, agent, message):
    result = await Runner.run(content_safety_agent, message, context=ctx.context)
    output = result.final_output
    
    # Block if inappropriate content found with severity > 2
    should_block = output.contains_inappropriate_content and output.severity_level > 2
    
    return GuardrailFunctionOutput(
        output_info={
            "safety_check": output,
            "blocked_reason": f"Inappropriate {output.content_type}" if should_block else None
        },
        tripwire_triggered=should_block
    )

###############################################################################################################

## Business Hours Guardrail

from datetime import datetime, time

class BusinessHoursOutput(BaseModel):
    is_urgent_request: bool
    requires_immediate_action: bool
    estimated_response_time: str

business_hours_agent = Agent(
    name="Business Hours Analyzer",
    instructions="Determine if this request is urgent and requires immediate action outside business hours.",
    output_type=BusinessHoursOutput,
    model="gpt-4o-mini"
)

@input_guardrail
async def business_hours_guardrail(ctx, agent, message):
    current_time = datetime.now().time()
    business_start = time(9, 0)  # 9 AM
    business_end = time(17, 0)   # 5 PM
    
    is_business_hours = business_start <= current_time <= business_end
    
    if is_business_hours:
        return GuardrailFunctionOutput(
            output_info={"status": "business_hours"},
            tripwire_triggered=False
        )
    
    # Check if urgent during off-hours
    result = await Runner.run(business_hours_agent, message, context=ctx.context)
    output = result.final_output
    
    # Block non-urgent requests outside business hours
    should_block = not output.is_urgent_request
    
    return GuardrailFunctionOutput(
        output_info={
            "urgency_check": output,
            "current_time": current_time.strftime("%H:%M"),
            "message": "Non-urgent requests are processed during business hours (9 AM - 5 PM)" if should_block else None
        },
        tripwire_triggered=should_block
    )

###############################################################################################################

## Email Content Validation Guardrail

class EmailValidationOutput(BaseModel):
    contains_sensitive_info: bool
    has_appropriate_tone: bool
    includes_required_disclaimers: bool
    sensitive_items: list[str]

email_validation_agent = Agent(
    name="Email Validator",
    instructions="Check if the email contains sensitive information, has appropriate professional tone, and includes required legal disclaimers.",
    output_type=EmailValidationOutput,
    model="gpt-4o-mini"
)

@output_guardrail
async def email_output_guardrail(ctx, agent, output):
    # Validate the generated email content
    result = await Runner.run(email_validation_agent, f"Email content: {output}", context=ctx.context)
    validation = result.final_output
    
    # Block if contains sensitive info or inappropriate tone
    should_block = (validation.contains_sensitive_info or 
                   not validation.has_appropriate_tone or 
                   not validation.includes_required_disclaimers)
    
    if should_block:
        return GuardrailFunctionOutput(
            output_info={
                "validation_result": validation,
                "blocked_reason": "Email failed validation checks"
            },
            tripwire_triggered=True
        )
    
    return GuardrailFunctionOutput(
        output_info={"validation_result": validation},
        tripwire_triggered=False
    )

###############################################################################################

## Financial Data Protection Guardrail

class FinancialDataOutput(BaseModel):
    contains_financial_data: bool
    data_types_found: list[str]
    risk_level: str  # "low", "medium", "high"

financial_guard_agent = Agent(
    name="Financial Data Guardian",
    instructions="Scan for financial data like account numbers, SSNs, credit card info, salary details, etc.",
    output_type=FinancialDataOutput,
    model="gpt-4o-mini"
)

@output_guardrail
async def financial_data_guardrail(ctx, agent, output):
    result = await Runner.run(financial_guard_agent, f"Content to check: {output}", context=ctx.context)
    financial_check = result.final_output
    
    # Block high-risk financial data exposure
    should_block = (financial_check.contains_financial_data and 
                   financial_check.risk_level == "high")
    
    return GuardrailFunctionOutput(
        output_info={
            "financial_scan": financial_check,
            "action": "Content blocked due to financial data exposure" if should_block else "Content approved"
        },
        tripwire_triggered=should_block
    )

#############################################################################################

####  Guardrails as Agents  ####

## Multi-Step Validation Agent

class ComprehensiveValidation(BaseModel):
    safety_score: int  # 1-10
    compliance_score: int  # 1-10
    quality_score: int  # 1-10
    overall_approved: bool
    recommendations: list[str]

@function_tool
def check_content_safety(content: str) -> dict:
    """Check content for safety issues"""
    # Simulate safety check
    return {"safe": True, "issues": []}

@function_tool
def check_compliance(content: str) -> dict:
    """Check content for regulatory compliance"""
    # Simulate compliance check
    return {"compliant": True, "violations": []}

@function_tool
def check_quality(content: str) -> dict:
    """Check content quality and professionalism"""
    # Simulate quality check
    return {"quality_score": 8, "suggestions": []}

comprehensive_guardrail_agent = Agent(
    name="Comprehensive Content Validator",
    instructions="""You are a comprehensive content validator. Use the available tools to:
    1. Check content safety
    2. Verify regulatory compliance  
    3. Assess content quality
    
    Provide scores (1-10) for each area and overall approval recommendation.""",
    tools=[check_content_safety, check_compliance, check_quality],
    output_type=ComprehensiveValidation,
    model="gpt-4o-mini"
)

@output_guardrail
async def comprehensive_output_guardrail(ctx, agent, output):
    result = await Runner.run(
        comprehensive_guardrail_agent, 
        f"Please validate this content: {output}", 
        context=ctx.context
    )
    
    validation = result.final_output
    
    # Block if any score is below 6 or overall not approved
    should_block = (validation.safety_score < 6 or 
                   validation.compliance_score < 6 or 
                   validation.quality_score < 6 or 
                   not validation.overall_approved)
    
    return GuardrailFunctionOutput(
        output_info={
            "comprehensive_validation": validation,
            "decision": "blocked" if should_block else "approved"
        },
        tripwire_triggered=should_block
    )

#############################################################################################

## Adaptive Learning Agent


class AdaptiveGuardrailOutput(BaseModel):
    risk_assessment: str
    confidence_level: float
    learned_patterns: list[str]
    recommendation: str

adaptive_guardrail_agent = Agent(
    name="Adaptive Learning Guardrail",
    instructions="""You learn from previous interactions to improve guardrail decisions. 
    Consider context, user history, and emerging patterns to make intelligent blocking decisions.
    Adapt your sensitivity based on the user's role and previous behavior.
    The recommended action will be 'block' or 'allow'.""",
    output_type=AdaptiveGuardrailOutput,
    model="gpt-4o"  # Using more powerful model for complex reasoning
)

@input_guardrail
async def adaptive_learning_guardrail(ctx, agent, message):
    # Include context about user history, time of day, etc.
    context_info = f"""
    Message: {message}
    User context: {ctx.context if hasattr(ctx, 'context') else 'No context'}
    Previous interactions: {getattr(ctx, 'history', 'No history')}
    """
    
    result = await Runner.run(adaptive_guardrail_agent, context_info, context=ctx.context)
    assessment = result.final_output
    
    # Use AI-driven decision making
    should_block = assessment.recommendation.lower() == "block"
    
    return GuardrailFunctionOutput(
        output_info={
            "adaptive_assessment": assessment,
            "learning_applied": True
        },
        tripwire_triggered=should_block
    )

#############################################################################################

####  Using Multiple Guardrails  ####


# Create an agent with multiple guardrails
protected_sales_agent = Agent(
    name="Highly Protected Sales Agent",
    instructions="Generate professional sales emails with multiple safety checks.",
    model="gpt-4o-mini",
    input_guardrails=[
        content_safety_guardrail,
        business_hours_guardrail,
        adaptive_learning_guardrail
    ],
    output_guardrails=[
        email_output_guardrail,
        financial_data_guardrail,
        comprehensive_output_guardrail
    ]
)


async def main():
    # Example usage
    message = "Create a sales email for our new compliance software"

    with trace("Multi-Guardrail Protected Agent"):
        result = await Runner.run(protected_sales_agent, message)
        print(f"Final output:\n{result.final_output}")

if __name__ == "__main__":
    asyncio.run(main())
