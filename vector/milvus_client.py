# -*- coding: utf-8 -*-
"""Milvus client - upsert and search operations for OpenAPI vectors."""

from pathlib import Path

from pymilvus import MilvusClient, DataType, AnnSearchRequest
from pymilvus import Function, FunctionType

from config import MILVUS_HOST, MILVUS_PORT, MILVUS_COLLECTION, DIM
from vector.embedder import get_embedder


def make_uri(path: str, method: str) -> str:
    """Create a URI key from path and method."""
    return f"{method.upper()} {path}"


class MilvusVectorStore:
    """Milvus vector store for OpenAPI search."""

    MILVUS_DB = "restapi"

    def __init__(self, collection: str | None = None, host: str = MILVUS_HOST, port: int = MILVUS_PORT):
        self.client = MilvusClient(uri=f"http://{host}:{port}", db_name=self.MILVUS_DB)
        self.collection = collection or MILVUS_COLLECTION
        self.embedder = get_embedder()

    def _ensure_database(self) -> None:
        """Ensure the restapi database exists, create if not."""
        try:
            databases = self.client.list_databases()
            if self.MILVUS_DB not in databases:
                self.client.create_database(self.MILVUS_DB)
                print(f"Created database: {self.MILVUS_DB}")
        except Exception as e:
            print(f"Failed to ensure database: {e}")

    def create_collection(self, description: str = "", dim: int = int(DIM)) -> None:
        """Create the collection if it doesn't exist in the restapi database.

        Creates two vector fields for hybrid search:
        - sparse_vector: SPARSE_FLOAT_VECTOR for BM25/sparse retrieval on text
        - dense_vector: FLOAT_VECTOR for semantic/dense retrieval
        """
        # Ensure database exists
        self._ensure_database()

        if self.client.has_collection(self.collection):
            return

        schema = self.client.create_schema(
            auto_id=False,
            enable_dynamic_field=False,
            description=description,
        )

        schema.add_field(field_name="uri", datatype=DataType.VARCHAR, max_length=512, is_primary=True)
        schema.add_field(field_name="app_name", datatype=DataType.VARCHAR, max_length=128)
        schema.add_field(field_name="operation_id", datatype=DataType.VARCHAR, max_length=512)
        schema.add_field(field_name="summary", datatype=DataType.VARCHAR, max_length=1024)
        schema.add_field(field_name="dense_vector", datatype=DataType.FLOAT_VECTOR, dim=dim)
        schema.add_field(field_name="sparse_vector", datatype=DataType.SPARSE_FLOAT_VECTOR)
        schema.add_field(field_name="text", datatype=DataType.VARCHAR, max_length=10240, enable_analyzer=True)
        schema.add_field(field_name="parameters", datatype=DataType.JSON, nullable=True)
        schema.add_field(field_name="request", datatype=DataType.JSON, nullable=True)
        schema.add_field(field_name="response", datatype=DataType.JSON, nullable=True)
        schema.add_field(field_name="deprecated", datatype=DataType.BOOL, default_value=False)

        # Create indexes for both vector fields
        index_params = self.client.prepare_index_params()
        index_params.add_index(
            field_name="dense_vector",
            index_type="AUTOINDEX",
            metric_type="COSINE",
        )
        index_params.add_index(
            field_name="sparse_vector",
            index_type="SPARSE_INVERTED_INDEX",
            metric_type="BM25",
        )
        bm25_function = Function(
            name="text_bm25_emb",
            input_field_names=["text"],
            output_field_names=["sparse_vector"],
            function_type=FunctionType.BM25,
        )

        schema.add_function(bm25_function)

        self.client.create_collection(
            collection_name=self.collection,
            schema=schema,
            index_params=index_params,
        )
        print(f"Created collection: {self.collection}")

    def upsert(
            self,
            docs: list,
            dense_vectors: list[list[float]],
            texts: list[str],
    ) -> None:
        """Upsert documents with dense vectors. Sparse vectors are auto-generated via BM25 Function."""
        if not docs:
            return

        data = []
        for doc, dense_vec, text in zip(docs, dense_vectors, texts):
            meta = doc.metadata
            uri = make_uri(meta.get("path", ""), meta.get("method", ""))
            if uri.isspace():
                continue
            data.append({
                "uri": uri,
                "app_name": meta.get("app_name", ""),
                "operation_id": meta.get("operation_id", ""),
                "summary": meta.get("summary", ""),
                "dense_vector": dense_vec,
                "text": text,
                "parameters": meta.get("parameters"),
                "request": meta.get("request"),
                "response": meta.get("response"),
                "deprecated": meta.get("deprecated", False),
            })

        for i, row in enumerate(data):
            print(
                f"[{i}] uri={row['uri']} | app_name={row['app_name']} | operation_id={row['operation_id']} | text_len={len(row['text'])} | dense_vec_dim={len(row['dense_vector'])}")

        self.client.upsert(collection_name=self.collection, data=data)

    def search(
            self,
            query_text: str,
            limit: int = 6,
    ) -> list[dict]:
        """
        Search for similar vectors by text query in the current collection.
        Returns list of matches with uri, operation_id, summary, request, response, score.
        """
        query_vector = self.embedder.embed_query(query_text)

        results = self.client.search(
            collection_name=self.collection,
            data=[query_vector],
            anns_field="dense_vector",
            limit=limit,
            output_fields=["uri", "app_name", "operation_id", "summary", "text", "parameters", "request", "response",
                           "deprecated"],
        )

        matches = []
        for hits in results:
            for hit in hits:
                matches.append({
                    "uri": hit.get("uri", ""),
                    "app_name": hit.get("app_name", ""),
                    "operation_id": hit.get("operation_id", ""),
                    "summary": hit.get("summary", ""),
                    "parameters": hit.get("parameters"),
                    "request": hit.get("request"),
                    "response": hit.get("response"),
                    "deprecated": hit.get("deprecated", False),
                    "score": hit.get("distance", 0.0),
                    "text": hit.get("text", "")[:200],
                })
        return matches

    def hybrid_search(
            self,
            query_text: str,
            limit: int = 3,
    ) -> list[dict]:
        """
        Hybrid search combining dense and sparse (BM25) vectors in the current collection.

        Args:
            query_text: Query text for BM25 sparse search
            limit: Maximum number of results

        Returns list of matches with uri, operation_id, summary, score.
        """
        query_dense = self.embedder.embed_query(query_text)

        # Milvus hybrid search: search both dense and sparse fields
        spare_search_param = {
            "data": [query_text],
            "anns_field": "sparse_vector",
            "limit": limit,
            "param": {},
        }
        ann1 = AnnSearchRequest(**spare_search_param)

        search_param_1 = {
            "data": [query_dense],
            "anns_field": "dense_vector",
            "limit": limit,
            "param": {},
        }
        ann2 = AnnSearchRequest(**search_param_1)

        ranker = Function(
            name="rrf",
            input_field_names=[],  # Must be an empty list
            function_type=FunctionType.RERANK,
            params={
                "reranker": "rrf",
                "k": 100
            }
        )

        # ranker = Function(
        #     name="weight",
        #     input_field_names=[],  # Must be an empty list
        #     function_type=FunctionType.RERANK,
        #     params={
        #         "reranker": "weighted",
        #         "weights": [0.4, 0.6],
        #         "norm_score": True  # Optional
        #     }
        # )

        results = self.client.hybrid_search(
            collection_name=self.collection,
            reqs=[ann1, ann2],
            ranker=ranker,
            limit=limit,
            output_fields=["uri", "app_name", "operation_id", "summary", "text", "parameters", "request", "response", "deprecated"],
        )

        matches = []
        for hits in results:
            for hit in hits:
                matches.append({
                    "uri": hit.get("uri", ""),
                    "app_name": hit.get("app_name", ""),
                    "operation_id": hit.get("operation_id", ""),
                    "summary": hit.get("summary", ""),
                    "parameters": hit.get("parameters"),
                    "request": hit.get("request"),
                    "response": hit.get("response"),
                    "deprecated": hit.get("deprecated", False),
                    "score": hit.get("distance", 0.0),
                    "text": hit.get("text", ""),
                })
        return matches

    def get_app_list(self) -> list[dict]:
        """List all collections in the restapi database with their descriptions."""
        try:
            self.client.use_database(self.MILVUS_DB)
            collections = self.client.list_collections()
            # Build app_name -> collection_name map from fetch.yaml
            from config import get_fetch_apps
            app_map = {a["collection_name"]: a["app_name"] for a in get_fetch_apps()}

            result = []
            for coll in sorted(collections):
                # Get collection description from Milvus
                coll_info = self.client.describe_collection(coll)
                coll_desc = coll_info.get("description", "")
                result.append({
                    "collection": coll,
                    "app_name": app_map.get(coll, coll),
                    "description": coll_desc,
                })
            return result
        except Exception as e:
            print(f"Failed to get app list: {e}")
            return []
