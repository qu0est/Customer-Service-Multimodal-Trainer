# Customer Service Multimodal Trainer

An AI-powered content moderation system for customer service training. A trainee agent practices handling an angry customer (played by an LLM), and every message or media file they send is automatically moderated for PII, tone, and content quality before reaching the simulated customer.

## Overview

```
Trainee types message / uploads file
        ↓
Moderation agents (text / image / video / audio)
        ↓ blocked?          ↓ safe?
  Show warning        Send to AI customer (Gemini)
                            ↓
                    Customer LLM responds
```

The moderation pipeline catches:
- **PII** — names, phone numbers, email addresses, account numbers
- **Unprofessional or unfriendly tone** — rude, dismissive, or aggressive language
- **Disturbing or low-quality media** — inappropriate images/videos, blurry or pixelated files

All agent interactions are traced through [Arize Phoenix](https://phoenix.arize.com/) for full observability.

---

## Architecture

### Moderation Agents (`multimodal_moderation/agents/`)

| Agent | Input | Flags |
|---|---|---|
| `text_agent.py` | Plain text | `contains_pii`, `is_unfriendly`, `is_unprofessional` |
| `image_agent.py` | Image bytes | `contains_pii`, `is_disturbing`, `is_low_quality` |
| `video_agent.py` | Video bytes | `contains_pii`, `is_disturbing`, `is_low_quality` |
| `audio_agent.py` | Audio bytes | `transcription`, `contains_pii`, `is_unfriendly`, `is_unprofessional` |

Each agent uses Google Gemini via [Pydantic AI](https://ai.pydantic.dev/) and returns a typed Pydantic model.

### LLM Customer (`multimodal_moderation/agents/customer_agent.py`)

A Gemini-powered agent that plays the role of a frustrated customer whose ACME Power Widget Pro stopped working. It starts irritable and gradually calms down if the trainee agent is polite and professional.

### Structured Outputs (`multimodal_moderation/types/moderation_result.py`)

```python
class ModerationResult(BaseModel):
    rationale: str

class TextModerationResult(ModerationResult):
    contains_pii: bool
    is_unfriendly: bool
    is_unprofessional: bool

class ImageModerationResult(ModerationResult):
    contains_pii: bool
    is_disturbing: bool
    is_low_quality: bool

# VideoModerationResult mirrors Image; AudioModerationResult adds transcription
```

### Frontend — Gradio (`multimodal_moderation/gradio_app.py`)

Multimodal chat UI. Supports text, image, video, and audio uploads. Every submission is moderated before reaching the customer LLM. Blocked content shows an inline warning with the moderation rationale.

### Backend — FastAPI (`multimodal_moderation/fastapi_app.py`)

REST API that wraps the moderation agents:

| Endpoint | Method | Description |
|---|---|---|
| `/api/v1/moderate_text` | POST | Moderate a text message |
| `/api/v1/moderate_image_file` | POST | Moderate an uploaded image |
| `/api/v1/moderate_video_file` | POST | Moderate an uploaded video |
| `/api/v1/moderate_audio_file` | POST | Moderate an uploaded audio file |
| `/api/v1/health` | GET | Health check |

All endpoints require `Authorization: Bearer <USER_API_KEY>`.

### Observability — Tracing (`multimodal_moderation/tracing.py`)

OpenTelemetry spans sent to Arize Phoenix:

| Span | Description |
|---|---|
| `conversation` | Root span for entire session — carries `session.id` |
| `chat_turn` | One full user→moderation→AI round trip |
| `moderate_text` / `moderate_image` / etc. | Individual moderation calls |
| `feedback` | Created when content is flagged — carries `feedback.content` and `feedback.flagged` |
| `llm_customer` | The Gemini customer agent call |

---

## Setup

### 1. Clone and install

```bash
git clone <your-repo-url>
cd customer_service_trainer
pip install -e .
```

### 2. Configure credentials

```bash
cp env.example .env
```

Open `.env` and fill in:

```env
GEMINI_API_KEY=your-key-from-aistudio.google.com
USER_API_KEY=any-string-you-choose
DEFAULT_GOOGLE_MODEL=gemini-2.5-flash-lite
```

Get a free Gemini API key at https://aistudio.google.com/apikey.

### 3. Run the app

```bash
multimodal-moderation
```

This starts three services simultaneously:

| Service | URL |
|---|---|
| Chat UI (Gradio) | http://localhost:7860 |
| API docs (FastAPI) | http://localhost:8000/docs |
| Traces (Phoenix) | http://localhost:6006 |

---

## Example Conversation

1. **You:** `Welcome to ACME Customer Service. How can I help you today?`
2. **Customer:** *(complains about broken Power Widget Pro, demands a refund)*
3. **You:** `I absolutely cannot give you a refund.` → ⚠️ **flagged as unprofessional**
4. **You:** `I'm sorry to hear that. I'm authorized to offer you a replacement — would that work?`
5. **Customer:** *(may accept, negotiate, or push back)*
6. Click **End Conversation**, then view the full trace at http://localhost:6006

---

## Running Tests

```bash
# All tests
python -m pytest tests/ -vv

# Individual test files
python -m pytest tests/test_moderation_result.py -vv
python -m pytest tests/test_text_agent.py -vv
python -m pytest tests/test_image_agent.py -vv
python -m pytest tests/test_audio_agent.py -vv
python -m pytest tests/test_gradio_app.py -vv
```

Tests use Pydantic AI's `TestModel` to avoid real API calls except for `test_env_setup.py::test_can_call_gemini_api`, which validates your live API key.

---

## Running Evals

Evals measure how accurately the moderation agents make decisions across a set of labelled test cases.

```bash
# Text moderation evals
python evals/text/test_cases.py

# Image moderation evals
python evals/image/test_cases.py

# Audio moderation evals
python evals/audio/test_cases.py

# Video moderation evals
python evals/video/test_cases.py
```

Each eval run prints a report showing which test cases passed and failed. LLM-based evaluators are non-deterministic — a score below 100% is expected and normal.

Control how many times each case repeats (for statistical confidence) via `EVAL_NUM_REPEATS` in `.env`.

---

## Project Structure

```
customer_service_trainer/
├── multimodal_moderation/
│   ├── agents/
│   │   ├── text_agent.py       # Text moderation agent
│   │   ├── image_agent.py      # Image moderation agent
│   │   ├── video_agent.py      # Video moderation agent
│   │   ├── audio_agent.py      # Audio moderation agent
│   │   └── customer_agent.py   # Simulated angry customer (LLM)
│   ├── types/
│   │   ├── moderation_result.py  # Pydantic output schemas
│   │   └── model_choice.py       # Model configuration dataclass
│   ├── gradio_app.py     # Chat UI frontend
│   ├── fastapi_app.py    # REST API backend
│   ├── tracing.py        # OpenTelemetry + Phoenix setup
│   ├── env.py            # Environment variable loading
│   └── app.py            # Launcher (starts all three services)
├── evals/
│   ├── text/             # Text moderation eval cases
│   ├── image/            # Image moderation eval cases
│   ├── audio/            # Audio moderation eval cases
│   ├── video/            # Video moderation eval cases
│   └── test_data/        # Sample files used by evals
├── tests/                # Pytest unit tests
├── env.example           # Template for .env
└── pyproject.toml
```

---

## Tech Stack

- **[Pydantic AI](https://ai.pydantic.dev/)** — agent framework with structured outputs
- **[Google Gemini](https://aistudio.google.com/)** — LLM for moderation agents and customer simulation
- **[Gradio](https://gradio.app/)** — multimodal chat UI
- **[FastAPI](https://fastapi.tiangolo.com/)** — REST API backend
- **[Arize Phoenix](https://phoenix.arize.com/)** — LLM observability and tracing
- **[OpenTelemetry](https://opentelemetry.io/)** — distributed tracing standard
- **[Pydantic Evals](https://ai.pydantic.dev/evals/)** — evaluation framework
