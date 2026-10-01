🔍 Multi-Source RAG Research Agent (Bright Data + LangGraph)
An autonomous multi-source research agent that combines real-time Google Search data and deep Reddit Community Discussions using Bright Data APIs and LangGraph, synthesizing balanced, evidence-backed answers with LLMs (Groq / GPT-OSS).

🎯 Problem Solving: What Challenge Does This Solve?
Standard AI chatbots and single-source RAG (Retrieval-Augmented Generation) systems suffer from major real-world research limitations:

🚫 Surface-Level & Sanitized Web Results: Standard search engines prioritize SEO-optimized articles, marketing copy, and official documentation, which often lack real-world customer sentiment, practical troubleshooting tips, and authentic experiences.
🚫 Unverified Social Echo Chambers: Relying solely on forums like Reddit can introduce subjective bias, misinformation, and lack of verified technical or factual validation.
🚫 Anti-Scraping & Rate Limiting Roadblocks: Scraping search engines and social platforms directly leads to IP bans, CAPTCHAs, and flaky scrapers.
🚫 Reddit Information Noise & Overload: Keyword searches on Reddit return hundreds of unrelated discussions. Reading through every thread manually or feeding raw noisy threads into an LLM exceeds context windows and degrades answer quality.
💡 The Solution
This agent addresses these problems through an automated multi-stage pipeline:

🌐 Reliable Data Ingestion via Bright Data: Uses Bright Data SERP API for live Google search and Bright Data Web Scraper Datasets for structured Reddit discovery and comment retrieval without bot blocks or CAPTCHAs.
⚡ Parallel Research Orchestration: Runs Google search and Reddit keyword discovery simultaneously using a LangGraph state machine.
🧠 Smart URL Filtering: Employs structured LLM outputs (RedditURLAnalysis) to scan candidate Reddit posts and cherry-pick only high-value, substantive threads.
📥 Deep Comment Retrieval: Pulls the full discussion trees and comments for the selected threads via snapshot datasets.
⚖️ Dual-Perspective Analysis & Synthesis: Evaluates factual authority (Google) alongside user experiences and community sentiment (Reddit), synthesizing them into a coherent report with source attribution.
🏗️ Architecture & Workflow

                          [ START ]
                             │
            ┌────────────────┴────────────────┐
            ▼                                 ▼
   [ 🌐 google_search ]              [ 💬 reddit_search ]
            │                                 │
            ▼                                 ▼
[ 📊 analyze_google_results ]     [ 🎯 analyze_reddit_posts ]
            │                                 │
            │                                 ▼
            │                    [ 📥 retrieve_reddit_posts ]
            │                                 │
            │                                 ▼
            │                    [ 💬 analyze_reddit_results ]
            └────────────────┬────────────────┘
                             ▼
                 [ 📑 synthesize_analyses ]
                             │
                             ▼
                          [ END ]
📁 Repository Structure

.
├── main.py                 # LangGraph state definition, graph nodes, and CLI runner
├── streamlit_app.py        # Streamlit web UI with chat interface and inspection tabs
├── web_operations.py       # Bright Data SERP and Dataset API integrations
├── snapshot_operations.py  # Asynchronous Bright Data snapshot polling and downloads
├── prompts.py              # Prompt engineering templates and message builders
├── sample.py               # Quick sanity check for Bright Data SERP API
├── requirements.txt        # Project dependencies
└── README.md               # Project documentation
🛠️ Necessary Functions & Core Modules
1. web_operations.py (Data Extraction Layer)
Handles communication with Bright Data endpoints:

🔹 serp_search(query, engine="google"): Sends an authenticated POST request to Bright Data SERP API (zone: serp_api1) to retrieve Google search results (knowledge graphs and organic listings).
🔹 reddit_search_api(keyword, date="All time", sort_by="Hot", num_of_posts=80): Triggers a discovery job on Bright Data Dataset (gd_lvz8ah06191smkebj4) to find candidate Reddit threads matching the query.
🔹 reddit_post_retrieval(urls, days_back=12, load_all_replies=False, comment_limit=""): Triggers a snapshot retrieval job on Bright Data Dataset (gd_lvzdpsdlw09j6t702) to extract full comments and discussion trees for selected URLs.
🔹 _make_api_request(url, **kwargs): Internal helper managing HTTP headers, Bearer authorization, and error handling for Bright Data endpoints.
🔹 _trigger_and_download_snapshot(trigger_url, params, data, operation_name): Coordinates the asynchronous workflow: triggering a dataset snapshot, awaiting readiness, and parsing the payload.
2. snapshot_operations.py (Async Snapshot Engine)
Handles dataset collection lifecycles:

🔹 poll_snapshot_status(snapshot_id, max_attempts=90, delay=10): Polls https://api.brightdata.com/datasets/v3/progress/{snapshot_id} every 10 seconds until status becomes ready or failed.
🔹 download_snapshot(snapshot_id, format="json"): Fetches the complete dataset JSON payload once generation completes.
3. prompts.py (Prompt Templates & Factories)
Maintains system prompts and user message formatters:

🔹 PromptTemplates.reddit_url_analysis_system() / ...user(): Directs the LLM to inspect search results and select Reddit URLs that contain meaningful technical discussions and community consensus.
🔹 PromptTemplates.google_analysis_system() / ...user(): Guides extraction of factual claims, authoritative sources, official documentation, and statistics.
🔹 PromptTemplates.reddit_analysis_system() / ...user(): Extracts community sentiment, firsthand user testimonials, controversies, and direct quotes.
🔹 PromptTemplates.synthesis_system() / ...user(): Fuses findings from both channels, highlights points of consensus or contradictions, and builds a comprehensive summary.
🔹 create_message_pair(system_prompt, user_prompt): Helper generating standard {"role": "system" | "user", "content": ...} message structures.
4. main.py (LangGraph Orchestration & Agent State)
Defines the graph execution pipeline and CLI:

🔹 State: TypedDict tracking the query, raw API outputs, filtered URLs, Reddit comments, independent analyses, and the final combined synthesis.
🔹 RedditURLAnalysis: Pydantic model enforcing structured output (selected_urls: List[str]) from the LLM.
🔹 Graph Node Functions:
google_search(state): Queries Google SERP.
reddit_search(state): Discovers Reddit discussions.
analyze_reddit_posts(state): Runs structured LLM curation on discovered Reddit links.
retrieve_reddit_posts(state): Pulls deep comments for curated links.
analyze_google_results(state): Analyzes Google data.
analyze_reddit_results(state): Analyzes Reddit comments.
synthesize_analyses(state): Merges both analyses into the final response.
🔹 run_chatbot(): Interactive command-line loop allowing users to submit queries and inspect final answers in real-time.
5. streamlit_app.py (Web Dashboard)
Provides an interactive web UI:

🔹 load_graph(): Cached initialization of the LangGraph agent workflow (@st.cache_resource).
🔹 Chat interface rendering query history, real-time research status indicators (st.status), final syntheses, and expandable drawers for:
📊 Google Analysis (Facts, stats, and documentation)
💬 Reddit Analysis (User discussions, opinions, and quotes)
⚙️ Prerequisites & Environment Setup
1. API Keys Required
🔑 Bright Data API Key (BRIGHTDATA_API_KEY): Used to access the SERP API and dataset discovery/snapshot endpoints.
🔑 Groq API Key (GROQ_API_KEY): Used to run LLM inference via ChatGroq.
2. Environment Variables (.env)
Create a .env file in the root directory:

env

BRIGHTDATA_API_KEY=your_brightdata_api_key_here
GROQ_API_KEY=your_groq_api_key_here
📦 Installation
Clone the repository:

bash

git clone <repo-url>
cd RAG_agent_BRIGHTDATA
Create and activate a virtual environment:

bash

python -m venv venv
# On Windows:
.\venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
Install dependencies:

bash

pip install -r requirements.txt
pip install langgraph langchain-groq streamlit
🚀 Running the Agent
Option A: Interactive Web UI (Streamlit)
Launch the browser dashboard:

bash

streamlit run streamlit_app.py
Open http://localhost:8501 in your browser, enter your question, and inspect the final synthesis along with side-by-side Google and Reddit breakdowns.

Option B: Command-Line Interface (CLI)
Run the terminal chatbot:

bash

python main.py
Type your query at the prompt and review the step-by-step progress and final answer. Type exit to quit.

Option C: Connectivity Verification
Test your Bright Data SERP API setup:

bash

python sample.py
🛡️ Key Technologies
🤖 LangGraph & LangChain: Stateful graph orchestration and multi-agent workflow management.
⚡ Groq (ChatGroq): High-speed LLM inference for analysis, filtering, and synthesis.
🌐 Bright Data:
SERP API (serp_api1) for real-time search engine data.
Web Scraper Datasets (gd_lvz8ah06191smkebj4 and gd_lvzdpsdlw09j6t702) for Reddit thread discovery and comment extraction.
🎈 Streamlit: Clean, responsive frontend with live execution status and accordion drawers.
