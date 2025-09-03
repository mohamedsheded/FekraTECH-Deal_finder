# Deal Finder - AI Product Comparison Assistant

An intelligent Streamlit application that helps users find the best deals on products, compare prices across retailers, and get AI-powered shopping recommendations.

## 🚀 Features

- **AI-Powered Product Search**: Find products using natural language queries
- **Smart Price Comparison**: Automatically compare offers and identify the best deals
- **URL Product Extraction**: Extract product information from pasted URLs
- **Conversational Interface**: Chat naturally with the AI assistant
- **Memory Management**: Maintains conversation context across sessions
- **Beautiful UI**: Modern, responsive interface with product cards and metrics

## 🛠️ Technology Stack

- **Frontend**: Streamlit
- **AI/ML**: OpenAI GPT models, LangChain, LangGraph
- **Web Search**: Tavily Search API
- **Data Models**: Pydantic
- **Web Scraping**: BeautifulSoup4, Requests

## 📋 Prerequisites

- Python 3.8+
- OpenAI API key
- Tavily API key (optional, for enhanced search)

## 🚀 Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd deal-finder
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   ```bash
   # Copy the example environment file
   cp env_example.txt .env
   
   # Edit .env with your API keys
   OPENAI_API_KEY=your_openai_api_key_here
   TAVILY_API_KEY=your_tavily_api_key_here
   ```

4. **Run the application**
   ```bash
   streamlit run streamlit_app.py
   ```

## 🔑 API Keys Setup

### OpenAI API Key
1. Visit [OpenAI Platform](https://platform.openai.com/)
2. Create an account and get your API key
3. Add it to your `.env` file

### Tavily API Key (Optional)
1. Visit [Tavily](https://tavily.com/)
2. Sign up for a free account
3. Get your API key and add it to `.env`
4. Without this key, the app will use fallback search results

## 💡 Usage Examples

### Product Search
- "Find the best laptop under $1000"
- "Compare iPhone prices"
- "Look for deals on wireless headphones"
- "What's the best gaming mouse?"

### URL Analysis
- Paste any product URL to get detailed information
- The AI will extract product details and analyze the offer

### General Chat
- Ask questions about products
- Get shopping advice
- Discuss product features and comparisons

## 🏗️ Architecture

The application is built with a modular architecture:

```
deal-finder/
├── config.py              # Configuration and constants
├── models.py              # Data models and schemas
├── web_searcher.py        # Web search and URL extraction
├── offer_comparator.py    # Product offer comparison logic
├── product_agent.py       # Main AI agent with LangGraph
├── streamlit_app.py       # Streamlit user interface
├── requirements.txt       # Python dependencies
└── README.md             # This file
```

### Core Components

1. **WebSearcher**: Handles product search using Tavily API and fallback methods
2. **OfferComparator**: Analyzes and scores product offers to find the best deals
3. **ProductChatAgent**: Main AI agent using LangGraph for workflow management
4. **Streamlit Interface**: User-friendly web interface with chat and product display

## 🔄 Workflow

1. **Input Analysis**: AI classifies user input as product search, URL extraction, or general chat
2. **Product Search**: Searches web for relevant product offers
3. **Offer Comparison**: Scores and compares offers based on price, source credibility, and other factors
4. **Response Generation**: AI generates helpful, contextual responses with citations
5. **Memory Management**: Maintains conversation context for follow-up questions



## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

##  Acknowledgments

- OpenAI for providing the GPT models
- Tavily for web search capabilities
- Streamlit for the web framework
- LangChain and LangGraph communities


