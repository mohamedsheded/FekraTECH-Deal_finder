from typing import Dict, Any, List, Annotated, Literal, Optional, TypedDict
from langgraph.graph import StateGraph, END, START
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph.message import add_messages

from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, AIMessage, BaseMessage
import re
from urllib.parse import urlparse
from pydantic import BaseModel, Field
from datetime import datetime

from models import ActionClassification
from web_searcher import WebSearcher
from offer_comparator import OfferComparator
from config import DEFAULT_MODEL, MAX_TOKENS, OPENAI_API_KEY
from dotenv import load_dotenv
import os

load_dotenv()
# os.environ['TAVILY_API_KEY'] = TAVILY_API_KEY
# os.environ['OPENAI_API_KEY'] = OPENAI_API_KEY
# Simplified AgentState using TypedDict for LangGraph compatibility
class AgentState(TypedDict):
    """State maintained by the LangGraph agent"""
    messages: Annotated[List[BaseMessage], add_messages]
    user_input: str
    action_type: str
    search_results: List[Any]  # ProductOffer
    comparison_result: Optional[Any]  # ComparisonResult
    citations: List[str]

class ProductChatAgent:
    """Main chat agent that handles product search, comparison, and chat"""

    def __init__(self):
        self.llm = ChatOpenAI(
            model=DEFAULT_MODEL,
            temperature=0.1,
            max_tokens=MAX_TOKENS,
            api_key=OPENAI_API_KEY
        )

        # Create a separate LLM instance for structured output
        self.structured_llm = self.llm.with_structured_output(ActionClassification)

        self.web_searcher = WebSearcher()
        self.comparator = OfferComparator()

        # Initialize memory saver
        self.memory = MemorySaver()
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow with memory"""
        workflow = StateGraph(AgentState)

        # Add nodes
        workflow.add_node("analyze_input", self._analyze_input)
        workflow.add_node("search_products", self._search_products)
        workflow.add_node("extract_from_url", self._extract_from_url)
        workflow.add_node("compare_offers", self._compare_offers)
        workflow.add_node("generate_response", self._generate_response)

        # Add edges with proper routing
        workflow.add_edge(START, "analyze_input")

        # Add conditional edges from analyze_input
        workflow.add_conditional_edges(
            "analyze_input",
            self._route_input,
            {
                "search_products": "search_products",
                "extract_from_url": "extract_from_url",
                "default_chat": "generate_response"
            }
        )

        # Direct edges to comparison and response
        workflow.add_edge("search_products", "compare_offers")
        workflow.add_edge("extract_from_url", "generate_response")
        workflow.add_edge("compare_offers", "generate_response")
        workflow.add_edge("generate_response", END)

        # Compile with memory saver
        return workflow.compile(checkpointer=self.memory)

    def _analyze_input(self, state: AgentState) -> Dict[str, Any]:
        """Analyze user input to determine the action needed using structured output"""
        user_input = state["user_input"]
        print(f"Analyzing user input: {user_input}")

        # Create prompt for action classification
        analysis_prompt = f"""
        Analyze the following user input and determine what type of action should be performed:

        User Input: "{user_input}"

        Classification Guidelines:
        1. "search_products" - If the user is asking to find, search for, compare products, or asking about deals/prices for items
           Examples: "find the best laptop", "search for headphones", "compare iPhone prices", "look for deals on TVs"

        2. "extract_from_url" - If the user has provided a URL (starting with http:// or https://) and wants information about that specific product
           Examples: "https://amazon.com/product-link", "check this deal: https://...", any message containing a URL

        3. "default_chat" - For general conversation, questions not related to product search, or unclear requests
           Examples: "hello", "how are you?", "what can you do?", "thanks", general questions

        Choose the most appropriate action type and provide reasoning for your decision.
        """

        try:
            # Get structured classification from LLM
            classification = self.structured_llm.invoke([HumanMessage(content=analysis_prompt)])

            print(f"LLM Classification: {classification.action_type}")
            print(f"Reasoning: {classification.reasoning}")

            action_type = classification.action_type

        except Exception as e:
            print(f"Error in structured classification: {e}")
            # Fallback to rule-based classification
            action_type = self._fallback_classification(user_input)

        return {"action_type": action_type}

    def _fallback_classification(self, user_input: str) -> str:
        """Fallback rule-based classification if structured output fails"""
        user_input_lower = user_input.lower()

        # Check if input contains a URL
        url_pattern = re.compile(r'https?://[^\s]+')
        if url_pattern.search(user_input):
            print("URL detected - fallback")
            return "extract_from_url"

        # Check if input is a product search query
        search_keywords = ['find', 'search', 'look for', 'compare', 'best price', 'deal',
                          'buy', 'purchase', 'shop', 'price', 'cost', 'cheap', 'expensive']
        if any(keyword in user_input_lower for keyword in search_keywords):
            print("Product search detected - fallback")
            return "search_products"

        print("Defaulting to chat - fallback")
        return "default_chat"

    def _route_input(self, state: AgentState) -> str:
        """Route the input to appropriate node based on action_type"""
        return state["action_type"]

    def _search_products(self, state: AgentState) -> Dict[str, Any]:
        """Search for products based on user query"""
        search_query = state["user_input"]
        print(f"Searching for: {search_query}")

        # Perform web search
        offers = self.web_searcher.search_products(search_query)

        return {"search_results": offers}

    def _extract_from_url(self, state: AgentState) -> Dict[str, Any]:
        """Extract product information from a pasted URL"""
        # Extract URL from user input
        url_pattern = re.compile(r'https?://[^\s]+')
        url_match = url_pattern.search(state["user_input"])

        search_results = []
        if url_match:
            url = url_match.group()
            print(f"Extracting from URL: {url}")
            offer = self.web_searcher.extract_from_url(url)
            if offer:
                search_results = [offer]

        return {"search_results": search_results}

    def _compare_offers(self, state: AgentState) -> Dict[str, Any]:
        """Compare offers and find the best deal"""
        comparison_result = None

        if state["search_results"]:
            try:
                comparison_result = self.comparator.compare_offers(state["search_results"])
                print(f"Comparison completed: {comparison_result.best_offer.title}")
            except Exception as e:
                print(f"Comparison error: {e}")

        return {"comparison_result": comparison_result}

    def _generate_response(self, state: AgentState) -> Dict[str, Any]:
        """Generate the final response using LLM"""
        # Prepare context for LLM
        context_parts = []

        # Add conversation history from messages
        if state.get("messages"):
            context_parts.append("Previous conversation:")
            for msg in state["messages"]:
                role = "User" if isinstance(msg, HumanMessage) else "Assistant"
                context_parts.append(f"{role}: {msg.content}")

        # Add search results
        if state.get("search_results"):
            context_parts.append("\nProduct offers found:")
            for i, offer in enumerate(state["search_results"], 1):
                context_parts.append(f"{i}. {offer.title}")
                if offer.price:
                    context_parts.append(f"   Price: {offer.price}")
                context_parts.append(f"   Source: {offer.source}")
                if offer.description:
                    context_parts.append(f"   Description: {offer.description[:100]}...")
                context_parts.append("")

        # Add comparison result
        if state.get("comparison_result"):
            context_parts.append("Best offer analysis:")
            context_parts.append(f"Best: {state['comparison_result'].best_offer.title}")
            context_parts.append(f"Price: {state['comparison_result'].best_offer.price}")
            context_parts.append(f"Source: {state['comparison_result'].best_offer.source}")
            context_parts.append(f"Reasoning: {state['comparison_result'].reasoning}")

        # Generate response using LLM
        context_text = "\n".join(context_parts)

        prompt = f"""You are a helpful product comparison assistant.
        Based on the following information, provide a natural, helpful response to the user.

        Context:
        {context_text}

        User's current request: {state["user_input"]}

        Provide a helpful response with citations to the sources. Be conversational and helpful."""

        response = self.llm.invoke([HumanMessage(content=prompt)])

        # Extract citations
        citations = self._extract_citations(response.content)

        # Return both the response message and citations
        return {
            "messages": [AIMessage(content=response.content)],
            "citations": citations
        }

    def _extract_citations(self, text: str) -> List[str]:
        """Extract citations from LLM response"""
        citations = []

        # Look for URLs in the text
        url_pattern = re.compile(r'https?://[^\s]+')
        urls = url_pattern.findall(text)
        citations.extend(urls)

        # Look for source mentions
        source_pattern = re.compile(r'from\s+([^\s,]+)', re.IGNORECASE)
        sources = source_pattern.findall(text)
        citations.extend(sources)

        return list(set(citations))

    def chat(self, user_input: str, thread_id: str = "default") -> Dict[str, Any]:
        """Main chat interface using thread_id for memory management"""

        # Create initial state with user message
        initial_state = {
            "messages": [HumanMessage(content=user_input)],
            "user_input": user_input,
            "action_type": "",
            "search_results": [],
            "comparison_result": None,
            "citations": []
        }

        # Configuration with thread_id for memory
        config = {"configurable": {"thread_id": thread_id}}

        # Run the graph with memory
        final_state = self.graph.invoke(initial_state, config=config)

        return {
            "response": final_state["messages"][-1].content if final_state["messages"] else "",
            "citations": final_state.get("citations", []),
            "search_results": final_state.get("search_results", []),
            "comparison_result": final_state.get("comparison_result"),
            "thread_id": thread_id
        }

    def get_chat_history(self, thread_id: str = "default") -> List[Dict[str, Any]]:
        """Get formatted chat history for a specific thread"""
        try:
            # Get the current state for the thread
            config = {"configurable": {"thread_id": thread_id}}
            current_state = self.graph.get_state(config)

            history = []
            if current_state and current_state.values.get("messages"):
                for msg in current_state.values["messages"]:
                    history.append({
                        "role": "user" if isinstance(msg, HumanMessage) else "assistant",
                        "content": msg.content,
                        "timestamp": datetime.now().isoformat()  # You might want to store actual timestamps
                    })

            return history

        except Exception as e:
            print(f"Error retrieving chat history: {e}")
            return []

    def clear_thread(self, thread_id: str):
        """Clear conversation history for a specific thread"""
        try:
            config = {"configurable": {"thread_id": thread_id}}
            # This will effectively clear the thread by starting fresh
            self.memory.delete_state(config)
            print(f"Cleared thread: {thread_id}")
        except Exception as e:
            print(f"Error clearing thread: {e}")
