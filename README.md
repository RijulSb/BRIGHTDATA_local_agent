<strong>Multi-Source Research Analysis Agent</strong>


A local-first, graph-orchestrated research agent that combines search-engine discovery, Reddit context, structured URL selection, targeted post retrieval, and evidence-aware LLM synthesis.




 

</details> <details>
<summary><strong>🧭 Quick navigation</strong> — click an icon to jump</summary>   

Section
What you will find
🎯
The problem
The research and engineering gap this agent addresses
🧠
LLM strategy
Multi-pass reasoning, structured output, and evaluation guidance
🔀
Architecture
The parallel search and synthesis graph
🛠️
Tool reference
Responsibilities and boundaries for every tool
🛡️
Security
Current controls and production hardening
✅
Quality gates
Formatting, linting, typing, tests, and dependency scanning
🚀
Roadmap
The path from prototype to production




</details>

Why this project exists

Most AI assistants produce an answer from a single conversational context. That is convenient, but it can make the answer difficult to audit, vulnerable to source blind spots, and disconnected from the lived experience captured in community discussions.

This project treats research as a repeatable information pipeline, not a single prompt:

1.
Discover broad web evidence through Google-oriented search.

2.
Discover practical, first-hand discussion through Reddit.

3.
Use a structured LLM decision to identify the Reddit URLs worth deeper retrieval.

4.
Analyze the two evidence streams separately so one source type does not dominate the other.

5.
Synthesize both analyses into one response to the original question.

The result is a compact example of how to build an agent that is observable, decomposable, locally runnable, and extensible.

The problem it solves

When a question is ambiguous, current, technical, or experience-driven, a single model response often has predictable weaknesses:

•
Coverage gaps: the model may not know which sources matter for the specific question.

•
Weak source diversity: search-engine results and community experience answer different parts of a problem.

•
Context overload: sending every raw result into one prompt wastes context and increases noise.

•
Poor controllability: a monolithic prompt makes it hard to isolate failures or replace one stage.

•
Difficult debugging: when the final answer is wrong, it is unclear whether discovery, retrieval, selection, analysis, or synthesis failed.

This agent addresses those weaknesses by turning research into explicit graph nodes with typed state. Each stage can be inspected, tested, replaced, retried, or upgraded independently.

Why choose a local coding/research agent?

This project is not positioned as a replacement for general-purpose products such as Gemini or Claude. Those products are excellent conversational interfaces. The value here is different: engineering control over the reasoning workflow.

General-purpose AI app
This local-first agent
Optimized for a broad chat experience
Optimized for a specific, inspectable research workflow
Internal orchestration is mostly opaque
The workflow is explicit in Python and LangGraph
Source strategy may vary from turn to turn
Google and Reddit are deliberate, repeatable evidence channels
Harder to reproduce an answer path
State, nodes, and transitions define a reproducible execution model
Limited control over data handling
Credentials and execution remain under the developer's control
Extension often depends on product features
Add a node, tool, validator, evaluator, or data source directly
Best for general assistance
Best for domain-specific research and engineering workflows




A local agent is especially valuable when a team needs:

•
Data and credential ownership rather than sending everything through an opaque hosted workflow.

•
Provider flexibility, including an OpenAI-compatible model served through Groq today and other providers later.

•
Deterministic orchestration with explicit fan-out, joins, and state transitions.

•
Testability at the tool, node, graph, and end-to-end levels.

•
Integration with private systems, internal APIs, repositories, databases, or development tools.

•
Operational control, including rate limits, retries, logging, redaction, caching, and deployment topology.

•
A path from prototype to production without rewriting the research logic inside a different platform.


The key differentiator is not “another chatbot.” It is a transparent, programmable research system whose decisions can be inspected and improved by an engineering team.

Architecture

mermaid

Source



The graph is built with StateGraph, making the workflow explicit rather than hiding control flow inside one large agent loop. Google and Reddit discovery begin from START, execute as independent branches, and converge at the synthesis node.

End-to-end execution flow

1. Input and state initialization

run_chatbot() provides a minimal terminal interface. For every question, it creates a fresh State object containing the user message and empty slots for discovery results, analyses, selected URLs, retrieved posts, and the final answer.

This gives each run a clear state boundary and avoids accidental reuse of a previous question's intermediate data.

2. Parallel Google discovery

google_search(state) calls:

Python


serp_search(user_question, engine="google")



The raw result is stored in google_results. This branch is intended to maximize breadth and surface documentation, articles, product pages, and other web evidence.

3. Parallel Reddit discovery

reddit_search(state) calls:

Python


reddit_search_api(keyword=user_question)



The raw result is stored in reddit_results. Reddit adds a complementary signal: implementation experience, failure modes, trade-offs, and practical opinions that may not appear in polished web content.

4. Structured Reddit URL selection

analyze_reddit_posts(state) uses Pydantic and LangChain structured output:

Python


class RedditURLAnalysis(BaseModel):
    selected_urls: List[str]



The LLM receives the question and Reddit search results through get_reddit_url_analysis_messages(...). It must return a schema-conforming list of URLs instead of free-form prose.

This is an important reliability pattern: use natural language for interpretation, but use a typed contract for decisions that drive downstream tools.

5. Targeted Reddit retrieval

retrieve_reddit_posts(state) passes only the selected URLs to:

Python


reddit_post_retrieval(selected_urls)



This creates a lightweight relevance filter before deeper retrieval, reducing unnecessary requests and keeping later analysis focused.

6. Independent evidence analysis

The two source types are analyzed separately:

•
analyze_google_results(state) calls get_google_analysis_messages(...).

•
analyze_reddit_results(state) calls get_reddit_analysis_messages(...) with search results and retrieved post data.

Both stages use the configured LLM, but preserve source boundaries so web evidence and community evidence can be compared during synthesis rather than blended prematurely.

7. Final synthesis

synthesize_analyses(state) calls get_synthesis_messages(...) with the original question and both analyses. The final response is saved in final_answer and appended to the graph's message history.

The synthesizer is therefore responsible for combining already-processed evidence, not for doing all discovery and interpretation from scratch.

Tool-by-tool reference

serp_search

Location: web_operations.py (expected companion module)

Role: Search the web using a search-engine backend. In the current graph it is invoked with engine="google".

Input: The user's natural-language question.

Output: Search results stored as google_results.

Why it matters: Provides broad discovery and helps anchor the answer in publicly indexed web material.

Production considerations: Add provider timeouts, retry/backoff, response-size limits, source normalization, caching, and explicit provenance fields such as title, URL, snippet, and retrieval timestamp.

reddit_search_api

Location: web_operations.py (expected companion module)

Role: Find Reddit discussions relevant to the user's question.

Input: keyword=user_question.

Output: Search results stored as reddit_results.

Why it matters: Surfaces practical experiences, edge cases, and community disagreement that broad web search may underrepresent.

Production considerations: Respect Reddit's terms and rate limits, validate returned URLs, normalize result shape, and handle deleted, private, NSFW, or inaccessible content explicitly.

reddit_post_retrieval

Location: web_operations.py (expected companion module)

Role: Retrieve detailed content for the Reddit URLs selected by the structured LLM step.

Input: list[str] of selected URLs.

Output: Detailed post data stored as reddit_post_data.

Why it matters: Separates inexpensive discovery from deeper retrieval and avoids analyzing every candidate result.

Production considerations: Enforce a maximum URL count, allow-list the Reddit host, set request timeouts, sanitize HTML, cap body size, and retain source metadata for auditability.

LangGraph StateGraph

Role: Orchestrate the stateful workflow and define graph edges between tools, analysis nodes, and synthesis.

Why it matters: Makes parallel branches and convergence explicit, enabling node-level testing, tracing, retries, and future human-in-the-loop checkpoints.

ChatGroq

Role: Provide the chat model used for structured selection, source analysis, and final synthesis.

Current configuration:

Python


llm = ChatGroq(
    model="openai/gpt-oss-20b",
    temperature=0.3,
)



The low temperature favors consistent analysis while preserving enough flexibility for open-ended synthesis. The model is instantiated once and reused across nodes.

Pydantic BaseModel and Field

Role: Define the contract for structured Reddit URL selection.

Why it matters: Typed output reduces downstream parsing ambiguity and creates a natural validation boundary between LLM reasoning and network operations.

python-dotenv

Role: Load environment variables from a local .env file via load_dotenv().

Security benefit: Keeps API credentials out of source code. Never commit .env; provide a redacted .env.example instead.

Prompt builder functions

Location: prompts.py (expected companion module)

The four prompt builders separate prompt policy from orchestration code:

•
get_reddit_url_analysis_messages(...) — instructs the model to select useful Reddit URLs.

•
get_google_analysis_messages(...) — frames interpretation of web results.

•
get_reddit_analysis_messages(...) — frames interpretation of Reddit search and post data.

•
get_synthesis_messages(...) — combines both analysis streams into a final answer.

This separation makes prompts versionable, reviewable, unit-testable, and easier to evaluate independently from graph mechanics.




main.py design review

Strengths

•
Clear graph boundaries and named nodes.

•
Parallel source discovery from START.

•
Typed workflow state through TypedDict.

•
Schema-constrained LLM output for URL selection.

•
Graceful empty-result handling for Reddit selection and retrieval.

•
Source-specific analysis before final synthesis.

•
Environment-based configuration rather than hard-coded secrets.

Recommended next refactors

•
Move graph construction into graph.py and CLI code into cli.py.

•
Replace print() calls with structured logging and correlation IDs.

•
Introduce typed models for search results and Reddit post data instead of raw str and list values.

•
Add explicit timeouts, retries, rate limits, and error categories to the web adapters.

•
Add a configuration object for model name, temperature, result limits, and feature flags.

•
Add provenance to the final answer so users can inspect the supporting URLs.

•
Add a graph-level test fixture that replaces live tools with deterministic fakes.

•
Validate that selected URLs are well-formed and belong to approved domains before retrieval.

LLM strategy

The system uses a multi-pass, role-specific LLM strategy rather than a single giant prompt:

1.
Selection: The model chooses high-value Reddit URLs under a strict Pydantic schema.

2.
Google analysis: The model interprets broad web evidence independently.

3.
Reddit analysis: The model interprets community search results and retrieved post content independently.

4.
Synthesis: The model combines the two analyses in the context of the original question.

This architecture has several benefits:

•
Decomposition: Each model call has one job and a smaller context.

•
Controllability: Prompts can be tuned per evidence type.

•
Failure isolation: A failed selection step does not require changing synthesis logic.

•
Evaluation: Each stage can be scored separately for relevance, grounding, and completeness.

•
Provider portability: The orchestration layer is separated from the model provider.

•
Cost control: Deep retrieval is applied only after URL selection.

Recommended production-grade LLM safeguards

The current implementation provides the workflow foundation. For production use, add:

•
Explicit instructions to distinguish facts, opinions, uncertainty, and missing evidence.

•
Citation or URL references in intermediate analyses and final output.

•
Context truncation and token budgeting for large search responses and posts.

•
Prompt-injection defenses for untrusted web content; treat retrieved text as data, never instructions.

•
Structured output validation with a second-pass repair or deterministic fallback.

•
Model response timeouts, bounded retries, and provider failover.

•
Offline evaluation sets covering ambiguous questions, adversarial content, empty results, and conflicting sources.

•
Observability for latency, token usage, tool failures, selected URL quality, and synthesis quality.

Security and trust model

Security practices already reflected in the design

•
Secrets via environment variables: load_dotenv() supports local configuration without embedding credentials in Python.

•
Separation of concerns: Network operations live behind adapter functions rather than being scattered through prompts or synthesis code.

•
Typed boundary before retrieval: The selected URL list is validated by Pydantic before it drives downstream retrieval.

•
Bounded workflow stages: Explicit nodes make it possible to apply per-stage limits and permissions.

•
Local execution: Developers can inspect and control the code, model endpoint, logs, and network policy.

Hardening required before production

The snapshot does not yet implement all of the following controls; they are the recommended security baseline:

•
Never commit .env, API keys, cookies, or scraped personal data.

•
Allow-list outbound hosts and validate URL schemes (https only ).

•
Enforce request timeouts, response-size limits, concurrency limits, and rate limits.

•
Redact credentials, authorization headers, personal data, and raw sensitive content from logs.

•
Sanitize retrieved HTML and treat all external text as untrusted input.

•
Defend against indirect prompt injection by isolating content from instructions.

•
Use least-privilege API keys and separate development and production credentials.

•
Pin dependencies and scan them with tools such as pip-audit.

•
Run the agent in a restricted environment when processing untrusted content.

•
Add an explicit data-retention policy for search results, Reddit posts, traces, and caches.

Linting, formatting, and quality gates

A professional repository should make quality checks executable, not aspirational. The current single-file snapshot does not include configuration files yet, so the following baseline is recommended:

Bash


python -m pip install ruff mypy pytest pip-audit

ruff format .
ruff check .
mypy .
pytest -q
pip-audit



Suggested CI gates:

1.
ruff format --check . — formatting consistency.

2.
ruff check . — correctness and maintainability rules.

3.
mypy . — static type validation for graph state and tool boundaries.

4.
pytest -q — deterministic unit and graph tests.

5.
pip-audit — dependency vulnerability scanning.

6.
Secret scanning with a repository-approved tool such as Gitleaks.

High-value tests include:

•
Empty Google and Reddit responses.

•
Malformed or non-Reddit URLs returned by the model.

•
Structured-output parsing failures.

•
Tool timeouts and retry exhaustion.

•
Conflicting evidence between Google and Reddit.

•
Oversized result payloads.

•
Synthesis when one evidence branch is unavailable.

•
A full graph run using mocked search and retrieval adapters.

Setup

The uploaded snapshot includes main.py and references web_operations.py and prompts.py. Those companion modules and dependency metadata must be present before the application can run end to end.

1. Create an environment

Bash


python -m venv .venv
source .venv/bin/activate       # Windows: .venv\\Scripts\\activate
python -m pip install --upgrade pip



2. Install dependencies

At minimum, the code imports packages corresponding to:

Bash


pip install langgraph langchain langchain-groq langchain-core pydantic python-dotenv typing-extensions



Install the project-specific search and Reddit client dependencies required by web_operations.py as well.

3. Configure secrets

Create a local .env file and add the credentials required by your model provider and search/retrieval adapters. The exact variable names depend on the implementation of web_operations.py and provider configuration.

Plain Text


# Example only — use the names expected by your adapters
GROQ_API_KEY=replace_me
SEARCH_API_KEY=replace_me



Do not commit this file.

4. Run the agent

Bash


python main.py



Then enter a question at the prompt. Type exit to stop the process.

Project status

This repository is currently a focused prototype / research implementation. It demonstrates the core orchestration pattern and LLM strategy clearly, but the provided snapshot does not yet include the imported web_operations.py and prompts.py modules, dependency locking, automated tests, CI, or production-grade observability.

That distinction is intentional: the README documents both what exists today and the concrete engineering path required to harden it for production.

Roadmap




Add typed models for search results, Reddit posts, citations, and final answers.




Add pyproject.toml, locked dependencies, and reproducible development commands.




Implement retry, timeout, rate-limit, caching, and provider-fallback policies.




Add source citations and provenance to the final response.




Add unit, integration, adversarial, and regression tests.




Add structured logs, traces, metrics, and run IDs.




Add prompt-injection and untrusted-content defenses.




Add configurable model routing and token budgets.




Add a non-interactive CLI/API mode for CI and application integration.




Add evaluation datasets and quality dashboards.

Design principles

•
Explicit over magical: graph edges and state transitions are visible.

•
Typed over implicit: structured outputs create reliable boundaries.

•
Evidence over confidence: source diversity matters more than fluent prose.

•
Composable over monolithic: tools, prompts, analysis, and synthesis can evolve independently.

•
Secure by construction: secrets, untrusted content, network access, and logs should have clear boundaries.

•
Testable by default: every node should be runnable with deterministic fixtures.

•
Local-first, provider-flexible: own the workflow while retaining model choice.

License

No license is included in the current snapshot. Add an explicit license before distributing or accepting external contributions.

