from dotenv import load_dotenv
from agents import Agent, Runner, trace
import asyncio

# NOTE:
# -----
# Used Claude to generate this code based on 1-exercise-go-program.py (shitty name, I know)

load_dotenv(override=True)

OPENAI_MODEL = "gpt-4o-mini"

# Agent 1: Web Scraper Developer
scraper_developer = Agent(
    name="Web Scraper Developer",
    instructions="""You are a Python web scraping expert. Create robust web scrapers using requests and BeautifulSoup.
    Always include proper error handling, user-agent headers, and respect robots.txt.
    Write clean, well-documented code with appropriate delays between requests.
    Focus on extracting structured data and saving it to CSV or JSON format.""",
    model=OPENAI_MODEL,
)

# Agent 2: Data Analyst
data_analyst = Agent(
    name="Data Analyst",
    instructions="""You are a Python data analysis expert using pandas, matplotlib, and seaborn.
    Analyze scraped data to find patterns, trends, and insights.
    Create meaningful visualizations and statistical summaries.
    Provide clear interpretations of the data and actionable insights.""",
    model=OPENAI_MODEL,
)

# Agent 3: Report Generator
report_generator = Agent(
    name="Report Generator",
    instructions="""You are a technical report writer. Create comprehensive reports from data analysis results.
    Structure reports with executive summary, methodology, findings, and recommendations.
    Include descriptions of visualizations and key statistics.
    Write in clear, professional language suitable for stakeholders.""",
    model=OPENAI_MODEL,
)

# Agent 4: Code Reviewer
code_reviewer = Agent(
    name="Code Reviewer",
    instructions="""You are a senior Python developer focused on code quality and security.
    Review Python code for best practices, security issues, and performance optimizations.
    Check for proper error handling, code structure, and documentation.
    Suggest improvements and identify potential issues before deployment.""",
    model=OPENAI_MODEL,
)


async def main():
    target_website = "quotes.toscrape.com"
    data_focus = "quotes, authors, and tags"

    print("=== Multi-Agent Web Scraping & Analysis Workflow ===\n")

    # Step 1: Develop web scraper
    with trace("scraper development"):
        print("Step 1: Developing web scraper...")
        scraper_result = await Runner.run(
            starting_agent=scraper_developer,
            input=f"""Create a Python web scraper for {target_website} that extracts {data_focus}.
            Save the data to a CSV file called 'scraped_data.csv'.
            Include proper error handling and rate limiting.""",
        )
        print(f"Scraper Developer Response:\n{scraper_result.final_output}\n")

    # Step 2: Review the scraper code
    with trace("code review"):
        print("Step 2: Reviewing scraper code...")
        review_result = await Runner.run(
            starting_agent=code_reviewer,
            input="""Review the web scraper code that was just created. 
            Check for security issues, best practices, and potential improvements.
            Suggest any modifications needed before running the scraper.""",
        )
        print(f"Code Reviewer Response:\n{review_result.final_output}\n")

    # Step 3: Analyze the scraped data
    with trace("data analysis"):
        print("Step 3: Analyzing scraped data...")
        analysis_result = await Runner.run(
            starting_agent=data_analyst,
            input="""Analyze the scraped data from 'scraped_data.csv'.
            Create visualizations showing:
            1. Most common authors
            2. Most popular tags
            3. Quote length distribution
            4. Any other interesting patterns
            Save plots as PNG files and provide statistical insights.""",
        )
        print(f"Data Analyst Response:\n{analysis_result.final_output}\n")

    # Step 4: Generate comprehensive report
    with trace("report generation"):
        print("Step 4: Generating final report...")
        report_result = await Runner.run(
            starting_agent=report_generator,
            input="""Create a comprehensive report based on the web scraping project and data analysis.
            Include:
            - Executive summary of findings
            - Methodology used for scraping and analysis
            - Key insights and statistics
            - Visualizations descriptions
            - Recommendations for further analysis
            Save the report as 'scraping_analysis_report.md'.""",
        )
        print(f"Report Generator Response:\n{report_result.final_output}\n")

    print("=== Web Scraping & Analysis Workflow Complete ===")


if __name__ == "__main__":
    asyncio.run(main())
