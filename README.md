# 🚗 AI Car Chatbot - Local RAG-Powered Automotive Assistant

An intelligent car assistant powered by Retrieval-Augmented Generation (RAG) that answers questions about 1,218+ car specifications with 100% factual accuracy from the datasheet. **100% local and open-source - no external APIs required.**

## ✨ Features

- **RAG Architecture**: Hybrid semantic search + structured filtering for accurate car information
- **1,218+ Cars**: Comprehensive database with detailed specifications
- **ChatGPT-Style UI**: Modern, dark-themed conversational interface
- **Real-Time Responses**: Fast API backend with streaming capabilities
- **Source Citations**: View the exact car specifications used for each answer
- **Quick Queries**: Pre-built questions for instant car information
- **Metadata Filtering**: Filter by company, price, fuel type, etc.
- **100% Local**: No external API keys required, runs entirely on your machine

## 🏗️ Architecture

### Tech Stack
- **Backend**: FastAPI with LangChain RAG pipeline
- **Vector Database**: ChromaDB for semantic search (local)
- **Embeddings**: Sentence Transformers with all-MiniLM-L6-v2 (local)
- **LLM**: Ollama with Llama3 or Mistral (local) - can also use Hugging Face Transformers
- **Frontend**: Streamlit with custom CSS styling
- **Data**: CSV-based car specifications database

### RAG Pipeline
1. **Data Ingestion**: CSV → per-car documents with enriched metadata
2. **Embedding**: Sentence Transformers (all-MiniLM-L6-v2) for semantic search
3. **Retrieval**: Hybrid search (semantic + metadata filters)
4. **Context**: Top 5 relevant cars → LLM prompt with system instructions
5. **Response**: Generation with car spec citations using local LLM

## 📋 Prerequisites

- Python 3.8 or higher
- Ollama (optional, for local LLM) OR sufficient RAM for Hugging Face models
- 4GB+ RAM recommended

## 🚀 Installation

1. **Install dependencies**
```bash
pip install -r requirements.txt
```

2. **Set up environment variables**
```bash
cp .env.example .env
# Edit .env if needed (default settings work for local setup)
```

3. **Install Ollama (optional but recommended for local LLM)**
```bash
# Download from https://ollama.ai
# Then pull a model:
ollama pull llama3
# or
ollama pull mistral
```

4. **Ingest the car data**
```bash
cd backend
python ingest.py
```

5. **Start the backend API**
```bash
python main.py
```

6. **Start the frontend** (in a new terminal)
```bash
cd frontend
streamlit run app.py
```

7. **Or use the CLI interface** (alternative to web UI)
```bash
python main.py
```

## 🎯 Usage

### Getting Started

1. **Backend**: Run on http://localhost:8000
2. **Frontend**: Open http://localhost:8501 in your browser
3. **Start chatting**: Ask any question about cars

### Example Queries

- "What's the fastest Ferrari?"
- "Show me electric cars under $50k"
- "Compare Porsche vs Ferrari performance"
- "Best sports cars for 2025"
- "Most fuel-efficient SUVs"

### Features

- **Quick Queries**: Click pre-built questions in the sidebar
- **Chat History**: View conversation history
- **Source Citations**: Expand to see the exact car specifications
- **Clear Chat**: Reset the conversation
- **Database Stats**: View total cars and model information

## 📁 Project Structure

```
ChatBot/
├── backend/
│   ├── main.py              # FastAPI backend
│   ├── rag_pipeline.py      # LangChain RAG implementation
│   └── ingest.py            # Data ingestion script
├── frontend/
│   └── app.py               # Streamlit chat UI
├── data/
│   └── chroma_db/           # Vector database (auto-generated)
├── Cars Datasets 2025.csv   # Car specifications database
├── requirements.txt         # Python dependencies
├── .env.example            # Environment variables template
└── README.md               # This file
```

## 🔧 How It Works

### Data Processing
- Each car becomes a document with natural language description
- Metadata includes all specifications for filtering
- Stored in ChromaDB with semantic embeddings

### Query Processing
1. User asks a question
2. System retrieves top 5 relevant cars using semantic search
3. LLM generates answer using only retrieved context
4. Response includes citations to source car specifications

### System Prompt
The LLM is instructed to:
- Use ONLY provided car datasheet information
- Cite specific car models and exact specifications
- Admit when information is not available
- Maintain professional, enthusiastic automotive expert tone

## 📊 Database Statistics

- **Total Cars**: 1,218
- **Companies**: 50+ manufacturers
- **Specifications**: 11 fields per car
- **Embedding Model**: all-MiniLM-L6-v2 (Sentence Transformers)
- **LLM Model**: Llama3/Mistral via Ollama (local)

## 🎨 UI Features

- **Dark Theme**: ChatGPT-inspired modern design
- **Sidebar**: Quick queries, chat history, database stats
- **Message Bubbles**: Distinct user and AI styling
- **Source Cards**: Expandable citation cards
- **Responsive Design**: Works on all screen sizes
- **Streaming Text**: Real-time response generation

## 🔮 Future Enhancements

- [ ] Streaming responses in frontend
- [ ] Car comparison tables
- [ ] Image integration for car models
- [ ] Advanced filtering UI
- [ ] Export chat history
- [ ] Multi-language support

## 🐛 Troubleshooting

### Backend Issues
- **Connection Error**: Ensure backend is running on port 8000
- **Ollama Error**: Install Ollama from https://ollama.ai and pull a model (llama3 or mistral)
- **Vector DB Error**: Run `python backend/ingest.py` to rebuild database

### Frontend Issues
- **No Response**: Check backend connection and API status
- **Styling Issues**: Clear browser cache and reload
- **Slow Loading**: Check internet connection for API calls

## 📝 API Endpoints

### POST /api/chat
Main chat endpoint
```json
{
  "message": "What's the fastest Ferrari?",
  "filters": {
    "company": "Ferrari"
  }
}
```

### GET /api/stats
Database statistics
```json
{
  "total_cars": 1218,
  "embedding_model": "text-embedding-3-small",
  "llm_model": "gpt-4o"
}
```

### GET /health
Health check endpoint

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is open source and available under the MIT License.

## 🙏 Acknowledgments

- Car data from Kaggle Cars Datasets 2025
- Built with LangChain, ChromaDB, and OpenAI
- UI inspired by ChatGPT and Google Gemini
