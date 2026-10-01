import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from dotenv import load_dotenv
from typing import Annotated, List
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain.chat_models import init_chat_model
from typing_extensions import TypedDict
from pydantic import BaseModel, Field
from web_operations import serp_search, reddit_search_api, reddit_post_retrieval

from langchain_groq import ChatGroq

from prompts import (
    get_reddit_analysis_messages,
    get_google_analysis_messages,
    get_reddit_url_analysis_messages,
    get_synthesis_messages
)


#dataset


load_dotenv()
llm = ChatGroq(
    model="openai/gpt-oss-20b",
    temperature=0.3
)


class State(TypedDict):
    """Define the state or workflow of the agent and its contents"""
    messages: Annotated[str, add_messages] #add messages if the user wants
    user_question: str | None
    google_results: str | None

    #reddit
    reddit_results: str | None
    selected_reddit_urls: list[str] | None
    reddit_post_data: list | None #data for the selected URLs

    #analysis
    google_analysis: str | None
    reddit_analysis: str | None

    #final_answer
    final_answer: str | None

class RedditURLAnalysis(BaseModel):
    selected_urls: List[str] = Field(description="List of Reddit URLs that contain valuable information for answering the user's question")


def google_search(state: State):
    user_question = state.get("user_question", "")
    print(f"Searching Google for: {user_question}")

    google_results = serp_search(user_question, engine="google")

    return {"google_results": google_results}

def reddit_search(state: State):
    user_question = state.get("user_question", "")
    print(f"Searching Reddit for: {user_question}")

    reddit_results = reddit_search_api(keyword=user_question)
    print(reddit_results)

    return {"reddit_results": reddit_results}

def analyze_reddit_posts(state: State):
    user_question = state.get("user_question", "")
    reddit_results = state.get("reddit_results", "")

    if not reddit_results:
        return {"selected_reddit_urls": []}

    structured_llm = llm.with_structured_output(RedditURLAnalysis)
    messages = get_reddit_url_analysis_messages(user_question, reddit_results)

    try:
        analysis = structured_llm.invoke(messages)
        selected_urls = analysis.selected_urls

        print("Selected URLs:")
        for i, url in enumerate(selected_urls, 1):
            print(f"   {i}. {url}")

    except Exception as e:
        print(e)
        selected_urls = []

    return {"selected_reddit_urls": selected_urls}

def retrieve_reddit_posts(state: State):
    print("Getting reddit posts info...")

    selected_urls = state.get("selected_reddit_urls", [])

    if not selected_urls:
        return {"reddit_post_data": []}

    print(f"Processing {len(selected_urls)} Reddit URLs")

    reddit_post_data = reddit_post_retrieval(selected_urls)

    if reddit_post_data:
        print(f"Successfully got {len(reddit_post_data)} posts")
    else:
        print("Failed to get reddit posts data")
        reddit_post_data = []

    print(reddit_post_data)
    return {"reddit_post_data": reddit_post_data}


def analyze_google_results(state: State):
    print("Analyzing google search results")

    user_question = state.get("user_question", "")
    google_results = state.get("google_results", "")

    messages = get_google_analysis_messages(user_question, google_results)
    reply = llm.invoke(messages)

    return {"google_analysis": reply.content}

def analyze_reddit_results(state: State):
    print("Analyzing reddit search results")

    user_question = state.get("user_question", "")
    reddit_results = state.get("reddit_results", "")
    reddit_post_data = state.get("reddit_post_data", "")

    messages = get_reddit_analysis_messages(user_question, reddit_results, reddit_post_data)
    reply = llm.invoke(messages)

    return {"reddit_analysis": reply.content}



#synthesis final result(all results)

def synthesize_analyses(state: State):
    print("Combine all results together...")

    user_question = state.get("user_question", "")
    google_analysis = state.get("google_analysis", "")

    reddit_analysis = state.get("reddit_analysis", "")

    messages = get_synthesis_messages(
        user_question, google_analysis, reddit_analysis
    )

    reply = llm.invoke(messages)
    final_answer = reply.content

    return {"final_answer": final_answer, "messages": [{"role": "assistant", "content": final_answer}]}


#-------GRAPH NODES - LANGGRAPH ---------

graph_builder = StateGraph(State)

graph_builder.add_node("google_search", google_search)
graph_builder.add_node("reddit_search", reddit_search)
graph_builder.add_node("analyze_reddit_posts", analyze_reddit_posts)
graph_builder.add_node("retrieve_reddit_posts", retrieve_reddit_posts)
graph_builder.add_node("analyze_google_results", analyze_google_results)
graph_builder.add_node("analyze_reddit_results", analyze_reddit_results)
graph_builder.add_node("synthesize_analyses", synthesize_analyses)


#----- CONNECT EDGES -----
graph_builder.add_edge(START, "google_search")
graph_builder.add_edge(START, "reddit_search")


#connect google search directly to google analysis (parallel path)
graph_builder.add_edge("google_search", "analyze_google_results")

#connect reddit search to reddit post analysis
graph_builder.add_edge("reddit_search", "analyze_reddit_posts")

#retrieve reddit posts
graph_builder.add_edge("analyze_reddit_posts", "retrieve_reddit_posts")

#retrieve reddit posts feeds reddit analysis
graph_builder.add_edge("retrieve_reddit_posts", "analyze_reddit_results")

#both analyses feed synthesizer
graph_builder.add_edge("analyze_google_results", "synthesize_analyses")
graph_builder.add_edge("analyze_reddit_results", "synthesize_analyses")
graph_builder.add_edge("synthesize_analyses", END)

#compile graph
graph = graph_builder.compile()


def run_chatbot():
    print("Multi-Source Research Analysis Agent")
    print("Type 'exit' to quit\n")

    while True:
        user_input = input("Ask me anything: ")
        if user_input.lower() == "exit":
            print("Exiting...Bye, take care now.")
            break

        state = {
            "messages": [{"role": "user", "content": user_input}],
            "user_question": user_input,
            "google_results": None,

            "reddit_results": None,
            "selected_reddit_urls": None,
            "reddit_post_data": None,
            "google_analysis": None,

            "reddit_analysis": None,
            "final_answer": None,
        }

        print("\nStarting parallel research process...")
        print("Launching Google and Reddit searches...\n")
        final_state = graph.invoke(state)

        if final_state.get("final_answer"):
            print(f"\nFinal Answer:\n{final_state.get('final_answer')}\n")

        print("-" * 80)


if __name__ == "__main__":
    run_chatbot()



