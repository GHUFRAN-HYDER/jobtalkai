# JobTalk AI - Python Developer Recruiter Chat

A Streamlit-based AI recruiter chat application that simulates a recruitment conversation for a Python developer position in NYC. The application uses OpenAI's GPT-4 to handle natural conversations and rate negotiations.

## Features

- **Natural Conversation Flow**
  - Initial greeting and availability check
  - Professional rate negotiation
  - Context-aware responses
  - Humorous handling of unrealistic rates

- **Rate Handling Logic**
  - Below $50: Humorous/sarcastic response
  - $50-$100: Positive confirmation
  - $100-$150: Professional negotiation
  - Above $150: Humorous/sarcastic response

- **Smart Conversation Management**
  - Maintains conversation context
  - Tracks candidate information
  - Prevents duplicate questions
  - Professional conversation flow

- **Security & Moderation**
  - Content moderation for inappropriate language
  - Input validation
  - Rate limiting
  - Secure API key handling

## Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/jobtalkai.git
cd jobtalkai
```

2. Create and activate a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file in the root directory:
```
OPENAI_API_KEY=your_api_key_here
```

5. Run the application:
```bash
streamlit run streamlit_app.py
```

## Usage

1. Open the application in your browser (default: http://localhost:8501)
2. Start chatting with the AI recruiter
3. Follow the conversation flow:
   - Confirm availability
   - Share your expected hourly rate
   - Receive appropriate response based on rate

## Rate Categories

- **Below $50**: "Are you being sarcastic?" with humor
- **$50-$100**: Positive confirmation and acceptance
- **$100-$150**: Professional negotiation attempt
- **Above $150**: "Are you being sarcastic?" with humor about different ballparks

## Development

- Built with Streamlit
- Uses OpenAI's GPT-4 API
- Implements conversation memory
- Handles rate negotiations professionally

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- OpenAI for GPT-4 API
- Streamlit for the web framework
- Python community for various libraries 