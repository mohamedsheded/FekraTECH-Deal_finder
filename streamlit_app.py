import streamlit as st
import uuid
from datetime import datetime
import json

from config import APP_TITLE, APP_DESCRIPTION
from product_agent import ProductChatAgent
from models import ProductOffer, ComparisonResult

# Page configuration
st.set_page_config(
    page_title=APP_TITLE,
    page_icon="🛍️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .chat-message {
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
        border-left: 4px solid;
    }
    .user-message {
        background-color: #e3f2fd;
        border-left-color: #2196f3;
    }
    .assistant-message {
        background-color: #f3e5f5;
        border-left-color: #9c27b0;
    }
    .product-card {
        border: 1px solid #ddd;
        border-radius: 0.5rem;
        padding: 1rem;
        margin: 0.5rem 0;
        background-color: #fafafa;
    }
    .best-offer {
        border-color: #4caf50;
        background-color: #e8f5e8;
        border-width: 2px;
    }
    .price-highlight {
        font-size: 1.2rem;
        font-weight: bold;
        color: #4caf50;
    }
    .source-badge {
        background-color: #ff9800;
        color: white;
        padding: 0.2rem 0.5rem;
        border-radius: 0.3rem;
        font-size: 0.8rem;
    }
</style>
""", unsafe_allow_html=True)

def initialize_session_state():
    """Initialize session state variables"""
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    if 'current_thread_id' not in st.session_state:
        st.session_state.current_thread_id = str(uuid.uuid4())
    if 'agent' not in st.session_state:
        st.session_state.agent = ProductChatAgent()

def display_product_offer(offer: ProductOffer, is_best: bool = False):
    """Display a product offer in a card format"""
    card_class = "product-card best-offer" if is_best else "product-card"
    
    st.markdown(f"""
    <div class="{card_class}">
        <h4>{offer.title}</h4>
        {f'<p class="price-highlight">💰 {offer.price}</p>' if offer.price else ''}
        <p><span class="source-badge">🏪 {offer.source}</span></p>
        {f'<p>{offer.description[:150]}...</p>' if offer.description else ''}
        <p><a href="{offer.url}" target="_blank">🔗 View Product</a></p>
    </div>
    """, unsafe_allow_html=True)

def display_comparison_result(comparison_result: ComparisonResult):
    """Display comparison results"""
    if not comparison_result:
        return
    
    st.markdown("### 🏆 Best Offer Analysis")
    
    # Display best offer
    st.markdown("**Best Offer:**")
    display_product_offer(comparison_result.best_offer, is_best=True)
    
    # Display reasoning
    st.markdown(f"**Why this is the best:** {comparison_result.reasoning}")
    
    # Display all offers
    st.markdown("### 📊 All Offers Found")
    for offer in comparison_result.all_offers:
        display_product_offer(offer, is_best=(offer == comparison_result.best_offer))
    
    # Display metrics if available
    if comparison_result.comparison_metrics:
        st.markdown("### 📈 Comparison Metrics")
        metrics = comparison_result.comparison_metrics
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Offers", metrics.get("total_offers", 0))
        with col2:
            if "source_diversity" in metrics:
                st.metric("Unique Sources", metrics["source_diversity"].get("unique_sources", 0))
        with col3:
            if "price_range" in metrics and metrics["price_range"]:
                st.metric("Price Range", f"${metrics['price_range']['min']:.2f} - ${metrics['price_range']['max']:.2f}")

def display_chat_message(role: str, content: str, citations: list = None):
    """Display a chat message with proper styling"""
    message_class = "user-message" if role == "user" else "assistant-message"
    
    st.markdown(f"""
    <div class="chat-message {message_class}">
        <strong>{role.capitalize()}:</strong> {content}
    </div>
    """, unsafe_allow_html=True)
    
    # Display citations if available
    if citations:
        st.markdown("**Sources:**")
        for citation in citations:
            if citation.startswith('http'):
                st.markdown(f"- [{citation}]({citation})")
            else:
                st.markdown(f"- {citation}")

def main():
    """Main application function"""
    # Initialize session state
    initialize_session_state()
    
    # Header
    st.markdown(f'<h1 class="main-header">{APP_TITLE}</h1>', unsafe_allow_html=True)
    st.markdown(APP_DESCRIPTION)
    
    # Sidebar
    with st.sidebar:
        st.markdown("### 🎯 Quick Actions")
        
        # New conversation button
        if st.button("🆕 New Conversation"):
            st.session_state.current_thread_id = str(uuid.uuid4())
            st.session_state.chat_history = []
            st.rerun()
        
        # Clear history button
        if st.button("🗑️ Clear History"):
            st.session_state.agent.clear_thread(st.session_state.current_thread_id)
            st.session_state.chat_history = []
            st.rerun()
        
        st.markdown("---")
        
        # Example queries
        st.markdown("### 💡 Example Queries")
        example_queries = [
            "Find the best laptop under $1000",
            "Compare iPhone prices",
            "Look for deals on wireless headphones",
            "What's the best gaming mouse?"
        ]
        
        for query in example_queries:
            if st.button(query, key=f"example_{query}"):
                st.session_state.user_input = query
                st.rerun()
        
        st.markdown("---")
        
        # Thread ID display
        st.markdown("### 🔗 Current Session")
        st.code(st.session_state.current_thread_id[:8] + "...")
        
        # API status
        st.markdown("### 🔑 API Status")
        # Check if OpenAI API key is configured from environment
        from config import OPENAI_API_KEY
        if OPENAI_API_KEY:
            st.success("✅ OpenAI API Connected")
        else:
            st.error("❌ OpenAI API Key Missing")
        
        # Check if Tavily API key is configured from environment
        from config import TAVILY_API_KEY
        if TAVILY_API_KEY:
            st.success("✅ Tavily API Connected")
        else:
            st.warning("⚠️ Tavily API Key Missing (using fallback)")

    # Main chat interface
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("### 💬 Chat Interface")
        
        # Chat input
        user_input = st.text_input(
            "Ask me to find products, compare prices, or just chat!",
            key="user_input",
            placeholder="e.g., 'Find the best laptop under $1000' or paste a product URL"
        )
        
        # Send button
        if st.button("🚀 Send", type="primary") and user_input:
            with st.spinner("🤔 Thinking..."):
                try:
                    # Get response from agent
                    response = st.session_state.agent.chat(
                        user_input, 
                        thread_id=st.session_state.current_thread_id
                    )
                    
                    # Add to chat history
                    st.session_state.chat_history.append({
                        "role": "user",
                        "content": user_input,
                        "timestamp": datetime.now().isoformat()
                    })
                    
                    st.session_state.chat_history.append({
                        "role": "assistant",
                        "content": response["response"],
                        "citations": response.get("citations", []),
                        "search_results": response.get("search_results", []),
                        "comparison_result": response.get("comparison_result"),
                        "timestamp": datetime.now().isoformat()
                    })
                    
                    # Clear input and rerun to refresh the page
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"Error: {str(e)}")
        
        # Display chat history
        st.markdown("### 📝 Conversation History")
        
        if not st.session_state.chat_history:
            st.info("👋 Start a conversation by asking me to find products or compare prices!")
        
        for i, message in enumerate(st.session_state.chat_history):
            display_chat_message(
                message["role"], 
                message["content"],
                message.get("citations", [])
            )
            
            # Display search results and comparison if available
            if message["role"] == "assistant":
                if message.get("search_results"):
                    st.markdown("**🔍 Products Found:**")
                    for offer in message["search_results"]:
                        display_product_offer(offer)
                
                if message.get("comparison_result"):
                    display_comparison_result(message["comparison_result"])
    
    with col2:
        st.markdown("### 📊 Current Session Info")
        
        # Display current thread info
        st.markdown(f"**Session ID:** {st.session_state.current_thread_id[:8]}...")
        st.markdown(f"**Messages:** {len(st.session_state.chat_history)}")
        
        # Recent activity
        if st.session_state.chat_history:
            st.markdown("**Recent Activity:**")
            recent_messages = st.session_state.chat_history[-5:]  # Last 5 messages
            for msg in recent_messages:
                timestamp = datetime.fromisoformat(msg["timestamp"]).strftime("%H:%M")
                st.markdown(f"• {msg['role'].capitalize()} ({timestamp})")
        
        # Quick stats
        if st.session_state.chat_history:
            user_messages = len([m for m in st.session_state.chat_history if m["role"] == "user"])
            assistant_messages = len([m for m in st.session_state.chat_history if m["role"] == "assistant"])
            
            st.markdown("**Message Count:**")
            col_a, col_b = st.columns(2)
            with col_a:
                st.metric("User", user_messages)
            with col_b:
                st.metric("Assistant", assistant_messages)

if __name__ == "__main__":
    main()
