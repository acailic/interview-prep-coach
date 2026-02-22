#!/usr/bin/env python3
"""Interview Preparation Tool - Main CLI and Orchestrator.

Transforms job postings and resumes into comprehensive interview prep guides.
Also provides practice sessions, progress tracking, and interview day modes.
"""

import asyncio
import sys
from pathlib import Path

import click

from .utils.logger import get_logger

from .models import InterviewOutcome
from .models import PracticeMode
from .models import QuestionCategory
from .modes import InterviewDayMode
from .modes.interview_day import SessionManager
from .practice import FeedbackAnalyzer
from .practice import PracticeEngine
from .practice import QuestionBank
from .practice import Scorer
from .tracking import PostInterviewCapture
from .tracking import ProgressTracker

logger = get_logger(__name__)

STAGE_ORDER = [
    "company_research",
    "position_analysis",
    "tech_stack",
    "skill_gaps",
    "interview_process",
    "prep_guide",
]


def _create_engine(data_dir: Path | None = None) -> PracticeEngine:
    """Create a PracticeEngine with all dependencies."""
    tracker = ProgressTracker(data_dir=data_dir)
    bank = QuestionBank()
    analyzer = FeedbackAnalyzer()
    scorer = Scorer()
    return PracticeEngine(
        question_bank=bank,
        progress_tracker=tracker,
        feedback_analyzer=analyzer,
        scorer=scorer,
    )


def _get_data_dir() -> Path:
    """Get default data directory for practice tracking."""
    return Path("./data/tracking")


@click.group()
def main():
    """Interview Preparation Tool - Generate comprehensive prep guides.

    Transforms job postings and your resume into a personalized interview
    preparation guide with study plans, practice questions, and talking points.

    Commands:
        practice       Start interactive practice session
        progress       Show practice progress and weak areas
        log-interview  Log a real interview experience
        day-mode       Interview day preparation modes
    """
    pass


@main.command()
@click.option("--session", type=str, default=None, help="Resume existing session by ID")
@click.option(
    "--category",
    type=click.Choice(["behavioral", "technical", "system_design", "coding"]),
    default=None,
    help="Focus on specific category",
)
@click.option("--timed", is_flag=True, help="Enable timed mode")
@click.option("--review", is_flag=True, help="Review weak areas")
@click.option("--limit", type=int, default=120, help="Time limit in seconds (for timed mode)")
@click.option("--questions", type=int, default=5, help="Number of questions to practice")
def practice(
    session: str | None,
    category: str | None,
    timed: bool,
    review: bool,
    limit: int,
    questions: int,
):
    """Start interactive practice session.

    Practice interview questions with AI-powered feedback on your answers.

    Examples:
        python -m ai_working.interview_prep practice
        python -m ai_working.interview_prep practice --category behavioral
        python -m ai_working.interview_prep practice --timed --limit 120
        python -m ai_working.interview_prep practice --review
    """
    data_dir = _get_data_dir()
    engine = _create_engine(data_dir)

    mode = PracticeMode.mixed
    if category:
        mode = PracticeMode.focused
    elif timed:
        mode = PracticeMode.timed
    elif review:
        mode = PracticeMode.review

    cat_enum = QuestionCategory(category) if category else None

    async def run_practice():
        try:
            await engine.start_session(
                mode=mode,
                category=cat_enum,
                time_limit=limit if timed else None,
            )

            click.echo(f"\n Practice Session Started ({mode.value} mode)")
            click.echo("=" * 40)

            q_count = 0
            while q_count < questions:
                question = await engine.get_next_question()
                if question is None:
                    click.echo("\n No more questions available.")
                    break

                q_count += 1
                click.echo(f"\n Question {q_count}/{questions}")
                click.echo(f" Category: {question.category.value}")
                click.echo(f"\n{question.question_text}")
                click.echo("\n" + "-" * 40)

                answer = click.prompt(
                    "Your answer (or 'skip' to pass)",
                    type=str,
                    default="",
                    show_default=False,
                )

                if answer.lower() == "skip":
                    click.echo(" Skipping this question...")
                    continue

                if not answer.strip():
                    click.echo(" No answer provided, skipping...")
                    continue

                click.echo("\n Analyzing your answer...")
                result = await engine.submit_answer(question.question_id, answer)

                click.echo(f"\n Score: {result.score:.1f}/10")
                click.echo(f"\n Feedback:\n{result.scout_feedback}")

                if result.weak_areas:
                    click.echo(f"\n Areas to improve: {', '.join(result.weak_areas)}")

                if q_count < questions and not click.confirm(
                    "\n Continue to next question?", default=True
                ):
                    break

            completed = await engine.end_session()
            avg_score = sum(q.score for q in completed.questions) / len(completed.questions) if completed.questions else 0

            click.echo("\n" + "=" * 40)
            click.echo(" Session Complete!")
            click.echo(f" Questions answered: {len(completed.questions)}")
            click.echo(f" Average score: {avg_score:.1f}/10")
            click.echo(f" Session ID: {completed.session_id}")

        except Exception as e:
            click.echo(f"\n Error during practice: {e}", err=True)
            raise

    asyncio.run(run_practice())


@main.command()
@click.option("--weak-areas", is_flag=True, help="Show identified weak areas")
@click.option("--detailed", is_flag=True, help="Show detailed progress breakdown")
def progress(weak_areas: bool, detailed: bool):
    """Show practice progress.

    Display your practice history, scores by category, and improvement trends.

    Examples:
        python -m ai_working.interview_prep progress
        python -m ai_working.interview_prep progress --weak-areas
        python -m ai_working.interview_prep progress --detailed
    """
    data_dir = _get_data_dir()
    tracker = ProgressTracker(data_dir=data_dir)
    summary = tracker.get_summary()

    if weak_areas:
        click.echo("\n Identified Weak Areas")
        click.echo("=" * 30)

        areas = tracker.get_weak_areas(threshold=2)
        if areas:
            for i, area in enumerate(areas, 1):
                click.echo(f"  {i}. {area}")
        else:
            click.echo("  No weak areas identified yet.")
            click.echo("  Practice more to get personalized insights.")
        return

    click.echo("\n Practice Progress Summary")
    click.echo("=" * 30)
    click.echo(f"  Total sessions: {summary.total_sessions}")
    click.echo(f"  Questions practiced: {summary.total_questions_practiced}")
    click.echo(f"  Average score: {summary.avg_score:.1f}/10")
    click.echo(f"  Trend: {summary.improvement_trend}")

    if detailed or summary.category_scores:
        click.echo("\n Scores by Category:")
        category_scores = tracker.get_category_scores()
        for cat, score in sorted(category_scores.items()):
            status = "OK" if score >= 7.0 else "NEEDS WORK"
            click.echo(f"  - {cat}: {score:.1f} [{status}]")

    if summary.weak_areas:
        click.echo("\n Top Weak Areas:")
        for area in summary.weak_areas[:5]:
            click.echo(f"  - {area}")


@main.command("log-interview")
@click.option("--company", type=str, required=True, help="Company name")
@click.option("--position", type=str, required=True, help="Position title")
@click.option("--questions-asked", type=str, multiple=True, help="Questions asked (can specify multiple)")
@click.option("--went-well", type=str, multiple=True, help="What went well (can specify multiple)")
@click.option("--stumped", type=str, multiple=True, help="What stumped you (can specify multiple)")
@click.option("--style-notes", type=str, default=None, help="Notes about interview style")
@click.option(
    "--outcome",
    type=click.Choice(["pending", "offer", "rejected", "withdrawn"]),
    default="pending",
    help="Interview outcome",
)
def log_interview(
    company: str,
    position: str,
    questions_asked: tuple[str, ...],
    went_well: tuple[str, ...],
    stumped: tuple[str, ...],
    style_notes: str | None,
    outcome: str,
):
    """Log a real interview experience.

    Capture what was asked, what went well, and what stumped you.
    Questions get added to your practice bank for future review.

    Examples:
        python -m ai_working.interview_prep log-interview \\
            --company "TechCorp" \\
            --position "Senior Engineer" \\
            --questions-asked "Tell me about yourself" \\
            --questions-asked "Design a cache" \\
            --went-well "Clear communication" \\
            --stumped "Distributed locking"
    """
    data_dir = _get_data_dir()
    bank = QuestionBank()
    capture = PostInterviewCapture(question_bank=bank, data_dir=data_dir)

    log = capture.log_interview(
        company=company,
        position=position,
        questions_asked=list(questions_asked),
        what_went_well=list(went_well),
        what_stumped=list(stumped),
        style_notes=style_notes,
        outcome=InterviewOutcome(outcome),
    )

    click.echo("\n Interview Logged Successfully")
    click.echo("=" * 30)
    click.echo(f"  Company: {log.company}")
    click.echo(f"  Position: {log.position}")
    click.echo(f"  Date: {log.interview_date}")
    click.echo(f"  Questions captured: {len(log.questions_asked)}")
    click.echo(f"  Outcome: {log.outcome.value if log.outcome else 'pending'}")

    if questions_asked:
        click.echo(f"\n  Questions added to practice bank: {len(questions_asked)}")


@main.command("day-mode")
@click.option("--night-before", is_flag=True, help="Night before interview prep")
@click.option("--morning-of", is_flag=True, help="Morning of interview warmup")
@click.option("--one-hour", is_flag=True, help="One hour before final prep")
def day_mode(night_before: bool, morning_of: bool, one_hour: bool):
    """Interview day preparation modes.

    Get targeted preparation content based on when your interview is.

    Examples:
        python -m ai_working.interview_prep day-mode --night-before
        python -m ai_working.interview_prep day-mode --morning-of
        python -m ai_working.interview_prep day-mode --one-hour
    """
    data_dir = _get_data_dir()
    tracker = ProgressTracker(data_dir=data_dir)
    session_manager = SessionManager(tracker)
    mode = InterviewDayMode(session_manager, tracker)

    if not any([night_before, morning_of, one_hour]):
        click.echo("\n Please specify a timing option:")
        click.echo("  --night-before  : Comprehensive review for night before")
        click.echo("  --morning-of    : 5-minute warmup")
        click.echo("  --one-hour      : Final prep checklist")
        return

    async def run_mode():
        if night_before:
            content = await mode.night_before()
            click.echo(content)
        elif morning_of:
            content = await mode.morning_of()
            click.echo(content)
        elif one_hour:
            content = await mode.one_hour_before()
            click.echo(content)

    asyncio.run(run_mode())


@main.command("quick-practice")
@click.option(
    "--category",
    type=click.Choice(["behavioral", "technical", "system_design", "coding"]),
    default="behavioral",
    help="Question category",
)
@click.option("--questions", type=int, default=3, help="Number of questions")
def quick_practice(category: str, questions: int):
    """Quick practice session with minimal setup.

    Fast practice mode for a quick warmup.

    Examples:
        python -m ai_working.interview_prep quick-practice
        python -m ai_working.interview_prep quick-practice --category technical --questions 5
    """
    data_dir = _get_data_dir()
    engine = _create_engine(data_dir)
    cat_enum = QuestionCategory(category)

    async def run():
        click.echo(f"\n Quick Practice: {category}")
        click.echo(f" {questions} questions\n")

        await engine.start_session(mode=PracticeMode.focused, category=cat_enum)

        for i in range(questions):
            question = await engine.get_next_question()
            if not question:
                break

            click.echo(f"\n Q{i+1}: {question.question_text}")
            answer = click.prompt("Answer", type=str, default="")

            if answer.strip():
                result = await engine.submit_answer(question.question_id, answer)
                click.echo(f" Score: {result.score:.1f}/10")

        await engine.end_session()
        click.echo("\n Quick practice complete!")

    asyncio.run(run())


if __name__ == "__main__":
    sys.exit(main())
