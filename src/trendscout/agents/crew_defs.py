from crewai import Crew, Process, Task
from .trend_analyzer import TrendAnalyzerAgent
from .content_generator import ContentGeneratorAgent
from .scheduler import SchedulerAgent
from ..core.logging import logger

# Note: The actual agent instances (TrendAnalyzerAgent, etc.) are wrappers.
# We need to access the underlying CrewAI agent object they manage.
# Assuming the wrapper classes have an 'agent' attribute that is the CrewAI Agent.
# If not, this part will need adjustment based on how BaseAgent and its children are structured.


def create_trend_to_post_crew():
    """
    Creates and configures the Trend-to-Post CrewAI crew.
    """
    logger.info("Initializing Trend-to-Post Crew agents...")
    try:
        # These agent classes (TrendAnalyzerAgent, etc.) are our wrappers.
        # We need to ensure they correctly initialize and provide the CrewAI 'Agent' object.
        # For now, let's assume they are instantiated here and their .agent property
        # gives the actual CrewAI agent.
        trend_analyzer_wrapper = TrendAnalyzerAgent()
        content_generator_wrapper = ContentGeneratorAgent()
        scheduler_wrapper = SchedulerAgent()

        # Access the underlying CrewAI agent instances
        # This assumes your wrapper classes (TrendAnalyzerAgent, etc.) have an 'agent' attribute
        # which is the actual CrewAI Agent object.
        # If your BaseAgent initializes the CrewAI agent and stores it as self.agent, this should work.
        crew_trend_analyzer = trend_analyzer_wrapper.agent
        crew_content_generator = content_generator_wrapper.agent
        crew_scheduler = scheduler_wrapper.agent

        logger.info("Trend-to-Post Crew agents initialized.")
    except Exception as e:
        logger.error(f"Error initializing agents for Trend-to-Post Crew: {e}")
        raise

    # Define Tasks
    logger.info("Defining tasks for Trend-to-Post Crew...")
    try:
        trend_analysis_task = Task(
            description="Analyze current trends for the topic: {topic}. Focus on identifying 2-3 key actionable insights or sub-themes that are currently popular or emerging.",
            expected_output="A concise summary of 2-3 key trends, popular keywords, and any relevant hashtags or platforms. The output should be directly usable for content creation.",
            agent=crew_trend_analyzer,
        )

        content_generation_task = Task(
            description="Based on the provided trend analysis, generate 1 engaging social media post idea. The post should be creative and tailored to the identified trends.",
            expected_output="A single, well-crafted social media post including text, and suggestions for visuals if applicable. Ensure the post is ready for publishing.",
            agent=crew_content_generator,
            context=[trend_analysis_task],
        )

        scheduling_task = Task(
            description="Based on the generated social media post and the initial trend analysis, determine the optimal posting time and platform to maximize engagement.",
            expected_output="A specific recommendation for the best day and time to post, and the most suitable platform(s). Provide a brief justification.",
            agent=crew_scheduler,
            context=[content_generation_task],
        )
        logger.info("Trend-to-Post Crew tasks defined.")
    except Exception as e:
        logger.error(f"Error defining tasks for Trend-to-Post Crew: {e}")
        raise

    # Create Crew
    logger.info("Creating Trend-to-Post Crew instance...")
    trend_to_post_crew = Crew(
        agents=[crew_trend_analyzer, crew_content_generator, crew_scheduler],
        tasks=[trend_analysis_task, content_generation_task, scheduling_task],
        process=Process.sequential,
        verbose=True,
    )
    logger.info("Trend-to-Post Crew instance created.")
    return (
        trend_to_post_crew,
        trend_analysis_task,
        content_generation_task,
        scheduling_task,
    )


def run_trend_to_post_workflow(topic: str) -> dict:
    """
    Runs the full Trend-to-Post workflow for a given topic.
    Returns a dictionary containing the structured results.
    """
    from datetime import datetime

    logger.info(f"Starting Trend-to-Post workflow for topic: {topic}")
    try:
        (
            crew,
            trend_analysis_task_obj,
            content_generation_task_obj,
            scheduling_task_obj,
        ) = create_trend_to_post_crew()
        raw_result = crew.kickoff(inputs={"topic": topic})

        logger.info(f"Trend-to-Post workflow completed. Raw result: {raw_result}")

        intermediate_steps = []
        tasks_with_names = [
            ("Trend Analysis", trend_analysis_task_obj),
            ("Content Generation", content_generation_task_obj),
            ("Scheduling", scheduling_task_obj),
        ]

        for agent_name, task_obj in tasks_with_names:
            step_output = "Output not available"
            if task_obj and task_obj.output:
                if (
                    hasattr(task_obj.output, "exported_output")
                    and task_obj.output.exported_output
                ):
                    step_output = task_obj.output.exported_output
                elif (
                    hasattr(task_obj.output, "raw_output")
                    and task_obj.output.raw_output
                ):
                    step_output = task_obj.output.raw_output
                elif isinstance(task_obj.output, str):
                    step_output = task_obj.output

            intermediate_steps.append(
                {
                    "agent_name": agent_name,
                    "output": step_output,
                    "timestamp": datetime.utcnow().isoformat(),
                }
            )

        structured_result = {
            "topic": topic,
            "final_output": raw_result,
            "intermediate_steps": intermediate_steps,
        }

        return structured_result

    except Exception as e:
        logger.error(
            f"Error during Trend-to-Post workflow for topic '{topic}': {e}",
            exc_info=True,
        )
        # Return a structured error to be stored in the task result
        return {
            "topic": topic,
            "error": str(e),
            "details": "The Trend-to-Post workflow encountered an error during execution.",
        }


if __name__ == "__main__":
    # Example usage (for testing this module directly)
    sample_topic = "sustainable travel trends for 2025"
    logger.info(f"Running test for Trend-to-Post workflow with topic: '{sample_topic}'")
    result = run_trend_to_post_workflow(sample_topic)
    logger.info(f"Test run result: {result}")
