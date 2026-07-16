from flask_sqlalchemy import SQLAlchemy
import chromadb

db = SQLAlchemy()

# Chroma client - persistent, lives in instance/ alongside mate.db.
# Unlike db, this doesn't need an init_app() call - PersistentClient
# is ready to use as soon as it's constructed.
chroma_client = chromadb.PersistentClient(path="instance/chroma_store")

# One shared collection for all documents, filtered by doc_id at query time
doc_collection = chroma_client.get_or_create_collection(name="mate_documents")