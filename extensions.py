from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
import chromadb

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = "auth.login"
login_manager.login_message = "Please sign in to continue."
login_manager.login_message_category = "info"
migrate = Migrate()
csrf = CSRFProtect()

# Chroma client - persistent, lives in instance/ alongside mate.db.
# Unlike db, this doesn't need an init_app() call - PersistentClient
# is ready to use as soon as it's constructed.
chroma_client = chromadb.PersistentClient(path="instance/chroma_store")

# Embedding function: BAAI/bge-base-en-v1.5 significantly outperforms
# the default MiniLM for construction/legal document retrieval.
# Model downloads on first use (~400 MB).
# Falls back to ChromaDB's default (all-MiniLM-L6-v2) if
# sentence-transformers is not yet installed.
try:
    from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction

    _embedding_fn = SentenceTransformerEmbeddingFunction(
        model_name="BAAI/bge-base-en-v1.5",
    )
    _collection_name = "mate_documents_v2"
except (ImportError, ValueError):
    _embedding_fn = None
    _collection_name = "mate_documents"

if _embedding_fn:
    doc_collection = chroma_client.get_or_create_collection(
        name=_collection_name,
        embedding_function=_embedding_fn,
    )
else:
    doc_collection = chroma_client.get_or_create_collection(name=_collection_name)
