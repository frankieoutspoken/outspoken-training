# Project Guidelines

## Structure
```
src/           — Application code (agents, tools, frontend)
data/          — Data files (CSVs, markdown docs, knowledge bases)
tests/         — Test files
.env.example   — Required environment variables template
```

## Conventions
- Python 3.11+
- Use `src/` for all application code — don't put code in the project root
- Keep agents, tools, and skills in separate subdirectories under `src/`
- Data files live in `data/` — never hardcode data in source code
- Environment variables go in `.env` (never committed) — see `.env.example` for required keys
- Use type hints on all function signatures
- Keep functions small and single-purpose

## Dependencies
- Agent framework: Claude Agent SDK (`claude-agent-sdk`)
- API clients: `anthropic`, `openai`
- Frontend: `streamlit`
- Document generation: `python-docx`
- Data: `pandas` for CSV operations

## Running
```bash
# Install dependencies
pip install -r requirements.txt

# Copy and fill in env vars
cp .env.example .env

# Run the app
streamlit run src/app.py
```
