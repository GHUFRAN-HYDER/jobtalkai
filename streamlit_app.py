import streamlit as st
import re
import time
import logging
import openai
from openai import OpenAI
from typing import Dict, Any, List, Optional, Tuple
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Application settings
APP_NAME = "Recruiter AI Chat"
APP_VERSION = "1.0.0"
APP_DESCRIPTION = "An interactive AI chatbot that simulates a recruitment conversation"

# OpenAI settings
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
if not OPENAI_API_KEY:
    st.error("OpenAI API key not found. Please add it to your .env file as OPENAI_API_KEY=your-key-here")
    st.stop()

# Initialize OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)

# Content moderation settings
CONTENT_MODERATION_ENABLED = True
HARMFUL_PATTERNS: List[str] = [
    r'\b(hate|kill|death threat|bomb|attack|racism|sexism)\b',
    r'\b(stupid|idiot|moron|dumb)\b',
    r'\b(obscenity|profanity)\b',
]
MAX_MESSAGE_LENGTH = 1000
MAX_FRONTEND_MESSAGE_LENGTH = 500

# Chat settings
INITIAL_GREETING = "Hi there, I have a Python developer position in New York City. Are you available?"

# Rate settings
MIN_RATE = 50
ACCEPTABLE_RATE = 100
MAX_RATE = 150

# Set page config
st.set_page_config(
    page_title=APP_NAME,
    page_icon="💼",
    layout="centered"
)

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []

if "error" not in st.session_state:
    st.session_state.error = None

if "candidate_info" not in st.session_state:
    st.session_state.candidate_info = {
        "shared_name": False,
        "shared_skills": False,
        "shared_experience": False,
        "shared_rate": None
    }

# Input validation
def validate_user_input(text: str) -> Tuple[bool, Optional[str]]:
    # Check for empty input
    if not text or text.isspace():
        return False, "Your message cannot be empty."
    
    # Check for input length
    if len(text) > MAX_FRONTEND_MESSAGE_LENGTH:
        return False, f"Your message is too long. Please limit to {MAX_FRONTEND_MESSAGE_LENGTH} characters."
    
    # Check for potentially harmful content (simple check)
    if CONTENT_MODERATION_ENABLED:
        for pattern in HARMFUL_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                return False, "Your message contains inappropriate content."
    
    return True, None

# Content moderation
def moderate_content(text: str) -> Optional[str]:
    if not CONTENT_MODERATION_ENABLED:
        return None
        
    harmful_regex = re.compile('|'.join(HARMFUL_PATTERNS), re.IGNORECASE)
    if harmful_regex.search(text):
        match = harmful_regex.search(text)
        if match:
            return f"Content contains potentially harmful text: '{match.group()}'"
    return None

def get_rate_category(rate: float) -> str:
    """Determine which category a rate falls into based on config."""
    if rate < MIN_RATE:
        return "too_low"
    elif rate > MAX_RATE:
        return "too_high"
    elif MIN_RATE <= rate <= ACCEPTABLE_RATE:
        return "acceptable"
    else:  # ACCEPTABLE_RATE < rate <= MAX_RATE
        return "negotiable"

def extract_rate(text: str) -> Optional[float]:
    """Extract hourly rate from text."""
    # First try to find currency patterns like $50 or 50 USD
    currency_pattern = r'[$€£¥](\d+(?:\.\d+)?)|(\d+(?:\.\d+)?)\s?(?:usd|dollars|eur|euro|gbp|pounds|jpy|yen)'
    currency_matches = re.findall(currency_pattern, text, re.IGNORECASE)
    
    if currency_matches:
        # Extract the first match
        for match in currency_matches:
            if match[0]:  # Currency symbol first
                return float(match[0])
            elif match[1]:  # Currency name after
                return float(match[1])
    
    # If no currency pattern found, try to find any number
    number_pattern = r'\b(\d+(?:\.\d+)?)\b'
    number_match = re.search(number_pattern, text)
    if number_match:
        return float(number_match.group(1))
    
    return None

def update_candidate_info(user_message: str):
    """Update shared candidate information based on message content"""
    # Extract rate if provided
    rate = extract_rate(user_message)
    if rate is not None:
        st.session_state.candidate_info["shared_rate"] = rate
    
    # Check for name sharing
    if "my name is" in user_message.lower() or "i am" in user_message.lower() or "i'm" in user_message.lower():
        st.session_state.candidate_info["shared_name"] = True
    
    # Check for skills or experience
    skills_keywords = ["python", "javascript", "react", "angular", "java", "c#", "sql", "nosql", "node", 
                      "experience", "years", "expert", "junior", "senior", "developer", "engineer", "programmer"]
    
    for keyword in skills_keywords:
        if keyword.lower() in user_message.lower():
            st.session_state.candidate_info["shared_skills"] = True
            break

def generate_system_message() -> str:
    """Generate system message based on candidate info without using states"""
    candidate_info = st.session_state.candidate_info
    
    system_content = f"""You are an AI recruiter for a Python developer position in New York City.
    Your goal is to have a professional conversation with the candidate and find someone who can work within a budget of $100 per hour, but NEVER mention this specific amount.
    
    Information the candidate has shared:
    - Name: {"Yes" if candidate_info["shared_name"] else "No"}
    - Skills/Experience: {"Yes" if candidate_info["shared_skills"] else "No"}
    - Rate: {candidate_info["shared_rate"] if candidate_info["shared_rate"] is not None else "Not shared"}
    
    IMPORTANT: ONLY reference information that the candidate has explicitly shared above. DO NOT make assumptions about their background, skills, or experience unless they are listed as shared.
    
    Conversation Flow:
    1. First, ask if they're available for a Python developer position in NYC.
    2. If they say yes, ask for their expected hourly rate.
    3. Based on their rate:
       - If between $50-$100: Thank them, confirm the rate works, and end the conversation positively.
       - If between $100-$150: Politely negotiate to bring the rate down, without revealing your maximum budget.
       - If below $50: Respond with "Are you sarcastic?" and make a joke like are you pulling my leg or whatever best humor you can do
       - If above $150: Respond with "Haha, are you being sarcastic? That's quite a number! While I appreciate your confidence, I think we might be in different ballparks here. Best of luck with your search!"
    
    Rate guidelines:
    - NEVER mention the exact budget of $100/hour
    - For rates between $100-$150, negotiate with phrases like "something more competitive" or "a rate that better aligns with our budget"
    - If the candidate asks what rate you can offer, NEVER give a specific number
    - Don't ask about rate multiple times - if they've already shared it, move the conversation forward
    - When a candidate agrees to negotiate, suggest a lower rate without specifying an exact number keep neotiating till candidate agrees for 100$ or between 50 to 100$
    - For rates above $150: ALWAYS respond with "Are you being sarcastic?" and humor relevant to that and end the conversation
    - For rates below $50: ALWAYS respond with "Are you being sarcastic?" and humor as he was making joke out of you and end the conversation
    
    Keep your responses professional, concise, and focused on the recruitment process. Never make up information about the candidate.
    """
    
    return system_content

def generate_llm_response(user_message: str) -> Dict[str, Any]:
    """Generate response using OpenAI API without state management."""
    # Update candidate info based on message
    update_candidate_info(user_message)
    
    # Generate system message
    system_content = generate_system_message()
    
    # Prepare conversation history
    messages = [
        {"role": "system", "content": system_content}
    ]
    
    # Add relevant conversation history
    for msg in st.session_state.messages[-6:]:  # Last 6 messages for context
        messages.append({"role": msg["role"], "content": msg["content"]})
    
    # Add current user message
    messages.append({"role": "user", "content": user_message})
    
    try:
        # Call OpenAI API
        response = client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=messages,
            max_tokens=250,
            temperature=0.7
        )
        
        # Extract response
        ai_message = response.choices[0].message.content.strip()
        
        return {
            "message": ai_message
        }
    
    except Exception as e:
        logger.error(f"Error calling OpenAI API: {str(e)}")
        return {
            "error": f"Sorry, I encountered an error while processing your message. Please try again."
        }

# Process user message
def process_message(user_message: str) -> Dict[str, Any]:
    # Validate input
    is_valid, error_msg = validate_user_input(user_message)
    if not is_valid:
        return {"error": error_msg}
    
    # Check for content moderation
    violation = moderate_content(user_message)
    if violation:
        return {"error": violation}
    
    # Generate response using LLM without state management
    return generate_llm_response(user_message)

# Page header
st.title(APP_NAME)
st.markdown("Chat with our AI recruiter about the Python developer position in NYC")

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

# If no messages, initiate the conversation
if not st.session_state.messages:
    with st.chat_message("assistant"):
        st.write(INITIAL_GREETING)
    st.session_state.messages.append({"role": "assistant", "content": INITIAL_GREETING})

# Chat input
if user_input := st.chat_input("Type your message here..."):
    # Display user message
    with st.chat_message("user"):
        st.write(user_input)
    
    # Add to conversation history
    st.session_state.messages.append({"role": "user", "content": user_input})
    
    # Process message
    with st.spinner("Thinking..."):
        response = process_message(user_input)
    
    if "error" in response:
        st.error(response["error"])
    else:
        # Display assistant response
        with st.chat_message("assistant"):
            st.write(response["message"])
        
        # Add to conversation history
        st.session_state.messages.append({"role": "assistant", "content": response["message"]})

# Add a sidebar with info
with st.sidebar:
    st.header("About")
    st.markdown("""
    This is an AI recruiter chat application that simulates a recruitment conversation for a Python developer position in NYC.
    
    """)
    
    if st.button("Reset Conversation"):
        st.session_state.messages = []
        st.session_state.error = None
        st.session_state.candidate_info = {
            "shared_name": False,
            "shared_skills": False,
            "shared_experience": False,
            "shared_rate": None
        }
        st.rerun()
    
    # Display environment info
    st.subheader("Environment")
    st.info(f"Running in development mode")
    st.caption(f"Version: {APP_VERSION}")
    
    
    st.subheader("Usage Guidelines")
    st.markdown("""
    - Keep messages professional and relevant
    - Do not share personal identifiable information
    - Avoid offensive language or content
    - For demonstration purposes only
    """)
    
