from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

class ProductOffer(BaseModel):
    """Represents a product offer found during web search"""
    title: str
    price: Optional[str] = None
    url: str
    source: str
    description: Optional[str] = None
    rating: Optional[float] = None
    availability: Optional[str] = None

class ComparisonResult(BaseModel):
    """Result of comparing multiple product offers"""
    best_offer: ProductOffer
    all_offers: List[ProductOffer]
    comparison_metrics: Dict[str, Any]
    reasoning: str

class ChatMessage(BaseModel):
    """Represents a single chat message"""
    role: str  # "user" or "assistant"
    content: str
    timestamp: datetime = Field(default_factory=datetime.now)
    citations: Optional[List[str]] = None

class ChatContext(BaseModel):
    """Maintains rolling context of recent messages"""
    messages: List[ChatMessage] = Field(default_factory=list)
    max_turns: int = 3

    def add_message(self, message: ChatMessage):
        self.messages.append(message)
        if len(self.messages) > self.max_turns * 2:  # *2 because each turn has user + assistant
            self.messages = self.messages[-self.max_turns * 2:]

    def get_context_string(self) -> str:
        """Convert context to string for LLM input"""
        context = []
        for msg in self.messages:
            context.append(f"{msg.role.capitalize()}: {msg.content}")
        return "\n".join(context)

class ActionClassification(BaseModel):
    """Classification of user input action type"""
    action_type: str = Field(description="The type of action to perform based on user input")
    reasoning: str = Field(description="Brief explanation of why this action was chosen")
