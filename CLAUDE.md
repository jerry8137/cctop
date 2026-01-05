# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

cctop is an HTOP-like TUI monitor for Claude Code agents built with Python 3.12 and the Textual framework. It monitors Claude Code's log files in `~/.claude/projects/` to provide real-time visibility into agent activity, token usage, and API costs.

## Development Commands

### Environment Setup
```bash
uv sync              # Install dependencies
uv sync --extra dev  # Install with dev dependencies
```

### Running the Application
```bash
uv run python main.py                    # Run with defaults
uv run python main.py --refresh 0.5      # Custom refresh rate
uv run python main.py --log-dir /path    # Custom log directory
uv run python main.py --no-watch         # Disable file watching
```

### Testing
```bash
uv run pytest tests/ -v                  # Run all tests
uv run pytest tests/test_parsers.py -v   # Run specific test file
uv run pytest tests/test_parsers.py::test_parse_log_file -v  # Run single test
```

## Architecture

### Data Flow Pipeline

The application follows a three-stage data flow:

1. **Log Parsing** (`parsers/`) → 2. **Data Aggregation** → 3. **UI Rendering** (`widgets/`)

```
~/.claude/projects/agent-*.jsonl
    ↓ (monitored by LogFileWatcher)
JSONLParser.parse_log_file()
    ↓ (extracts token usage from message.usage fields)
DataAggregator.scan_all_logs()
    ↓ (builds Agent objects with status detection)
CCTopApp.refresh_data()
    ↓ (updates all UI widgets)
Textual widgets render in TUI
```

### Core Components Interaction

**DataAggregator** is the central orchestrator:
- Scans `~/.claude/projects/` for `agent-*.jsonl` files
- Uses `JSONLParser` to extract log entries and token usage
- Builds `Agent` objects with calculated costs (via `utils/pricing.py`)
- Detects agent status through three-layer check:
  1. Last message type and stop_reason
  2. Todo files in `~/.claude/todos/`
  3. Inactivity duration

**Status Detection Logic**:
- `ACTIVE`: Activity within last 30 seconds
- `IDLE`: Activity within last hour
- `WAITING_FOR_USER`: Assistant message with `end_turn` + recent activity
- `STOPPED`: No activity for over 1 hour

**Real-time Updates**:
- `LogFileWatcher` uses `watchdog` library to monitor file changes
- Callbacks are debounced (100ms) to prevent excessive refreshes
- Updates are thread-safe via `call_from_thread()`

### Pricing System

Token costs are calculated in `utils/pricing.py` using hardcoded rates for all Claude models (Opus 4.5, Sonnet 4.5, Haiku 3.5, etc.). Each agent's total cost is computed from four token types:
- Input tokens
- Output tokens
- Cache creation tokens
- Cache read tokens

Model names are normalized (e.g., "claude-sonnet-4-5-20250929" → "claude-sonnet-4-5") before lookup.

### Widget Architecture

The Textual app (`app.py`) composes multiple widgets:

- **MetricsPanel**: Top summary bar (agents, tokens, cost)
- **AgentTable**: DataTable with sortable columns
- **NotificationBar**: Alerts for waiting agents (conditionally visible)
- **CostPanel** & **SystemPanel**: Bottom horizontal panels
- **AgentDetail**: Modal screen for detailed agent view

All widgets receive updates via their `update_*()` methods called from `CCTopApp.refresh_data()`.

### File Watching vs Polling

Two update modes controlled by `_disable_watcher` flag:
- **File watching** (default): Event-driven updates via `watchdog`
- **Polling mode** (`--no-watch`): Periodic refresh at configured interval

## Key Implementation Details

### Log File Format

Claude Code logs are JSONL (JSON Lines) with entries like:
```json
{
  "timestamp": "2026-01-04T10:00:00Z",
  "agentId": "abc123",
  "sessionId": "xyz789",
  "type": "assistant",
  "message": {
    "model": "claude-sonnet-4-5-20250929",
    "usage": {
      "input_tokens": 100,
      "output_tokens": 50,
      "cache_creation_input_tokens": 10,
      "cache_read_input_tokens": 5
    },
    "stop_reason": "end_turn"
  }
}
```

The parser (`parsers/jsonl_parser.py`) extracts:
- Agent metadata (ID, session, timestamps)
- Token usage per API call
- Message types for status detection

### Sorting and Filtering

App maintains state for current sort and filter:
- `sort_by`: "last_activity" | "cost" | "tokens" | "agent_id"
- `filter_status`: None | AgentStatus enum value

Implemented in `DataAggregator.get_all_agents_sorted()` with post-filtering in `refresh_data()`.

### CSS Styling

Custom Textual CSS in `app.css` defines:
- Panel heights and docking
- DataTable header/cursor colors
- Widget borders and padding

Widgets reference IDs like `#metrics`, `#agents`, `#panels`.

## Testing Strategy

Tests focus on core logic:
- **Parsers**: JSONL parsing, token extraction, agent info aggregation
- **Pricing**: Model normalization, cost calculation
- **Fixtures**: `tests/fixtures/sample_logs.jsonl` for parser tests

UI widgets are not unit tested (rely on manual TUI testing).

## Common Patterns

### Adding a New Widget
1. Create widget class inheriting from `Static` or `DataTable`
2. Implement `update_*()` method to receive data
3. Add to `CCTopApp.compose()` with unique ID
4. Call update method from `refresh_data()`
5. Add CSS rules in `app.css` if needed

### Adding a New Keyboard Shortcut
1. Add `Binding` to `CCTopApp.BINDINGS`
2. Implement `action_*()` method
3. Update help text in `action_show_help()`
4. Update README.md

### Updating Pricing
Modify `PRICING` dictionary in `utils/pricing.py`. Use `Decimal` for precision. Add model variant to `normalize_model_name()` if needed.
