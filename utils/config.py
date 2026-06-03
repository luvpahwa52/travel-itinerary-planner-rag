import os
from dotenv import load_dotenv

load_dotenv()

# AWS Bedrock
AWS_REGION = os.getenv("AWS_DEFAULT_REGION", "us-east-1")
LLM_MODEL_ID = "amazon.nova-micro-v1:0"
EMBED_MODEL_ID = "amazon.titan-embed-text-v2:0"

# LLM Settings (used in Phase 4)
LLM_TEMPERATURE = 0.3
LLM_MAX_TOKENS = 2048
LLM_TOP_P = 0.9

# ChromaDB
CHROMA_DB_PATH = "db/chroma_store"
COLLECTION_NAME = "travel_knowledge"

# Retriever
TOP_K_RESULTS = 5