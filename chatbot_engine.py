"""
Chatbot Engine Module
Core RAG engine for the car chatbot using local embeddings and LLM.
"""

import chromadb
from sentence_transformers import SentenceTransformer
from typing import Dict, List, Any, Optional
import os

# Optional langchain import for Ollama support
try:
    from langchain_community.llms import Ollama
    HAS_LANGCHAIN = True
except ImportError:
    HAS_LANGCHAIN = False
    Ollama = None


class LocalEmbeddings:
    """Local embeddings using Sentence Transformers"""
    
    def __init__(self, model_name: str = 'all-MiniLM-L6-v2'):
        """
        Initialize local embedding model
        
        Args:
            model_name: Name of the sentence transformer model
        """
        self.model = SentenceTransformer(model_name)
        print(f"✅ Loaded embedding model: {model_name}")
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        Embed multiple documents
        
        Args:
            texts: List of text strings to embed
            
        Returns:
            List of embedding vectors
        """
        return self.model.encode(texts).tolist()
    
    def embed_query(self, text: str) -> List[float]:
        """
        Embed a single query
        
        Args:
            text: Query string to embed
            
        Returns:
            Embedding vector
        """
        return self.model.encode([text])[0].tolist()


class CarChatbotEngine:
    """RAG-based car chatbot engine with local components"""
    
    def __init__(
        self,
        chroma_db_path: str = "data/chroma_db",
        embedding_model: str = 'all-MiniLM-L6-v2',
        ollama_model: str = 'llama3',
        use_ollama: bool = False
    ):
        """
        Initialize the chatbot engine
        
        Args:
            chroma_db_path: Path to ChromaDB vector store
            embedding_model: Name of sentence transformer model
            ollama_model: Name of Ollama model to use
            use_ollama: Whether to use Ollama (fallback to simple responses if False)
        """
        self.chroma_db_path = chroma_db_path
        self.embedding_model = embedding_model
        self.ollama_model = ollama_model
        self.use_ollama = use_ollama
        
        # Initialize components
        self.embeddings = LocalEmbeddings(embedding_model)
        self.llm = None
        self.client = None
        self.collection = None
        
        # Initialize vector store and LLM
        self._initialize_vectorstore()
        self._initialize_llm()
        self._setup_system_prompt()
    
    def _initialize_vectorstore(self):
        """Initialize ChromaDB vector store"""
        print("📂 Loading vector database...")
        
        if not os.path.exists(self.chroma_db_path):
            raise FileNotFoundError(
                f"Vector database not found at {self.chroma_db_path}. "
                "Please run the ingestion script first."
            )
        
        self.client = chromadb.PersistentClient(path=self.chroma_db_path)
        self.collection = self.client.get_collection(name="cars")
        print("✅ Vector database loaded successfully")
    
    def _initialize_llm(self):
        """Initialize local LLM (Ollama)"""
        if self.use_ollama and HAS_LANGCHAIN:
            try:
                self.llm = Ollama(model=self.ollama_model)
                print(f"✅ Using Ollama ({self.ollama_model}) for LLM")
            except Exception as e:
                print(f"⚠️ Ollama not available: {e}")
                print("   Falling back to simple response mode")
                self.llm = None
        else:
            if not HAS_LANGCHAIN:
                print("⚠️ Langchain not installed, using simple response mode")
            else:
                print("⚠️ Ollama disabled, using simple response mode")
            self.llm = None
    
    def _setup_system_prompt(self):
        """Setup the system prompt for the LLM"""
        self.system_prompt = """You are an expert automotive assistant with deep knowledge of car specifications and performance. 
Answer the user's question using ONLY the provided car datasheet information. 

Context from car datasheet:
{context}

User Question: {question}

Instructions:
- Provide accurate, specific information about car models, specifications, and performance
- Cite exact figures from the datasheet (horsepower, speed, acceleration, price, etc.)
- If comparing cars, be specific about the differences
- If the information is not available in the context, clearly state that
- Maintain a professional, enthusiastic tone like a car expert
- Format technical specifications clearly
- When mentioning a car, include its key specs for context

Answer:"""
    
    def query(self, question: str, n_results: int = 5) -> Dict[str, Any]:
        """
        Query the RAG pipeline
        
        Args:
            question: User's question
            n_results: Number of relevant documents to retrieve
            
        Returns:
            Dictionary containing answer and source documents
        """
        try:
            # Check if this is a comparison query with specific brands
            question_lower = question.lower()
            is_comparison = any(word in question_lower for word in ['compare', 'vs', 'versus', 'difference'])
            
            # Extract brand names from comparison query
            brands = self._extract_brands(question_lower)
            
            if is_comparison and len(brands) >= 2:
                # Use metadata filters to get cars from both brands
                results = self._query_by_brands(brands, n_results)
            else:
                # Generate embedding for query
                query_embedding = self.embeddings.embed_query(question)
                
                # Query ChromaDB
                results = self.collection.query(
                    query_embeddings=[query_embedding],
                    n_results=n_results
                )
            
            # Apply filtering before generating response
            filtered_results = self._apply_filters(results, question)
            
            # Format context
            context = "\n\n".join(filtered_results['documents'][0])
            
            # Generate response
            if self.llm:
                # Use LLM for response generation
                prompt = self.system_prompt.format(context=context, question=question)
                answer = self.llm.invoke(prompt)
            else:
                # Simple fallback response
                answer = self._generate_simple_response(filtered_results, question)
            
            # Format source documents from FILTERED results
            source_documents = []
            metadatas = filtered_results['metadatas'][0] if isinstance(filtered_results['metadatas'], list) else filtered_results['metadatas']
            for i, (doc, metadata) in enumerate(zip(filtered_results['documents'][0], metadatas)):
                source_documents.append({
                    "page_content": doc,
                    "metadata": metadata
                })
            
            return {
                "answer": answer,
                "source_documents": source_documents,
                "num_results": len(filtered_results['documents'][0])
            }
            
        except Exception as e:
            return {
                "answer": f"I encountered an error: {str(e)}",
                "source_documents": [],
                "num_results": 0
            }
    
    def _apply_filters(self, results: Dict, question: str) -> Dict:
        """Apply filters to query results based on question type"""
        question_lower = question.lower()
        is_sports_car = 'sports car' in question_lower or 'sports cars' in question_lower
        is_electric = 'electric' in question_lower or 'ev' in question_lower
        
        metadatas = results['metadatas'][0] if isinstance(results['metadatas'], list) else results['metadatas']
        documents = results['documents'][0]
        
        # Extract price limit if specified (e.g., "under $50k")
        price_limit = None
        if 'under' in question_lower or 'below' in question_lower or 'less than' in question_lower:
            import re
            price_match = re.search(r'\$?(\d+)[kK]?', question_lower)
            if price_match:
                price_limit = self._extract_number(price_match.group(1)) * 1000
                print(f"🔍 Price limit extracted: ${price_limit}")
        
        # Filter results based on query type
        filtered_docs = []
        filtered_metas = []
        
        print(f"🔍 Filtering {len(documents)} cars - Electric: {is_electric}, Price Limit: ${price_limit}")
        
        for doc, meta in zip(documents, metadatas):
            include = True
            
            # Filter for sports cars
            if is_sports_car:
                hp = self._extract_number(meta.get('horsepower', '0'))
                accel = self._extract_number(meta.get('acceleration', '999'))
                if not (hp > 300 or accel < 4.5):
                    include = False
            
            # Filter for electric cars
            if is_electric:
                fuel = meta.get('fuel_type', '').lower()
                if 'electric' not in fuel:
                    include = False
                    print(f"❌ Filtered out: {meta.get('company')} {meta.get('model')} - Fuel: {fuel}")
            
            # Filter by price limit
            if price_limit:
                price = self._extract_price(meta.get('price', '999999999'))
                if price > price_limit:
                    include = False
                    print(f"❌ Filtered out: {meta.get('company')} {meta.get('model')} - Price: ${price} > ${price_limit}")
            
            if include:
                filtered_docs.append(doc)
                filtered_metas.append(meta)
                print(f"✅ Included: {meta.get('company')} {meta.get('model')} - Price: ${meta.get('price')}")
        
        # Return filtered results in same format as original
        return {
            'documents': [filtered_docs],
            'metadatas': [filtered_metas],
            'distances': results['distances']
        }
    
    def _extract_brands(self, question: str) -> List[str]:
        """Extract brand names from comparison query"""
        # Common car brands to look for
        brands = [
            'ferrari', 'porsche', 'lamborghini', 'mclaren', 'bugatti',
            'bmw', 'mercedes', 'audi', 'tesla', 'ford', 'chevrolet',
            'toyota', 'honda', 'nissan', 'hyundai', 'kia', 'volkswagen',
            'jaguar', 'land rover', 'maserati', 'aston martin', 'bentley',
            'rolls royce', 'lexus', 'infiniti', 'acura', 'genesis'
        ]
        
        found_brands = []
        for brand in brands:
            if brand in question:
                found_brands.append(brand)
        
        return found_brands
    
    def _query_by_brands(self, brands: List[str], n_results: int) -> Dict:
        """Query ChromaDB using brand filters"""
        all_results = {'documents': [[]], 'metadatas': [[]], 'distances': [[]]}
        
        for brand in brands:
            # Use semantic search for each brand separately
            query_embedding = self.embeddings.embed_query(brand)
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results
            )
            
            # Filter results to only include cars from the specified brand
            filtered_docs = []
            filtered_metas = []
            filtered_dists = []
            
            for i, (doc, metadata, dist) in enumerate(zip(results['documents'][0], results['metadatas'][0], results['distances'][0])):
                company = metadata.get('company', '').lower()
                if brand.lower() in company:
                    filtered_docs.append(doc)
                    filtered_metas.append(metadata)
                    filtered_dists.append(dist)
            
            # Add filtered results to all_results
            for doc, meta, dist in zip(filtered_docs, filtered_metas, filtered_dists):
                all_results['documents'][0].append(doc)
                all_results['metadatas'][0].append(meta)
                all_results['distances'][0].append(dist)
        
        return all_results
    
    def _generate_simple_response(self, results: Dict, question: str) -> str:
        """
        Generate a simple response without LLM (fallback mode)
        
        Args:
            results: Query results from ChromaDB (already filtered)
            question: User's question
            
        Returns:
            Simple text response
        """
        question_lower = question.lower()
        is_comparison = any(word in question_lower for word in ['compare', 'vs', 'versus', 'difference'])
        is_sports_car = 'sports car' in question_lower or 'sports cars' in question_lower
        is_electric = 'electric' in question_lower or 'ev' in question_lower
        
        metadatas = results['metadatas'][0] if isinstance(results['metadatas'], list) else results['metadatas']
        documents = results['documents'][0]
        num_cars = len(documents)
        
        # Update the count in the response to reflect filtered results
        if num_cars == 0:
            return f"I searched the database but found no cars matching your criteria. Try adjusting your filters or search terms."
        
        if is_comparison and num_cars > 1:
            # Generate comparison response
            answer = f"## Comparison of {num_cars} Cars\n\n"
            
            # Create comparison table
            answer += "| Car | HP | Torque | Top Speed | 0-100 | Price |\n"
            answer += "|-----|-----|--------|-----------|-------|-------|\n"
            
            for i, (doc, metadata) in enumerate(zip(documents, metadatas)):
                name = f"{metadata.get('company', 'N/A')} {metadata.get('model', 'N/A')}"
                hp = metadata.get('horsepower', 'N/A')
                torque = metadata.get('torque', 'N/A')
                speed = metadata.get('top_speed', 'N/A')
                accel = metadata.get('acceleration', 'N/A')
                price = metadata.get('price', 'N/A')
                answer += f"| {name} | {hp} | {torque} | {speed} | {accel} | {price} |\n"
            
            # Add quick analysis
            answer += "\n### Quick Analysis:\n"
            
            # Find fastest
            fastest = max(metadatas[:3], key=lambda x: self._extract_speed(x.get('top_speed', '0')))
            answer += f"- **Fastest**: {fastest.get('company', 'N/A')} {fastest.get('model', 'N/A')} ({fastest.get('top_speed', 'N/A')})\n"
            
            # Find most powerful
            most_powerful = max(metadatas[:3], key=lambda x: self._extract_number(x.get('horsepower', '0')))
            answer += f"- **Most Powerful**: {most_powerful.get('company', 'N/A')} {most_powerful.get('model', 'N/A')} ({most_powerful.get('horsepower', 'N/A')})\n"
            
            # Find cheapest
            cheapest = min(metadatas[:3], key=lambda x: self._extract_price(x.get('price', '999999999')))
            answer += f"- **Most Affordable**: {cheapest.get('company', 'N/A')} {cheapest.get('model', 'N/A')} ({cheapest.get('price', 'N/A')})\n"
            
            
        else:
            # Simple listing response - show ALL cars found
            if is_sports_car:
                answer = f"Based on the car database, I found {num_cars} sports cars. Here are the top performers:\n\n"
            elif is_electric:
                answer = f"Based on the car database, I found {num_cars} electric cars. Here they are:\n\n"
            else:
                answer = f"Based on the car database, I found {num_cars} relevant cars. Here's what I found:\n\n"
            
            # Show ALL cars, not just first 3
            for i, doc in enumerate(documents):
                answer += f"{i+1}. {doc}\n\n"
        
        return answer
    
    def _extract_number(self, value: str) -> float:
        """Extract numeric value from string"""
        try:
            # Remove non-numeric characters except decimal point
            cleaned = ''.join(c for c in str(value) if c.isdigit() or c == '.')
            return float(cleaned) if cleaned else 0.0
        except:
            return 0.0
    
    def _extract_speed(self, value: str) -> float:
        """Extract speed value (handles km/h, mph)"""
        try:
            cleaned = ''.join(c for c in str(value) if c.isdigit() or c == '.')
            return float(cleaned) if cleaned else 0.0
        except:
            return 0.0
    
    def _extract_price(self, value: str) -> float:
        """Extract price value (handles $, commas)"""
        try:
            cleaned = ''.join(c for c in str(value) if c.isdigit() or c == '.')
            return float(cleaned) if cleaned else 999999999.0
        except:
            return 999999999.0
    
    def query_with_filters(
        self,
        question: str,
        filters: Dict[str, Any],
        n_results: int = 5
    ) -> Dict[str, Any]:
        """
        Query with metadata filters for structured queries
        
        Args:
            question: User's question
            filters: Metadata filters (e.g., {"company": "Ferrari"})
            n_results: Number of relevant documents to retrieve
            
        Returns:
            Dictionary containing answer and source documents
        """
        try:
            # Generate embedding for query
            query_embedding = self.embeddings.embed_query(question)
            
            # Query ChromaDB with filters
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                where=filters
            )
            
            # Format context and response
            context = "\n\n".join(results['documents'][0])
            
            if self.llm:
                prompt = self.system_prompt.format(context=context, question=question)
                answer = self.llm.invoke(prompt)
            else:
                answer = self._generate_simple_response(results, question)
            
            # Format source documents
            source_documents = []
            for i, (doc, metadata) in enumerate(zip(results['documents'][0], results['metadatas'][0])):
                source_documents.append({
                    "page_content": doc,
                    "metadata": metadata
                })
            
            return {
                "answer": answer,
                "source_documents": source_documents,
                "num_results": len(results['documents'][0])
            }
            
        except Exception as e:
            return {
                "answer": f"I encountered an error: {str(e)}",
                "source_documents": [],
                "num_results": 0
            }
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the vector database
        
        Returns:
            Dictionary containing database statistics
        """
        try:
            count = self.collection.count()
            return {
                "total_cars": count,
                "embedding_model": self.embedding_model,
                "llm_model": self.ollama_model if self.llm else "simple mode",
                "vector_db_path": self.chroma_db_path
            }
        except Exception as e:
            return {
                "error": str(e)
            }


# Singleton instance
_chatbot_engine = None


def get_chatbot_engine(
    chroma_db_path: str = "data/chroma_db",
    embedding_model: str = 'all-MiniLM-L6-v2',
    ollama_model: str = 'llama3',
    use_ollama: bool = True
) -> CarChatbotEngine:
    """
    Get or create the chatbot engine singleton
    
    Args:
        chroma_db_path: Path to ChromaDB vector store
        embedding_model: Name of sentence transformer model
        ollama_model: Name of Ollama model to use
        use_ollama: Whether to use Ollama
        
    Returns:
        CarChatbotEngine instance
    """
    global _chatbot_engine
    if _chatbot_engine is None:
        _chatbot_engine = CarChatbotEngine(
            chroma_db_path=chroma_db_path,
            embedding_model=embedding_model,
            ollama_model=ollama_model,
            use_ollama=use_ollama
        )
    return _chatbot_engine


if __name__ == "__main__":
    # Test the chatbot engine
    print("🚗 Testing Car Chatbot Engine")
    print("=" * 50)
    
    try:
        engine = get_chatbot_engine()
        stats = engine.get_stats()
        
        print("\n📊 Engine Statistics:")
        for key, value in stats.items():
            print(f"  {key}: {value}")
        
        print("\n🔍 Testing Query:")
        result = engine.query("What's the fastest Ferrari?")
        print(f"\nAnswer: {result['answer']}")
        print(f"\nSources found: {result['num_results']}")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("Make sure to run the ingestion script first:")
        print("  cd backend && python ingest.py")
