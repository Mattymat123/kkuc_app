"""
Search Tools for RAG Workflow
Handles vector search, BM25 search, hybrid search, and reranking
"""
import os
from typing import List

import weaviate
from weaviate.classes.query import MetadataQuery
from rank_bm25 import BM25Okapi
import cohere

from . import SearchResult


class SearchTools:
    """Tools for searching and reranking documents"""
    
    def __init__(self):
        """Initialize search tools with API clients"""
        # Initialize Weaviate client
        self.weaviate_client = weaviate.connect_to_weaviate_cloud(
            cluster_url=os.getenv("WEAVIATE_URL"),
            auth_credentials=weaviate.auth.AuthApiKey(os.getenv("WEAVIATE_API_KEY"))
        )
        
        # Initialize Cohere client
        self.cohere_client = cohere.Client(api_key=os.getenv("COHERE_API_KEY"))
        
        # Weaviate collection name
        self.collection_name = "KKUCContent"
        
        # Cache for BM25
        self._bm25_index = None
        self._bm25_documents = None
    
    def _get_bm25_index(self):
        """Lazy load BM25 index from Weaviate"""
        if self._bm25_index is None:
            print("  🔍 Building BM25 index...")
            collection = self.weaviate_client.collections.get(self.collection_name)
            
            # Fetch all documents
            response = collection.query.fetch_objects(limit=1000)
            
            self._bm25_documents = []
            texts = []
            
            for obj in response.objects:
                doc = {
                    'content': obj.properties.get('content', ''),
                    'source_url': obj.properties.get('source_url', ''),
                    'page_title': obj.properties.get('page_title', ''),
                    'uuid': str(obj.uuid)
                }
                self._bm25_documents.append(doc)
                texts.append(doc['content'])
            
            # Tokenize for BM25
            tokenized_corpus = [doc.lower().split() for doc in texts]
            self._bm25_index = BM25Okapi(tokenized_corpus)
            
            print(f"    ✓ BM25 index built with {len(self._bm25_documents)} documents")
        
        return self._bm25_index, self._bm25_documents
    
    def vector_search(self, query: str, limit: int = 10) -> List[SearchResult]:
        """Perform vector similarity search in Weaviate"""
        try:
            # Ensure query is a string
            if isinstance(query, list):
                query = query[0] if query else ""
            query = str(query)
            
            collection = self.weaviate_client.collections.get(self.collection_name)
            
            # Generate embedding for query using Cohere
            query_embedding = self.cohere_client.embed(
                texts=[query],
                model="embed-multilingual-v3.0",
                input_type="search_query"
            ).embeddings[0]
            
            # Search with vector
            response = collection.query.near_vector(
                near_vector=query_embedding,
                limit=limit,
                return_metadata=MetadataQuery(distance=True)
            )
            
            results = []
            for obj in response.objects:
                result = SearchResult(
                    content=obj.properties.get('content', ''),
                    source_url=obj.properties.get('source_url', ''),
                    page_title=obj.properties.get('page_title', ''),
                    score=1.0 - obj.metadata.distance  # Convert distance to similarity
                )
                results.append(result)
            
            print(f"  🔍 Vector search: {len(results)} results")
            return results
            
        except Exception as e:
            print(f"  ⚠️  Error in vector search: {e}")
            return []
    
    def bm25_search(self, query: str, limit: int = 10) -> List[SearchResult]:
        """Perform BM25 keyword search"""
        try:
            # Ensure query is a string
            if isinstance(query, list):
                query = query[0] if query else ""
            query = str(query)
            
            bm25_index, documents = self._get_bm25_index()
            
            # Tokenize query
            tokenized_query = query.lower().split()
            
            # Get BM25 scores
            scores = bm25_index.get_scores(tokenized_query)
            
            # Get top results
            top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:limit]
            
            results = []
            for idx in top_indices:
                if scores[idx] > 0:  # Only include results with positive scores
                    doc = documents[idx]
                    result = SearchResult(
                        content=doc['content'],
                        source_url=doc['source_url'],
                        page_title=doc['page_title'],
                        score=scores[idx]
                    )
                    results.append(result)
            
            print(f"  📝 BM25 search: {len(results)} results")
            return results
            
        except Exception as e:
            print(f"  ⚠️  Error in BM25 search: {e}")
            return []
    
    def hybrid_search(self, query: str, limit: int = 20) -> List[SearchResult]:
        """Combine vector and BM25 search results"""
        # Get results from both methods
        vector_results = self.vector_search(query, limit=limit)
        bm25_results = self.bm25_search(query, limit=limit)
        
        # Combine and deduplicate by URL + content
        seen = set()
        combined = []
        
        for result in vector_results + bm25_results:
            key = (result.source_url, result.content[:100])
            if key not in seen:
                seen.add(key)
                combined.append(result)
        
        print(f"  🔀 Hybrid search: {len(combined)} unique results")
        return combined
    
    def rerank_results(self, query: str, results: List[SearchResult], top_k: int = 10) -> List[SearchResult]:
        """Rerank results using Cohere reranker"""
        if not results:
            return []
        
        try:
            # Ensure query is a string
            if isinstance(query, list):
                query = query[0] if query else ""
            query = str(query)
            
            # Prepare documents for reranking
            documents = [r.content for r in results]
            
            # Rerank with Cohere
            rerank_response = self.cohere_client.rerank(
                model="rerank-multilingual-v3.0",
                query=query,
                documents=documents,
                top_n=top_k
            )
            
            # Map reranked results back to SearchResult objects
            reranked = []
            for result in rerank_response.results:
                original_result = results[result.index]
                # Update score with rerank score
                reranked_result = SearchResult(
                    content=original_result.content,
                    source_url=original_result.source_url,
                    page_title=original_result.page_title,
                    score=result.relevance_score
                )
                reranked.append(reranked_result)
            
            print(f"  🎯 Reranked to top {len(reranked)} results")
            return reranked
            
        except Exception as e:
            print(f"  ⚠️  Error in reranking: {e}")
            # Return original results sorted by score
            return sorted(results, key=lambda x: x.score, reverse=True)[:top_k]
    
    def close(self):
        """Close connections"""
        if self.weaviate_client:
            self.weaviate_client.close()
