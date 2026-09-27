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

# One shared collection for all documents, filtered by doc_id at query time
doc_collection = chroma_client.get_or_create_collection(name="mate_documents")
