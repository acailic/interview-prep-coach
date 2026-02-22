# Interview Prep Coach

Transform job postings and resumes into comprehensive interview preparation guides with interactive practice sessions.

## Meet Scout

Scout is your interview prep coach—a supportive, encouraging persona that guides you through the preparation process. Scout brings warmth and practical wisdom from years of coaching experience, making the prep journey feel less like a chore and more like working with a trusted mentor.

**Scout's Philosophy:**
- Preparation beats natural talent
- Every rejection is data, not defeat
- Progress over perfection
- Authenticity over acting

## Features

### Profile Generation
- **Company Research**: Key information about the company, culture, and values
- **Position Analysis**: Extracted requirements, skills, and expectations
- **Tech Stack**: Identified technologies and proficiency expectations
- **Skill Gap Analysis**: Comparison of your skills vs. requirements
- **Interview Process**: Expected interview stages and formats
- **Preparation Guide**: Study plan, practice questions, and talking points

### Interactive Practice
- **Practice Sessions**: Answer questions with AI-powered feedback
- **Multiple Modes**: Focused (category-specific), Timed (countdown pressure), Review (weak areas)
- **Progress Tracking**: Score history, weak area detection, improvement trends

### Interview Day Prep
- **Night Before**: Key talking points, 2-3 practice questions, confidence boost
- **Morning Of**: 5-minute warm-up, easy wins, positive framing
- **1 Hour Before**: 3 key reminders, calm mindset

### Post-Interview Capture
- Log real interview questions for future practice
- Track what went well and what stumped you
- Learn from patterns across interviews

## Installation

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/interview-prep-coach.git
cd interview-prep-coach

# Install with uv (recommended)
uv sync

# Or with pip
pip install -e .
```

## Usage

### Generate Prep Profile

```bash
# From job posting file
interview-prep --job-file job_posting.md --resume my_resume.md

# From job posting URL
interview-prep --job-url https://company.com/careers/job-123 --resume my_resume.md
```

### Practice Sessions

```bash
# Interactive practice
interview-prep practice

# Focus on specific category
interview-prep practice --category behavioral

# Timed mode (2 minutes per question)
interview-prep practice --timed --limit 120

# Review weak areas
interview-prep practice --review
```

### Progress Tracking

```bash
# Show summary
interview-prep progress

# Show weak areas
interview-prep progress --weak-areas
```

### Interview Day Modes

```bash
# Night before prep
interview-prep day-mode --night-before

# Morning warmup
interview-prep day-mode --morning-of
```

### Log Real Interviews

```bash
interview-prep log-interview \
    --company "Acme Corp" \
    --position "Senior Engineer" \
    --questions-asked "Tell me about yourself" \
    --questions-asked "Describe a challenging project" \
    --went-well "System design explanation" \
    --stumped "Behavioral questions about conflict" \
    --outcome pending
```

## Configuration

Set your Anthropic API key:

```bash
export ANTHROPIC_API_KEY=your_api_key_here
```

Or create a `.env` file:

```
ANTHROPIC_API_KEY=your_api_key_here
```

## Project Structure

```
interview_prep_coach/
├── __init__.py
├── cli.py                 # Main CLI commands
├── models.py              # Pydantic data models
├── anthropic_session.py   # Claude API wrapper
├── utils/
│   └── logger.py          # Logging utilities
├── practice/              # Practice session modules
│   ├── engine.py          # Session orchestration
│   ├── question_bank.py   # Question management
│   ├── feedback_analyzer.py  # AI answer analysis
│   └── scorer.py          # Scoring logic
├── tracking/              # Progress tracking
│   ├── progress.py        # Score history
│   └── post_interview.py  # Interview logging
└── modes/                 # Practice modes
    ├── focused.py         # Category-specific
    ├── timed.py           # Countdown pressure
    ├── review.py          # Weak spot drill
    └── interview_day.py   # Day-of prep
```

## Development

### Running Tests

```bash
pytest tests/
```

### Type Checking

```bash
pyright interview_prep_coach/
```

### Linting

```bash
ruff check interview_prep_coach/
```

## License

MIT License - see [LICENSE](LICENSE) for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
