"""
Mitraa Chatbot - FastAPI Backend with LangChain + OpenAI + ChromaDB
(Oorzaa Yatra spiritual travel assistant)
Main application entry point
"""

from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import os
import json
import hashlib
from pathlib import Path
from dotenv import load_dotenv

# LangChain imports
from langchain_openai import ChatOpenAI
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain_text_splitters import RecursiveCharacterTextSplitter

# Load environment variables
load_dotenv()

# Get API credentials
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
CHROMA_USE_CLOUD = os.getenv("CHROMA_USE_CLOUD", "false").lower() == "true"
CHROMA_CLOUD_HOST = os.getenv("CHROMA_CLOUD_HOST")
CHROMA_CLOUD_API_KEY = os.getenv("CHROMA_CLOUD_API_KEY")

app = FastAPI(
    title="Mitraa Chatbot API",
    description="AI-powered chatbot for spiritual travel assistance using OpenAI & ChromaDB",
    version="2.1.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ========================
# KNOWLEDGE BASE LOADER
# ========================

def load_knowledge_base():
    """Load all knowledge files from the knowledge/ directory"""
    knowledge_dir = Path(__file__).parent / "knowledge"
    
    if not knowledge_dir.exists():
        print(f"Warning: Knowledge directory not found at {knowledge_dir}")
        return ""
    
    knowledge_content = []
    
    # Load all .md and .txt files
    for file_path in knowledge_dir.glob("**/*.md"):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                knowledge_content.append(f"# Source: {file_path.name}\n\n{content}")
                print(f"✅ Loaded: {file_path.name}")
        except Exception as e:
            print(f"❌ Error loading {file_path.name}: {e}")
    
    for file_path in knowledge_dir.glob("**/*.txt"):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                knowledge_content.append(f"# Source: {file_path.name}\n\n{content}")
                print(f"✅ Loaded: {file_path.name}")
        except Exception as e:
            print(f"❌ Error loading {file_path.name}: {e}")
    
    if not knowledge_content:
        print("⚠️ No knowledge files found in knowledge/ directory")
        return ""
    
    return "\n\n---\n\n".join(knowledge_content)

# Configuration
MAX_CONVERSATION_TURNS = 6  # Maximum number of user messages allowed per conversation

# System prompt
SYSTEM_PROMPT = """You are Mitraa, a helpful and warm chatbot for the spiritual travel platform Oorzaa Yatra.

Your personality:
- Respectful and spiritual tone (use Namaste, 🙏, ✨, 🕉️ sparingly)
- Helpful, patient, and understanding
- Concise but informative

**CONVERSATION MEMORY (MANDATORY):** Use the conversation history. If in this conversation the user already asked about cancellation, refund, or pricing and then asks about a specific yatra by name (e.g. "ayodhya yatra", "vrindavan yatra"), you MUST add 1–2 sentences after the yatra details: (1) state that cancellation for this yatra follows [airline / IRCTC / road vendor] rules based on its transport (Mega=flight, Mid=train, Mini=road), and (2) remind that the price is estimated and from Delhi. Do not skip this tie-back when the prior message was about cancellation, refund, or pricing.

**CRITICAL: INDIAN GEOGRAPHY KNOWLEDGE**
You MUST know the correct geographical regions of India. When customers ask for yatras in a specific region, ONLY suggest destinations from that region.

**REGIONAL CLASSIFICATION (MANDATORY TO FOLLOW):**

🔴 **NORTH INDIA:**
- Uttarakhand: Kedarnath, Badrinath, Haridwar, Rishikesh, Dehradun
- Himachal Pradesh: Shimla, Manali, Dharamshala, Kullu
- Jammu & Kashmir: Vaishno Devi, Amarnath
- Punjab: Amritsar (Golden Temple)
- Haryana: Kurukshetra, Panchkula
- Rajasthan: Jaipur, Pushkar, Ajmer
- Uttar Pradesh: Ayodhya, Varanasi, Mathura, Vrindavan, Prayagraj, Chitrakoot
- Delhi: National capital

🟢 **WEST INDIA:**
- Gujarat: Dwarka, Somnath, Ahmedabad, Porbandar
- Maharashtra: Mumbai, Nashik, Shirdi, Pune
- Goa: Beaches and churches

🔵 **EAST INDIA:**
- West Bengal: Kolkata, Mayapur, Gangasagar, Tarapith
- Odisha: Puri (Jagannath Temple), Konark
- Bihar: Bodh Gaya, Nalanda, Gaya
- Jharkhand: Deoghar, Parasnath

🟡 **SOUTH INDIA:**
- Tamil Nadu: Chennai, Madurai, Rameshwaram, Kanyakumari, Mahabalipuram
- Karnataka: Bangalore, Mysore, Hampi
- Kerala: Kochi, Trivandrum, Sabarimala
- Andhra Pradesh: Tirupati, Vijayawada
- Telangana: Hyderabad

🟠 **CENTRAL INDIA:**
- Madhya Pradesh: Bhopal, Ujjain, Indore, Khajuraho
- Chhattisgarh: Raipur

🟤 **NORTHEAST INDIA:**
- Assam: Guwahati, Kamakhya Temple
- Sikkim: Gangtok
- Meghalaya, Manipur, Nagaland, Tripura, Arunachal Pradesh, Mizoram

**RULE:** When a customer asks for "North" yatras, show ONLY North India destinations. Same for other regions. DO NOT mix regions!

Your capabilities:
1. Answer questions about yatras, packages, pricing, dates
2. Provide travel logistics (departure, accommodation)
3. Explain payments, policies, refunds
4. Guide users to registration/booking

**FORMATTING RULES:**
- Use proper markdown formatting for lists
- For bullet points, use "• " (bullet symbol space)
- For links, use ONLY markdown: [link text](url). Example: [Registration/Login](https://oorzaayatra.com/login). Do NOT output raw HTML (no <a href=...>).
- Example of proper list format:
  If you need to cancel your yatra, the following terms apply:
  
  • Cancellations made before the specified cutoff date may be eligible for a partial refund.
  • Cancellations made after the cutoff date are generally non-refundable due to advance bookings.
  • Exact refund terms are shared at the time of registration.
  
  Additionally, if the yatra is cancelled by Oorzaa Yatra due to unavoidable circumstances, participants will be offered either a full refund or the option to transfer the amount to a future yatra.

**IMPORTANT COMMUNICATION RULES (VERY IMPORTANT) – The chatbot must always follow these:**

**Pricing & inclusion – what to say:**
• **Estimated pricing typically includes:** Travel as per itinerary; stay in good-quality ashram / hotel / resort; special gifts; three sattvic meals daily; expert-guided tour.
• **Estimated pricing typically excludes:** Personal or local expenses (where applicable).

**Rules you must always follow:**
1. Always say "estimated price", never "final price".
2. Clearly mention tentative dates where applicable.
3. Do not guarantee transport mode until officially confirmed.
4. Each yatra operates only if minimum participants register.
5. Prices may change depending on booking timing.
6. All pricing is from and to Delhi.

**MANDATORY COMMUNICATION – REFUND / CANCELLATION:**
Whenever a user asks about refund or cancellation, you MUST state (use this exact line or very close wording):
"Refunds are dependent on vendor policies (airlines, railways, hotels, or transport providers) and are not solely controlled by Oorzaa Yatra."
You may add this before or after other cancellation/refund details from context, but you must always include this sentence in your response.
For cancellation and refund questions, use the detailed Cancellation & Refund Policy from the context and explain eligibility, deductions, and timelines as per that policy.

**MANDATORY ESCALATION MESSAGE – CONFIRMATION / AVAILABILITY / EXACT PRICING:**
If a user asks about confirmation, availability, or exact pricing, you MUST reply (use this exact line or very close wording):
"Since pricing and availability can change based on bookings and confirmations, I'll connect you with our team to give you the most accurate and updated details."
Then offer contact options (call Neha, WhatsApp, or contact page) so they can get the live update.

**YATRA CATEGORY–WISE TRANSPORT & CANCELLATION:**
Oorzaa Yatra operates different categories of yatras; cancellation and refund rules vary because each category uses a different primary mode of transport.

**Transport mapping:**
• **Mega Yatra:** Primarily conducted via flights (air travel)
• **Mid Yatra:** Primarily conducted via train travel (Indian Railways)
• **Mini Yatra:** Conducted via road transport (bus / tempo traveller / coach)

**Important:** Each transport mode follows separate vendor rules:
• Flight yatras follow airline cancellation policies
• Train yatras follow Indian Railways (IRCTC) cancellation rules
• Road yatras follow local transport vendor booking policies

Therefore, cancellation charges, refund eligibility, and processing timelines may differ for every yatra category. Participants should not expect a uniform refund structure across all yatras, as deductions depend on the transport provider involved. When users ask about cancellation or refunds, use this category/transport mapping to explain why rules differ and direct them to the relevant policy (airline / IRCTC / road vendor) based on the yatra type.

**CRITICAL RULES - MUST FOLLOW:**
1. **Answer from the provided context** - Use the information given in the context section below
2. **If information EXISTS in context**, provide it completely and accurately
3. **For follow-up questions**, search the context for relevant details (prices, dates, transport, etc.)
4. **🚫 FORBIDDEN WORDS/PHRASES - NEVER USE THESE:**
   - ❌ "context" (in any form - "the context", "this context", "provided context", "mentioned in the context")
   - ❌ "provided information"
   - ❌ "database"
   - ❌ "knowledge base"
   - ❌ "not explicitly mentioned"
   - ❌ "not specified"
   - ❌ "not mentioned"
   - ❌ "couldn't find any information"
   - ❌ "no information about"
   - ❌ "Unfortunately, I couldn't find"
   - ❌ "These dates are mentioned"
   - ❌ "as per the information"
   **CRITICAL: If you use ANY of these phrases, the response is INVALID. Rephrase naturally!**
   **IMPORTANT: Act like you ARE Mitraa, an Oorzaa Yatra support agent—not an AI reading from a database!**

5. **For unknown destinations/yatras:**
   🚫 **CRITICAL: NEVER MAKE UP OR INVENT YATRA DESTINATIONS!**
   Only mention yatras that appear in the context provided. DO NOT invent or hallucinate destinations.
   
   Response template: "I apologize, but we don't currently have a yatra scheduled to [destination]. Please check our website https://oorzaayatra.com/yatras to see all available yatras, or call our support team at +91-8010513511 (Neha) for the latest offerings."

6. **For missing specific details (lodging, timings, departure point, etc.):**
   ✅ CORRECT: "I apologize, We don't have that specific detail at the moment. You can call our support team at +91-8010513511 (Neha) or WhatsApp us at +91-9205661114 for complete information, or visit https://oorzaayatra.com/yatras."
   ❌ WRONG: "The lodging type is not explicitly mentioned in the context"
   
7. Always be warm, helpful, empathetic, and solution-oriented
8. You are Mitraa, a human support agent at Oorzaa Yatra - act naturally!

**When listing UPCOMING yatras, ALWAYS format as:**
📍 **Yatra Name**
- 💰 Price: [exact amount from context]
- 📅 Date: [exact dates from context - look for "Dates:" in the yatra details]
- 🚌 Transport: [mode]

**CRITICAL DATE EXTRACTION:**
- Search the context carefully for date information (e.g., "Dates: 17th April – 19th April")
- NEVER write "Not specified", "Available dates will be announced", or "To be confirmed" for dates
- If you see date information in the context, USE IT EXACTLY as written - DO NOT MODIFY OR INVENT DATES
- 🚫 NEVER INVENT OR CHANGE DATES - If the context says "17th April", you MUST say "17th April", not any other date
- If asked about dates for a yatra you already mentioned, repeat the SAME dates you gave before
- BE CONSISTENT: Never give different dates for the same yatra in the same conversation

**IMPORTANT:** All yatra information (dates, prices, transport) comes from the context provided. Extract the exact details from the context.

Example:
📍 **Rishikesh & Shukartal Yatra**
- 💰 Price: ₹7,000
- 📅 Date: 17th April – 19th April
- 🚌 Transport: Deluxe Luxury Coach

**For COMPLETED yatras (past dates) or when asked "How can I see completed yatras?", ALWAYS share social media + website:**

When customer asks about completed yatras, past experiences, or wants to see proof of previous journeys, respond with:

"You can view the highlights and experiences from our completed yatras on our social media platforms and website:

📸 **Instagram** (Photos & Reels): https://www.instagram.com/oorzaa_yatra/
🎬 **YouTube** (Complete Videos): https://www.youtube.com/@OorzaaYatra
👨‍👩‍� **Facebook** (Albums & Reviews): https://www.facebook.com/profile.php?id=61584577333481

🌐 **Website Gallery**: https://oorzaayatra.com/yatras

These show real darshan moments, passenger experiences, and memories from our past yatras! 😊"

**CRITICAL**: When discussing completed yatras, ALWAYS include social media links - this is where customers see real proof and build trust.

When providing links for upcoming yatras, use these:
- Registration/Login: https://oorzaayatra.com/login
- Yatras Page: https://oorzaayatra.com/yatras
- Contact: https://oorzaayatra.com/contact
- Email: oorzaayatra@m2t.ai

**CONTACT NUMBERS - IMPORTANT DISTINCTION:**

📞 **For Call Support (Voice Calls):**
- Contact: Neha
- Phone: +91-8010513511
- Use for: Booking assistance, operational queries, coordination needs, detailed discussions

💬 **For WhatsApp Chat Support:**
- WhatsApp: +91-9205661114
- Link: https://wa.me/919205661114
- Use for: Quick queries, text-based support, sharing documents/links

**CRITICAL RULE:**
- When suggesting "call us" or "speak with our team" → Use Neha's number (+91-8010513511)
- When suggesting "WhatsApp us" or "message us" → Use WhatsApp number (+91-9205661114)
- ALWAYS specify which number is for what purpose when mentioning contact details

**SOCIAL MEDIA VERIFICATION & TRUST BUILDING:**

When customers express doubt about company authenticity, ask for proof, or want verification BEFORE booking, you MUST share our official social media platforms. This is CRITICAL for first-time travelers and families.

**TRIGGERS - Share social links when customer asks:**
- "Is the company genuine?"
- "Do you actually conduct yatras?"
- "Any proof?"
- "Can I see reviews?"
- "Need to verify before payment"
- "Show me customer experiences"
- "Koi proof hai?" / "Advance dene se pehle verify karna hai"

**Official Social Media Accounts (ALWAYS share these):**

🎥 **Instagram** (Primary - Live Yatra Updates):
https://www.instagram.com/oorzaa_yatra/
→ Reels from actual yatras, live darshan, bus journey, passenger reactions, daily trip stories

📹 **YouTube** (Complete Yatra Vlogs):
https://www.youtube.com/@OorzaaYatra
→ Full temple visits, group experiences, on-ground arrangements

👨‍👩‍👧 **Facebook** (Family & Senior Citizen Trust):
https://www.facebook.com/profile.php?id=61584577333481
→ Trusted by 40+ age group, parents verify here before allowing elders to travel

💼 **LinkedIn** (Corporate Authenticity):
https://www.linkedin.com/company/oorzaa/posts/?feedView=all
→ Company legitimacy, operations, useful for professionals & NRI travelers

**Standard Trust-Building Response Template:**
When customer needs verification, respond with:

"Namaste 🙏 I completely understand your concern. Before booking, you can verify our real yatras, customer experiences, and live travel stories on our official social media pages:

📸 **Instagram** (Live Updates): https://www.instagram.com/oorzaa_yatra/
🎬 **YouTube** (Complete Vlogs): https://www.youtube.com/@OorzaaYatra  
👨‍👩‍👧 **Facebook** (Customer Reviews): https://www.facebook.com/profile.php?id=61584577333481
💼 **LinkedIn** (Company Profile): https://www.linkedin.com/company/oorzaa/posts/?feedView=all

These show actual journeys of our yatris! 😊 After reviewing, I'll be happy to assist with your booking."

**KEY PRINCIPLE:**
✅ Don't over-convince verbally
✅ Show proof via social platforms
✅ "Verify yourself" (not "trust us")
✅ Social media = Digital darshan proof

This step builds confidence and reduces payment hesitation.
"""

# ========================
# CHROMA DB SETUP
# ========================

vector_stores = {}  # Dictionary to hold multiple collections
CHROMA_PERSIST_DIR = Path(__file__).parent / "chroma_db"
KNOWLEDGE_HASH_FILE = CHROMA_PERSIST_DIR / ".knowledge_hash"

# Collection definitions
COLLECTIONS = {
    "yatras": {
        "name": "oorzaa_yatras",
        "files": ["yatra_schedule.txt", "yatra"],  # Files containing these keywords
        "description": "Yatra schedules, destinations, and travel information"
    },
    "faqs": {
        "name": "oorzaa_faqs",
        "files": ["faq", "functional_requirements.txt"],
        "description": "Frequently asked questions and answers"
    },
    "policies": {
        "name": "oorzaa_policies",
        "files": ["policy", "policies", "additional_points.txt", "company_info.txt"],
        "description": "Policies, terms, and company information"
    }
}

def categorize_file(filename: str) -> str:
    """Categorize a file based on user selection (from metadata) or filename"""
    # First check if there's a manual collection mapping
    knowledge_dir = Path(__file__).parent / "knowledge"
    metadata_file = knowledge_dir / "collection_mappings.json"
    
    if metadata_file.exists():
        try:
            mappings = json.loads(metadata_file.read_text(encoding='utf-8'))
            if filename in mappings:
                return mappings[filename]
        except:
            pass
    
    # Fallback to automatic categorization based on keywords
    filename_lower = filename.lower()
    
    for category, config in COLLECTIONS.items():
        for keyword in config["files"]:
            if keyword in filename_lower:
                return category
    
    # Default to policies if no match
    return "policies"

def load_knowledge_by_collection() -> dict:
    """Load knowledge files grouped by collection"""
    knowledge_dir = Path(__file__).parent / "knowledge"
    collections_data = {cat: [] for cat in COLLECTIONS.keys()}
    
    if not knowledge_dir.exists():
        print("⚠️ Knowledge directory not found")
        return collections_data
    
    print("\n📚 Loading knowledge base by collection...")
    
    for file_path in sorted(knowledge_dir.glob("*.txt")) + sorted(knowledge_dir.glob("*.md")):
        try:
            content = file_path.read_text(encoding='utf-8')
            if content.strip():
                category = categorize_file(file_path.name)
                collections_data[category].append(content)
                print(f"✅ Loaded: {file_path.name} → {category}")
        except Exception as e:
            print(f"❌ Error loading {file_path.name}: {e}")
    
    return collections_data

def get_knowledge_hash() -> str:
    """Calculate hash of all knowledge files to detect changes"""
    knowledge_dir = Path(__file__).parent / "knowledge"
    if not knowledge_dir.exists():
        return ""
    
    hasher = hashlib.sha256()
    for file_path in sorted(knowledge_dir.glob("*.txt")) + sorted(knowledge_dir.glob("*.md")):
        hasher.update(file_path.read_bytes())
    return hasher.hexdigest()

def should_reingest() -> bool:
    """Check if knowledge base needs re-ingestion"""
    # Always check hash file, regardless of storage mode
    if not KNOWLEDGE_HASH_FILE.exists():
        return True
    
    current_hash = get_knowledge_hash()
    stored_hash = KNOWLEDGE_HASH_FILE.read_text() if KNOWLEDGE_HASH_FILE.exists() else ""
    
    return current_hash != stored_hash

def save_knowledge_hash():
    """Save current knowledge hash"""
    CHROMA_PERSIST_DIR.mkdir(exist_ok=True)
    current_hash = get_knowledge_hash()
    KNOWLEDGE_HASH_FILE.write_text(current_hash)

def _delete_documents_by_source(collection_name: str, filename: str):
    """Remove existing chunks with this source filename so re-upload = replace (Chroma Cloud or local)."""
    global vector_stores
    if collection_name not in vector_stores:
        return
    try:
        coll = vector_stores[collection_name]._collection
        coll.delete(where={"source": filename})
        print(f"🗑️ Replaced previous '{filename}' chunks in {collection_name} collection.")
    except Exception as e:
        print(f"⚠️ No previous chunks to replace for '{filename}' (or delete failed): {e}")


def ingest_content_to_collection(collection_name: str, content: str, filename: str, embeddings, append: bool = True):
    """Ingest content directly to a collection (cloud or local). Re-uploading the same filename replaces its chunks."""
    global vector_stores
    
    print(f"\n📥 Ingesting '{filename}' to {collection_name} collection...")
    
    config = COLLECTIONS[collection_name]
    
    # Replace-by-filename: remove existing chunks from this file so upload = update
    _delete_documents_by_source(collection_name, filename)
    
    # Split text into chunks
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    splits = text_splitter.create_documents(
        [content],
        metadatas=[{"category": collection_name, "collection": config["name"], "source": filename}] * len([content])
    )
    
    # Re-split to get proper metadata for each chunk
    splits = text_splitter.create_documents([content])
    for split in splits:
        split.metadata = {"category": collection_name, "collection": config["name"], "source": filename}
    
    print(f"💾 Adding {len(splits)} chunks to {collection_name} collection...")
    
    if CHROMA_USE_CLOUD:
        import chromadb
        tenant_id = CHROMA_CLOUD_HOST.split('.')[0]
        chroma_client = chromadb.CloudClient(
            api_key=CHROMA_CLOUD_API_KEY,
            tenant=tenant_id,
            database='OorzaYatra'
        )
        
        # Get or create collection
        if collection_name not in vector_stores:
            vector_stores[collection_name] = Chroma(
                client=chroma_client,
                collection_name=config["name"],
                embedding_function=embeddings
            )
        
        vector_stores[collection_name].add_documents(splits)
    else:
        # Use local persistent storage
        if collection_name not in vector_stores:
            vector_stores[collection_name] = Chroma(
                collection_name=config["name"],
                embedding_function=embeddings,
                persist_directory=str(CHROMA_PERSIST_DIR)
            )
        
        vector_stores[collection_name].add_documents(splits)
    
    print(f"✅ '{filename}' ingested to {collection_name} collection!")
    return len(splits)

def reingest_collection(collection_name: str, embeddings):
    """Reingest only a specific collection from local files (legacy support)"""
    global vector_stores
    
    print(f"\n🔄 Re-ingesting {collection_name} collection...")
    
    # Load all files for this collection
    collections_data = load_knowledge_by_collection()
    collection_content = collections_data.get(collection_name, [])
    
    if not collection_content:
        print(f"⚠️ No content for {collection_name} collection")
        return
    
    # Get collection config
    config = COLLECTIONS[collection_name]
    
    # Combine all documents for this collection
    combined_content = "\n\n---\n\n".join(collection_content)
    
    # Split text into chunks
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    splits = text_splitter.create_documents(
        [combined_content],
        metadatas=[{"category": collection_name, "collection": config["name"]}] * len([combined_content])
    )
    
    print(f"💾 Updating {collection_name} collection ({len(splits)} chunks)...")
    
    if CHROMA_USE_CLOUD:
        # Use Chroma Cloud
        import chromadb
        tenant_id = CHROMA_CLOUD_HOST.split('.')[0]
        chroma_client = chromadb.CloudClient(
            api_key=CHROMA_CLOUD_API_KEY,
            tenant=tenant_id,
            database='OorzaYatra'
        )
        
        # Delete existing collection and recreate
        try:
            chroma_client.delete_collection(name=config["name"])
            print(f"🗑️ Deleted old {collection_name} collection")
        except:
            pass
        
        vector_stores[collection_name] = Chroma(
            client=chroma_client,
            collection_name=config["name"],
            embedding_function=embeddings
        )
        vector_stores[collection_name].add_documents(splits)
    else:
        # Use local persistent storage
        # Delete and recreate collection
        try:
            old_collection = Chroma(
                collection_name=config["name"],
                embedding_function=embeddings,
                persist_directory=str(CHROMA_PERSIST_DIR)
            )
            old_collection.delete_collection()
            print(f"🗑️ Deleted old {collection_name} collection")
        except:
            pass
        
        vector_stores[collection_name] = Chroma.from_documents(
            documents=splits,
            embedding=embeddings,
            collection_name=config["name"],
            persist_directory=str(CHROMA_PERSIST_DIR)
        )
    
    # Update hash file
    save_knowledge_hash()
    print(f"✅ {collection_name} collection updated successfully!")

def initialize_vector_store():
    """Initialize ChromaDB with multiple collections"""
    global vector_stores
    
    # Initialize embeddings model with increased timeout
    print("\n🔄 Loading embedding model...")
    try:
        # Set environment variable for HuggingFace timeout
        os.environ['HF_HUB_DOWNLOAD_TIMEOUT'] = '300'  # 5 minutes
        
        embeddings = HuggingFaceEmbeddings(
            model_name="all-MiniLM-L6-v2",
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True}
        )
    except Exception as e:
        print(f"⚠️ Error loading embedding model: {e}")
        print("💡 Tip: The model is downloading from HuggingFace. Please wait or check your internet connection.")
        raise
    
    # Check if we need to re-ingest
    if should_reingest():
        print("📚 Loading knowledge base by collections...")
        collections_data = load_knowledge_by_collection()
        
        # Initialize each collection
        for category, config in COLLECTIONS.items():
            collection_content = collections_data.get(category, [])
            
            if not collection_content:
                print(f"⚠️ No content for {category} collection")
                continue
            
            # Combine all documents for this collection
            combined_content = "\n\n---\n\n".join(collection_content)
            
            # Split text into chunks
            text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
            splits = text_splitter.create_documents(
                [combined_content],
                metadatas=[{"category": category, "collection": config["name"]}] * len([combined_content])
            )
            
            # Create persistent Chroma vector store for this collection
            print(f"💾 Ingesting {category} collection ({len(splits)} chunks)...")
            
            if CHROMA_USE_CLOUD:
                # Use Chroma Cloud
                import chromadb
                # Extract tenant ID from host (format: tenant.api.trychroma.com)
                tenant_id = CHROMA_CLOUD_HOST.split('.')[0]
                chroma_client = chromadb.CloudClient(
                    api_key=CHROMA_CLOUD_API_KEY,
                    tenant=tenant_id,
                    database='OorzaYatra'
                )
                
                # Delete existing collection first to prevent duplicates
                try:
                    chroma_client.delete_collection(name=config["name"])
                    print(f"🗑️ Deleted old {category} collection from cloud")
                except:
                    pass
                
                vector_stores[category] = Chroma(
                    client=chroma_client,
                    collection_name=config["name"],
                    embedding_function=embeddings
                )
                vector_stores[category].add_documents(splits)
            else:
                # Use local persistent storage
                vector_stores[category] = Chroma.from_documents(
                    documents=splits,
                    embedding=embeddings,
                    collection_name=config["name"],
                    persist_directory=str(CHROMA_PERSIST_DIR)
                )
        
        # Save hash to prevent re-ingestion
        save_knowledge_hash()
        print(f"✅ All {len(vector_stores)} collections initialized successfully!")
    else:
        # Load existing vector stores
        if CHROMA_USE_CLOUD:
            print("📂 Loading existing collections from Chroma Cloud...")
            import chromadb
            # Extract tenant ID from host (format: tenant.api.trychroma.com)
            tenant_id = CHROMA_CLOUD_HOST.split('.')[0]
            chroma_client = chromadb.CloudClient(
                api_key=CHROMA_CLOUD_API_KEY,
                tenant=tenant_id,
                database='OorzaYatra'
            )
            for category, config in COLLECTIONS.items():
                try:
                    vector_stores[category] = Chroma(
                        client=chroma_client,
                        collection_name=config["name"],
                        embedding_function=embeddings
                    )
                    print(f"✅ Loaded: {category} (from cloud)")
                except Exception as e:
                    print(f"⚠️ Could not load {category} from cloud: {e}")
        else:
            print("📂 Loading existing collections from disk...")
            for category, config in COLLECTIONS.items():
                try:
                    vector_stores[category] = Chroma(
                        collection_name=config["name"],
                        embedding_function=embeddings,
                        persist_directory=str(CHROMA_PERSIST_DIR)
                    )
                    print(f"✅ Loaded: {category}")
                except Exception as e:
                    print(f"⚠️ Could not load {category}: {e}")
        
        storage_location = "Chroma Cloud" if CHROMA_USE_CLOUD else "disk"
        print(f"✅ {len(vector_stores)} collections loaded from {storage_location} (no re-ingestion needed).")

# ========================
# MODELS & UTILS
# ========================

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    message: str
    conversation_history: Optional[List[ChatMessage]] = []
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    session_id: str
    should_escalate: bool = False
    escalation_reason: Optional[str] = None
    links: Optional[List[dict]] = None
    used_rag: bool = True
    show_live_agent_option: bool = False
    show_callback_option: bool = False

failed_attempts: dict = {}

def get_rag_response(query: str, chat_history: List):
    """Get RAG response by searching across all collections"""
    if not vector_stores:
        raise ValueError("Vector stores not initialized")
    
    if not OPENAI_API_KEY:
        raise ValueError("OpenAI API key not configured")
        
    llm = ChatOpenAI(
        model="gpt-4o-mini",
        api_key=OPENAI_API_KEY,
        temperature=0.3,
        max_tokens=512  # Limit response length to keep answers concise
    )
    
    # Search across all collections and gather results
    all_docs = []
    for category, store in vector_stores.items():
        retriever = store.as_retriever(search_kwargs={"k": 4})  # Get top 4 from each for better coverage
        docs = retriever.invoke(query)
        # Add category info to each doc
        for doc in docs:
            doc.metadata["source_category"] = category
            all_docs.append(doc)
    
    # Check if we have any relevant documents
    if not all_docs:
        return "🙏 Namaste! I apologize, but I don't have that information right now. Please contact our support team at +91-9205661114 or visit https://oorzaayatra.com for assistance. We're happy to help! ✨"
    
    # Sort by relevance (if needed) and take top results
    # For now, we'll use all retrieved docs
    context_parts = []
    for doc in all_docs[:10]:  # Limit to 10 total docs for better coverage
        category = doc.metadata.get("source_category", "unknown")
        context_parts.append(f"[{category.upper()}]\n{doc.page_content}")
    
    context = "\n\n---\n\n".join(context_parts)
    
    # Build prompt with context and history
    messages = [SystemMessage(content=SYSTEM_PROMPT + f"\n\nContext:\n{context}")]
    messages.extend(chat_history)
    messages.append(HumanMessage(content=query))
    
    # Get response
    response = llm.invoke(messages)
    return response.content

def detect_links_needed(message: str) -> List[dict]:
    """Detect links based on keywords"""
    links = []
    msg = message.lower()
    
    if any(w in msg for w in ["register", "join", "book", "sign up", "login"]):
        links.append({"text": "Register/Login", "url": "https://oorzaayatra.com/login", "type": "registration"})
    # Payment Options link removed as per user request
    # if any(w in msg for w in ["pay", "money", "cost", "price"]):
    #     links.append({"text": "Payment Options", "url": "https://oorzaayatra.com/login", "type": "payment"})
    if any(w in msg for w in ["contact", "call", "help", "support"]):
        links.append({"text": "WhatsApp Support", "url": "https://wa.me/919205661114", "type": "whatsapp"})
        
    return links

def check_escalation(session_id: str, response: str) -> bool:
    """Check for human handoff need"""
    uncertain = ["i don't know", "contact support", "unable to answer", "not sure"]
    if any(p in response.lower() for p in uncertain):
        failed_attempts[session_id] = failed_attempts.get(session_id, 0) + 1
    else:
        failed_attempts[session_id] = 0
    return failed_attempts.get(session_id, 0) >= 3

# ========================
# API ENDPOINTS
# ========================

@app.on_event("startup")
async def startup_event():
    initialize_vector_store()

@app.get("/")
async def root():
    return {"message": "Mitraa Chatbot API v2.1 (OpenAI + ChromaDB)", "status": "running"}

@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    if not OPENAI_API_KEY:
        raise HTTPException(500, "OPENAI_API_KEY missing")
        
    try:
        # Count user messages in conversation history
        user_message_count = sum(1 for msg in request.conversation_history if msg.role == "user")
        user_message_count += 1  # Include current message
        
        # Check if conversation limit exceeded
        if user_message_count > MAX_CONVERSATION_TURNS:
            import uuid
            session_id = request.session_id or str(uuid.uuid4())
            
            limit_message = f"""🙏 Namaste!

I notice you have many questions. For detailed assistance and personalized guidance, please connect with our support team:

📞 **Call Us:** +91-8010513511 (Neha)
💬 **WhatsApp:** https://wa.me/919205661114
📧 **Email:** oorzaayatra@m2t.ai
🌐 **Contact Form:** https://oorzaayatra.com/contact

Our team will be happy to help you with all your queries! ✨"""
            
            return ChatResponse(
                response=limit_message,
                session_id=session_id,
                should_escalate=True,
                links=[
                    {"text": "Neha: 8010513511", "url": "tel:8010513511", "type": "live_agent", "note": "For operational coordination, internal follow-ups, and yatra execution related communication."},
                    {"text": "WhatsApp Support", "url": "https://wa.me/919205661114", "type": "whatsapp"},
                    {"text": "Contact Us", "url": "https://oorzaayatra.com/contact", "type": "contact"}
                ],
                used_rag=False
            )
        
        # Prepare history
        chat_history = []
        for msg in request.conversation_history:
            if msg.role == "user":
                chat_history.append(HumanMessage(content=msg.content))
            else:
                chat_history.append(AIMessage(content=msg.content))
        
        # Get RAG response
        response_text = get_rag_response(request.message, chat_history)
        
        # Escalation logic for complex/uncertain queries
        import uuid
        session_id = request.session_id or str(uuid.uuid4())
        links = detect_links_needed(request.message)
        escalate = check_escalation(session_id, response_text)
        show_live_agent_option = escalate
        show_callback_option = escalate
        escalation_reason = None
        if escalate:
            escalation_reason = "Complex or unclear query. User may need human support."
            # Add Neha's direct contact for operations
            links.append({
                "text": "Neha: 8010513511",
                "url": "tel:8010513511",
                "type": "live_agent",
                "note": "For operational coordination, internal follow-ups, and yatra execution related communication."
            })
            links.append({
                "text": "Connect with a Human Agent",
                "url": "https://oorzaayatra.com/contact",
                "type": "live_agent"
            })
            links.append({
                "text": "Request a Callback",
                "url": "https://oorzaayatra.com/callback",
                "type": "callback"
            })
        return ChatResponse(
            response=response_text,
            session_id=session_id,
            should_escalate=escalate,
            escalation_reason=escalation_reason,
            links=links,
            used_rag=True,
            show_live_agent_option=show_live_agent_option,
            show_callback_option=show_callback_option
        )
        # Callback request model and endpoint
        from fastapi import Body
        from pydantic import EmailStr

        class CallbackRequest(BaseModel):
            name: str
            phone: str
            email: Optional[EmailStr] = None
            preferred_time: Optional[str] = None
            message: Optional[str] = None

        callback_requests = []

        @app.post("/api/callback/request")
        async def request_callback(data: CallbackRequest = Body(...)):
            callback_requests.append(data.dict())
            # In production, send to CRM or notify agent
            return {"success": True, "message": "Callback request received. Our team will contact you soon!"}
        
    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(500, str(e))

@app.post("/api/knowledge/upload")
async def upload_knowledge(
    file: UploadFile = File(...),
    collection: str = Form(...)
):
    """Upload a knowledge file (.txt, .md, or .pdf) directly to Chroma Cloud"""
    try:
        # Validate collection
        valid_collections = ['yatras', 'faqs', 'policies']
        if collection not in valid_collections:
            raise HTTPException(400, f"Invalid collection. Must be one of: {', '.join(valid_collections)}")
        
        # Validate file extension
        if not file.filename.endswith(('.txt', '.md', '.pdf')):
            raise HTTPException(400, "Only .txt, .md, and .pdf files are allowed")
        
        # Read file content
        content = await file.read()
        
        # Validate content is not empty
        if not content:
            raise HTTPException(400, "File is empty")
        
        # Parse content based on file type
        if file.filename.endswith('.pdf'):
            # Parse PDF
            try:
                from PyPDF2 import PdfReader
                import io
                pdf_reader = PdfReader(io.BytesIO(content))
                content_str = ""
                for page in pdf_reader.pages:
                    text = page.extract_text()
                    if text:
                        content_str += text + "\n"
                if not content_str.strip():
                    raise HTTPException(400, "Could not extract text from PDF")
            except ImportError:
                raise HTTPException(500, "PDF parsing library not installed")
            except Exception as e:
                raise HTTPException(400, f"Failed to parse PDF: {str(e)}")
        else:
            # Parse text/markdown
            try:
                content_str = content.decode('utf-8')
            except UnicodeDecodeError:
                raise HTTPException(400, "File must be valid UTF-8 text")
        
        # Initialize embeddings
        embeddings = HuggingFaceEmbeddings(
            model_name="all-MiniLM-L6-v2",
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True}
        )
        
        # Initialize vector stores if not already done
        if not vector_stores:
            initialize_vector_store()
        
        # Ingest directly to Chroma Cloud (no local storage)
        chunks_added = ingest_content_to_collection(collection, content_str, file.filename, embeddings)
        
        print(f"📤 File uploaded: {file.filename} → {collection} collection ({chunks_added} chunks)")
        
        return {
            "success": True,
            "message": f"File '{file.filename}' ingested directly to {collection} collection ({chunks_added} chunks)",
            "filename": file.filename,
            "category": collection,
            "size_bytes": len(content),
            "chunks": chunks_added
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Upload error: {e}")
        raise HTTPException(500, f"Upload failed: {str(e)}")

@app.get("/api/knowledge/files")
async def list_knowledge_files():
    """List all knowledge files in the knowledge base"""
    try:
        knowledge_dir = Path(__file__).parent / "knowledge"
        if not knowledge_dir.exists():
            return {"files": []}
        
        files = []
        for file_path in sorted(knowledge_dir.glob("*.txt")) + sorted(knowledge_dir.glob("*.md")):
            files.append({
                "name": file_path.name,
                "size_bytes": file_path.stat().st_size,
                "modified": file_path.stat().st_mtime
            })
        
        return {"files": files}
    except Exception as e:
        print(f"Error listing files: {e}")
        raise HTTPException(500, str(e))

@app.delete("/api/knowledge/files/{filename}")
async def delete_knowledge_file(filename: str):
    """Delete a knowledge file"""
    try:
        knowledge_dir = Path(__file__).parent / "knowledge"
        file_path = knowledge_dir / filename
        
        if not file_path.exists():
            raise HTTPException(404, "File not found")
        
        if not file_path.suffix in ['.txt', '.md']:
            raise HTTPException(400, "Can only delete .txt and .md files")
        
        file_path.unlink()
        
        # Trigger re-ingestion
        print(f"\n🗑️ File deleted: {filename}")
        initialize_vector_store()
        
        return {"success": True, "message": f"File '{filename}' deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        print(f"Delete error: {e}")
        raise HTTPException(500, str(e))

@app.get("/api/knowledge/collections")
async def get_collections_info():
    """Get information about all collections"""
    try:
        collections_info = []
        for category, config in COLLECTIONS.items():
            info = {
                "category": category,
                "name": config["name"],
                "description": config["description"],
                "file_patterns": config["files"],
                "loaded": category in vector_stores
            }
            
            if category in vector_stores:
                # Get collection stats
                try:
                    collection = vector_stores[category]._collection
                    info["document_count"] = collection.count()
                except:
                    info["document_count"] = "N/A"
            else:
                info["document_count"] = 0
            
            collections_info.append(info)
        
        return {
            "collections": collections_info,
            "total_collections": len(COLLECTIONS),
            "active_collections": len(vector_stores)
        }
    except Exception as e:
        print(f"Error getting collections: {e}")
        raise HTTPException(500, str(e))

@app.post("/api/knowledge/refresh")
async def refresh_knowledge_base():
    """
    Force re-ingestion of the knowledge base from the knowledge/ folder.
    Call this after you update .txt/.md files in backend/knowledge/ so the chatbot
    uses the latest content without restarting the server.
    """
    try:
        if KNOWLEDGE_HASH_FILE.exists():
            KNOWLEDGE_HASH_FILE.unlink()
            print("🔄 Cleared knowledge hash to force re-ingestion.")
        initialize_vector_store()
        return {
            "success": True,
            "message": "Knowledge base refreshed from knowledge/ folder. The chatbot will now use the updated content."
        }
    except Exception as e:
        print(f"Refresh error: {e}")
        raise HTTPException(500, f"Refresh failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)

