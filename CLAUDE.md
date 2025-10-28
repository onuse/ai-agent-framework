# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**AI Agent Framework v3.0** - A hierarchical multi-agent system with intelligent project planning that can autonomously break down objectives, generate tasks, execute them, and validate results.

The framework supports both **OpenAI-compatible API servers** and **local Ollama** to power all agent reasoning and decision-making. Default model: llama3.1:8b.

## Core Architecture

### LLM Client Abstraction

The framework uses a unified `LLMClient` abstraction layer (`llm_client.py`) that supports:
- **OpenAI-compatible API servers** (default): Any server following OpenAI's API format
- **Local Ollama**: For running models locally
- **Reasoning Model Support**: Automatically extracts final answers from reasoning models that output chain-of-thought

This allows seamless switching between providers via `config.py` without code changes.

#### Reasoning Model Support

Some models (like GPT-OSS:120b) output their complete chain of thought before the final answer, marked with special tokens. The LLMClient automatically detects and extracts the final answer portion using the marker: `<|start|>assistant<|channel|>final<|message|>`.

This happens transparently - all agents receive only the clean final answer without needing any code changes.

### Three-Tier Agent Hierarchy

1. **Project Planner** (`project_planner.py`)
   - Assesses objective complexity (1-10 scale)
   - Creates comprehensive project plans with task breakdowns (1-20+ tasks based on complexity)
   - Defines dependencies, execution phases, and success criteria
   - Adapts plans based on progress

2. **Manager Agent** (`manager_agent.py`)
   - Orchestrates project execution according to the plan
   - Generates tasks from the plan in batches (respects dependencies)
   - Evaluates progress and determines when validation is needed
   - Coordinates improvement cycles based on validation feedback

3. **Worker Agent** (`worker_agent.py`)
   - Executes individual tasks
   - Classifies tasks into domains (code/creative/data/ui/research/game)
   - Generates, validates, and executes solutions
   - Saves artifacts to organized project folders

### Supporting Components

- **Task Queue** (`task_queue.py`): SQLite-backed task management with status tracking (pending/in_progress/completed/failed)
- **Task Classifier** (`task_classifier.py`): LLM-powered domain classification with confidence scoring
- **Context Manager** (`context_manager.py`): Provides plan-aware context to workers for integrated solutions
- **Code Validator** (`code_validator.py`, `minimal_validator.py`): Validates and improves generated code
- **Solution Creators** (`robust_solution_creator.py`, `multilanguage_solution_creators.py`): Generate domain-specific solutions
- **Project Folder Manager** (`project_folder_manager.py`): Organizes artifacts by project objective
- **Project Completeness Agent** (`project_completeness_agent.py`): Validates user perspective and satisfaction

### Data Persistence

- **tasks.db**: SQLite database storing tasks and project state
- **artifacts/**: Directory containing generated project folders organized by objective

## Running the Framework

### Prerequisites

The framework now supports both **local Ollama** and **OpenAI-compatible API servers**.

#### Option 1: Using OpenAI-Compatible API Server (Default)

```bash
# Install Python dependencies
pip install openai

# Configure in config.py or via environment variables
# Default configuration uses: http://192.168.1.95:8000/v1
```

#### Option 2: Using Local Ollama

```bash
# Install Python dependencies
pip install ollama

# Ensure Ollama is installed and running
ollama serve

# Download required model
ollama pull llama3.1:8b

# Update config.py to use Ollama:
# LLM_PROVIDER = "ollama"
```

### Basic Usage

```bash
# Run with objective as argument
python main.py "Create a simple calculator"

# Run interactively
python main.py
# Then enter your objective when prompted

# Run specific modes
python main.py
# Choose option:
# 1 - Normal mode (default)
# 2 - Simple test
# 3 - Complexity demo
# 4 - Planning analysis
```

### Testing

```bash
# Test language detection
python test_language_detection.py

# Test LLM classifier
python test_llm_classifier.py

# Debug language integration
python debug_language_integration.py

# Full pipeline test
python full_pipeline_test.py

# Final framework test
python final_framework_test.py
```

## Key Execution Flow

1. **Planning Phase**:
   - Manager creates project and invokes ProjectPlanner
   - Planner assesses complexity and generates comprehensive plan
   - Initial batch of tasks (up to 3) added to queue

2. **Execution Phase**:
   - Worker fetches next pending task from queue
   - Classifies task domain and generates solution
   - Validates and executes solution
   - Saves artifact to organized project folder
   - Notifies Manager of completion
   - Manager marks task complete in plan and generates next batch

3. **Validation Phase**:
   - When plan complete, ProjectCompletenessAgent evaluates from user perspective
   - Checks satisfaction score, entry points, integration, usability
   - If satisfaction < 7/10, generates improvement tasks
   - Repeats up to 3 improvement cycles

4. **Completion**:
   - Final summary with plan status, artifacts, and next steps
   - Organized project structure in artifacts directory

## Important Implementation Details

### Task Dependencies

Tasks have dependency chains managed by the planner. The system only generates tasks whose dependencies are completed:

```python
# In project_planner.py
def get_next_tasks_from_plan(project_plan, max_tasks=3):
    # Returns only tasks with satisfied dependencies
```

### Domain-Specific Execution

Different domains have specialized execution:
- **code/ui/game**: Subprocess execution with 15s timeout
- **creative**: Text validation (min 50 chars)
- **research**: Structure validation (min 100 chars, must have headers)
- **data**: Python execution with unsafe imports removed

GUI applications are detected and handled specially (3s startup test, then terminated).

### Safety Measures

Code execution includes safety checks:
- Removes dangerous imports (pandas, numpy, matplotlib)
- Replaces `input()` calls with hardcoded values
- Blocks `sys.exit()` calls
- 15-second timeout for non-GUI apps
- JavaScript validation only (no execution)

### Context Awareness

Workers receive plan-aware context including:
- Project objective and current task role
- Dependency information
- Existing project artifacts
- Integration guidance for building upon previous work

## Project Structure Conventions

Generated projects are saved to:
```
artifacts/
  <sanitized_objective_name>/
    main.py or index.html (entry point)
    <other_files>.py/js/html/css
```

Entry points should be clear and obvious (main.py, index.html, app.py, etc.).

## Configuration

### LLM Provider Configuration

The framework uses `config.py` for centralized configuration. You can configure via:

1. **config.py file** (recommended):
```python
# LLM Provider: "openai" or "ollama"
LLM_PROVIDER = "openai"

# Model name
LLM_MODEL = "llama3.1:8b"

# OpenAI-compatible API settings
OPENAI_BASE_URL = "http://192.168.1.95:8000/v1"
OPENAI_API_KEY = "not-needed"
```

2. **Environment variables**:
```bash
export LLM_PROVIDER="openai"
export LLM_MODEL="llama3.1:8b"
export OPENAI_BASE_URL="http://192.168.1.95:8000/v1"
export OPENAI_API_KEY="not-needed"
```

3. **Programmatically** (per-agent override):
```python
# Uses configuration from config.py by default
manager = ManagerAgent()
worker = WorkerAgent()

# Or override model name
manager = ManagerAgent(model_name="llama3.2:8b")
```

### Checking Current Configuration

```bash
# Print current LLM configuration
python config.py
```

### Reasoning Model Configuration

For reasoning models that output chain-of-thought:

```python
# Enable/disable automatic extraction (enabled by default)
EXTRACT_FINAL_ANSWER = True

# Customize the marker if your model uses a different one
FINAL_ANSWER_MARKER = "<|start|>assistant<|channel|>final<|message|>"
```

Test the extraction:
```bash
python test_reasoning_extraction.py
```

## Common Development Tasks

### Modifying Task Generation

Edit `project_planner.py`:
- `_create_planning_prompt()`: Adjust planning instructions
- `_assess_objective_complexity()`: Change complexity assessment
- Task count guidelines are in the planning prompt (lines 185-188)

### Changing Task Classification

Edit `task_classifier.py`:
- Add/modify domain definitions in `__init__`
- Adjust classification prompt in `_create_classification_prompt()`
- Update fallback logic in `_fallback_classification()`

### Adjusting Validation Criteria

Edit `project_completeness_agent.py`:
- Modify satisfaction threshold (default: 7/10) in `manager_agent.py:230`
- Change improvement cycles (default: 3) in `main.py:78`

### Adding New Domain Types

1. Add domain to `task_classifier.py` domain_definitions
2. Add execution logic to `worker_agent.py` `_execute_solution()`
3. Update `project_folder_manager.py` file extension mapping

## Troubleshooting

**ModuleNotFoundError: No module named 'openai' or 'ollama'**
- For OpenAI-compatible: `pip install openai`
- For Ollama: `pip install ollama`

**Connection errors to OpenAI-compatible server**
- Verify server is running and accessible
- Check `OPENAI_BASE_URL` in config.py matches your server
- Test connection: `curl http://192.168.1.95:8000/v1/models`
- Verify firewall allows connection to server port

**Ollama connection errors** (if using Ollama provider)
- Ensure Ollama service is running: `ollama serve`
- Check model is downloaded: `ollama list`
- Verify OLLAMA_HOST in config.py if using custom host

**Tasks timing out**
- Increase timeout in `worker_agent.py:467` (default: 15s)
- Check for `input()` calls or infinite loops in generated code

**Low quality outputs**
- Try more capable model (e.g., llama3.2:70b)
- Adjust complexity assessment in project_planner.py
- Increase task granularity by modifying task count guidelines

**Database locked errors**
- Only one framework instance should run at a time
- Delete tasks.db to reset (loses all task history)
