# Agent Command Center

אב טיפוס מקומי למערכת המנהלת שלושה פרופילים של סוכני AI: כללי, מחקר ויוזם.

**Status:** Development prototype. Not a production deployment. The repository is public; do not commit secrets or personal data.

## Architecture

* `app.py`: one central task orchestrator and local HTTP server
* `web/index.html`: Hebrew right to left management dashboard
* SQLite database: shared task history and memory
* Three agent profiles: `general`, `research`, `proactive`
* Background dispatcher with at most two concurrent model calls
* Proactive scheduler, disabled by default, with minimum 60 minute interval
* Daily cap: 20 tasks by default, configurable through settings database within the hard `AGENT_MAX_TASKS` ceiling

The model is invoked through the OpenAI Responses API. The research role requests a built in web search tool. This depends on API access and may incur charges. There is no automatic email sending, shell execution, purchases, messaging, or external write integration. High autonomy here means autonomous internal planning and generation, not unrestricted external actions.

## Run locally

Requires Python 3.10 or newer. No Python dependencies.

1. Clone the repository and switch to branch `feature/agent-command-center`.
2. Navigate to directory `agent-command-center`.
3. Set `OPENAI_API_KEY` in your shell environment, never in a source file. Set `OPENAI_MODEL` to an API model your project can access (defaults to `gpt-6.1-sol`).
4. Run `python app.py`.
5. Open `http://127.0.0.1:8765` in a browser.

Without the API key, the dashboard still opens and records tasks, but executions fail explicitly. It never invents a successful response.

## Tests

Run `python -m unittest discover -s tests -v` from `agent-command-center`. No API key or network required. GitHub Actions also runs these tests on commits to the feature branch.

## Controls and limitations

* Default bind address is loopback only. Do not expose this HTTP server directly to the Internet; it has no authentication or CSRF protection.
* Stop button pauses dispatching future queued work. It does **not** cancel an already running model call.
* A proactive goal can generate recurring analysis tasks. It is not a self modifying agent or unrestricted planner.
* The daily cap is a task count, **not** a strict monetary limit. Cost controls require provider spending limits, token accounting, per task budgets and throttles before production.
* Stored memory is local SQLite. Do not put credentials or sensitive personal data into prompts.
* Untrusted memory and external web content must not be treated as instructions. A future version should include explicit tool permission enforcement, authentication, detailed audit logs, robust retries, multi tenant storage and human approval for consequential actions.
* Data in `agent_center.sqlite3` is ignored in the recommended deployment and must never be committed.

## Suggested next steps

1. Add authenticated access before hosting.
2. Integrate budget enforcement and granular tool permissions.
3. Add task cancellation, retries and observability.
4. Add API connectors with approval requirements for writes.
5. Evaluate actual task success and research source quality against a fixed benchmark.
