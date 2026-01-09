# CCTOP

HTOP-like TUI monitor for Claude Code agents. Monitor resource usage, account costs, and active agents in real-time.

## Features

- **Real-time Monitoring**: Watch Claude Code agents as they run
- **Token Usage Tracking**: See input/output tokens and cache usage per agent
- **Dynamic Pricing**: Automatically fetches latest pricing from LiteLLM with local caching
- **Cost Calculation**: Accurate pricing for all Claude models (Opus 4.5, Sonnet 4.5, Haiku 3.5, etc.)
- **Agent Status**: Track active, idle, waiting, and stopped agents
- **File Watching**: Automatically updates when log files change
- **Live Updates**: Instant refresh when agents start, stop, or make API calls
- **Sorting & Filtering**: Sort by cost, tokens, or activity; filter by agent status
- **Agent Details**: View detailed information for any agent
- **Offline Mode**: Works completely offline with bundled pricing
- **Customizable**: CLI arguments for refresh rate, log directory, and more

## Installation

```bash
# Install with uv
uv sync

# Run directly
uv run python main.py

# Or use the cctop command
cctop
```

## Usage

Launch cctop:
```bash
uv run python main.py

# Or with options
cctop --refresh 0.5                # Faster refresh (500ms)
cctop --log-dir /custom/path       # Custom log directory
cctop --no-watch                   # Disable file watching
cctop --offline                    # Offline mode (use cached/bundled pricing)
cctop --help                       # Show all options
```

### Pricing

CCTOP uses a three-tier pricing system:

1. **Fetch from LiteLLM** (default): Automatically fetches latest pricing on first run
2. **Local Cache**: Caches pricing for 24 hours in `~/.cache/cctop/pricing.json`
3. **Bundled Fallback**: Uses bundled pricing when offline or if fetch fails

The subtitle shows the pricing source:
- `Pricing: updated` - Fetched from LiteLLM recently
- `Pricing: cached` - Using cached pricing
- `Pricing: bundled` - Using bundled fallback (offline mode)

Use `--offline` to skip network operations and use only cached/bundled pricing.

### Keyboard Shortcuts

- `q` or `Ctrl+C` - Quit
- `r` - Refresh data manually
- `s` - Cycle sort order (Activity → Cost → Tokens → ID)
- `f` - Cycle filter (All → Active → Idle → Waiting → Stopped)
- `c` - Toggle cost/system panels visibility
- `Enter` - Show detailed view for selected agent
- `?` - Show help screen
- Arrow keys - Navigate agent list

### Display

The TUI shows:

**Top Bar**: Summary metrics
- Total agents
- Active/Idle/Waiting counts
- Total tokens consumed
- Total cost

**Main Table**: Agent list with columns
- Agent ID (short)
- Name/slug
- Status (color-coded: green=active, yellow=waiting, blue=idle)
- Model (S-4.5, H-3.5, etc.)
- Input tokens
- Output tokens
- Cost per agent
- Last activity time

**Bottom Panels**: Detailed information
- Cost Breakdown: Input, output, cache creation/read costs
- System Resources: CPU, memory usage, uptime

**Detail View**: Press Enter on any agent to see:
- Full agent ID and session ID
- Complete project path
- Detailed token breakdown
- Creation time and activity history

## How It Works

cctop monitors Claude Code log files in `~/.claude/projects/`:
- Parses `agent-*.jsonl` files for conversation history
- Extracts token usage from `message.usage` fields
- Calculates costs based on official Claude API pricing
- Watches for file changes using `watchdog` for instant updates
- Updates UI in real-time as agents run

## Development

Developed with uv and Python 3.12.

### Project Structure

```
src/cctop/
├── models/          # Data models (Agent, Metrics, TokenUsage)
├── parsers/         # JSONL log parsers and aggregator
├── watchers/        # File watching for real-time updates
├── widgets/         # Textual TUI widgets
├── utils/           # Pricing and formatting utilities
└── app.py           # Main Textual application
```

### Running Tests

```bash
uv run pytest tests/ -v
```

## Command-Line Options

```
usage: cctop [-h] [--log-dir LOG_DIR] [--refresh SECONDS] [--no-watch] [--version]

options:
  --log-dir LOG_DIR   Path to Claude Code log directory (default: ~/.claude)
  --refresh SECONDS   Refresh interval in seconds (default: 1.0)
  --no-watch          Disable file watching (use polling only)
  --version           Show version number
  -h, --help          Show help message
```

## Features in Detail

### Sorting
Press `s` to cycle through sort options:
- **Last Activity** (default): Most recently active agents first
- **Cost**: Highest cost agents first
- **Tokens**: Most token-consuming agents first
- **Agent ID**: Alphabetical by ID

### Filtering
Press `f` to cycle through filters:
- **All** (default): Show all agents
- **Active**: Only running agents
- **Idle**: Recently active but idle
- **Waiting**: Agents waiting for user input
- **Stopped**: Inactive agents

### Notifications
When an agent needs user input, a yellow notification bar appears at the top showing which agent(s) are waiting.
