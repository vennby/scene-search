import os
import chromadb
from sentence_transformers import SentenceTransformer

# =============== CONFIG =============== #

CHROMA_DB_PATH = "chroma_db"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"

# Initialize Chroma client (persistent)
client = chromadb.PersistentClient(path=CHROMA_DB_PATH)

# Initialize embedding model
embedding_model = SentenceTransformer(EMBEDDING_MODEL)

# =============== HELPER FUNCTIONS =============== #

def get_collection(collection_name):
    """Get or create a Chroma collection"""
    return client.get_or_create_collection(
        name=collection_name,
        metadata={"hnsw:space": "cosine"}
    )


def get_searchable_text(title, description, tags):
    """Combine title, description, and tags into searchable text"""
    parts = []
    if title:
        parts.append(str(title).strip())
    if description:
        parts.append(str(description).strip())
    if tags:
        parts.append(str(tags).strip())
    
    return " ".join(parts)


def get_embedding(text):
    """Generate semantic embedding for text"""
    if not text or not str(text).strip():
        return None
    
    try:
        text = str(text).strip()
        embedding = embedding_model.encode(text, convert_to_numpy=True)
        return embedding.tolist()
    except Exception as e:
        print(f"Error generating embedding: {e}")
        return None

# =============== ADD/UPDATE FUNCTIONS =============== #

def add_or_update_video(video_id, title, description, tags):
    """Add or update a video clip in the vector database"""
    collection = get_collection("videos")
    
    searchable_text = get_searchable_text(title, description, tags)
    
    if not searchable_text:
        return
    
    embedding = get_embedding(searchable_text)
    if not embedding:
        return
    
    try:
        collection.upsert(
            ids=[str(video_id)],
            embeddings=[embedding],
            metadatas=[{
                "type": "video",
                "title": title or "",
                "description": description or "",
                "tags": tags or "",
            }],
            documents=[searchable_text]
        )
    except Exception as e:
        print(f"Error upserting video {video_id}: {e}")


def add_or_update_document(doc_id, title, description, tags, file_type):
    """Add or update a document in the vector database"""
    collection = get_collection("documents")
    
    searchable_text = get_searchable_text(title, description, tags)
    
    if not searchable_text:
        return
    
    embedding = get_embedding(searchable_text)
    if not embedding:
        return
    
    try:
        collection.upsert(
            ids=[str(doc_id)],
            embeddings=[embedding],
            metadatas=[{
                "type": file_type,  # 'text' or 'pdf'
                "title": title or "",
                "description": description or "",
                "tags": tags or "",
            }],
            documents=[searchable_text]
        )
    except Exception as e:
        print(f"Error upserting document {doc_id}: {e}")

# =============== SEARCH FUNCTION =============== #

def semantic_search(query, k=20):
    """
    Perform semantic search across videos and documents.
    Returns results ranked by similarity score (0-1).
    """
    if not query or not str(query).strip():
        return {"results": [], "query": query, "total": 0}
    
    query = str(query).strip()
    
    # Generate embedding for the query
    query_embedding = get_embedding(query)
    if not query_embedding:
        return {"results": [], "query": query, "total": 0}
    
    all_results = []
    
    # Search videos
    try:
        videos_collection = get_collection("videos")
        video_results = videos_collection.query(
            query_embeddings=[query_embedding],
            n_results=k,
            include=["distances", "metadatas", "documents"]
        )
        
        if video_results["ids"] and video_results["ids"][0]:
            for i, video_id in enumerate(video_results["ids"][0]):
                distance = video_results["distances"][0][i]
                similarity_score = 1 - distance
                
                metadata = video_results["metadatas"][0][i]
                all_results.append({
                    "id": int(video_id),
                    "type": "video",
                    "file_type": "video",
                    "title": metadata.get("title", ""),
                    "description": metadata.get("description", ""),
                    "tags": metadata.get("tags", ""),
                    "score": similarity_score
                })
    except Exception as e:
        print(f"Error searching videos: {e}")
    
    # Search documents
    try:
        docs_collection = get_collection("documents")
        doc_results = docs_collection.query(
            query_embeddings=[query_embedding],
            n_results=k,
            include=["distances", "metadatas", "documents"]
        )
        
        if doc_results["ids"] and doc_results["ids"][0]:
            for i, doc_id in enumerate(doc_results["ids"][0]):
                distance = doc_results["distances"][0][i]
                similarity_score = 1 - distance
                
                metadata = doc_results["metadatas"][0][i]
                all_results.append({
                    "id": int(doc_id),
                    "type": "document",
                    "file_type": "document",
                    "title": metadata.get("title", ""),
                    "description": metadata.get("description", ""),
                    "tags": metadata.get("tags", ""),
                    "score": similarity_score
                })
    except Exception as e:
        print(f"Error searching documents: {e}")
    
    # Sort by similarity score (descending)
    all_results.sort(key=lambda x: x["score"], reverse=True)
    
    return {
        "results": all_results[:k],
        "query": query,
        "total": len(all_results[:k])
    }

# =============== DELETE FUNCTIONS =============== #

def delete_video(video_id):
    """Delete a video from the vector database"""
    try:
        collection = get_collection("videos")
        collection.delete(ids=[str(video_id)])
    except Exception as e:
        print(f"Error deleting video {video_id}: {e}")


def delete_document(doc_id):
    """Delete a document from the vector database"""
    try:
        collection = get_collection("documents")
        collection.delete(ids=[str(doc_id)])
    except Exception as e:
        print(f"Error deleting document {doc_id}: {e}")

# =============== INITIALIZATION =============== #

def initialize_all_embeddings(video_clips, text_documents):
    """
    Initialize embeddings for all existing content from the database.
    Call this once on app startup to sync vector DB with SQL DB.
    """
    print("\n" + "="*60)
    print("🔄 INITIALIZING EMBEDDINGS FROM DATABASE")
    print("="*60)
    
    # Add all video clips
    video_count = 0
    for clip in video_clips:
        try:
            add_or_update_video(clip.id, clip.title, clip.description, clip.tags)
            video_count += 1
        except Exception as e:
            print(f"❌ Video {clip.id}: {e}")
    
    # Add all text documents
    doc_count = 0
    for doc in text_documents:
        try:
            add_or_update_document(doc.id, doc.title, doc.description, doc.tags, doc.file_type)
            doc_count += 1
        except Exception as e:
            print(f"❌ Document {doc.id}: {e}")
    
    print("="*60)
    print(f"✅ INITIALIZED: {video_count} videos + {doc_count} documents")
    print("="*60 + "\n")
