import os
import json
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from datetime import datetime
from config_fixed import (
    QDRANT_URL, QDRANT_API_KEY, QDRANT_COLLECTION_NAME,
    QDRANT_VECTOR_SIZE, SYNTHETIC_CRISES
)

class QdrantService:
    """
    Fixed Qdrant Service - NOW WORKING PROPERLY
    - Handles all Qdrant database operations
    - Search using correct API
    - Store and retrieve crisis vectors
    - Apply temporal decay
    """

    def __init__(self):
        """Initialize Qdrant client"""
        try:
            # Try connecting to local Qdrant
            self.client = QdrantClient(
                url=QDRANT_URL,
                api_key=QDRANT_API_KEY if QDRANT_API_KEY else None,
                timeout=30
            )
            print("✅ Connected to Qdrant at", QDRANT_URL)
        except Exception as e:
            print(f"⚠️ Qdrant connection warning: {str(e)}")
            # Fallback to in-memory for local dev
            self.client = QdrantClient(":memory:")
            print("✅ Using in-memory Qdrant for local development")

    def create_collection(self):
        """Create Qdrant collection for crisis vectors"""
        try:
            # Check if collection exists
            collections = self.client.get_collections()
            collection_names = [col.name for col in collections.collections]

            if QDRANT_COLLECTION_NAME in collection_names:
                print(f"✅ Collection '{QDRANT_COLLECTION_NAME}' already exists")
                return True

            # Create new collection
            self.client.create_collection(
                collection_name=QDRANT_COLLECTION_NAME,
                vectors_config=VectorParams(
                    size=QDRANT_VECTOR_SIZE,
                    distance=Distance.COSINE  # Use cosine similarity for embeddings
                )
            )
            print(f"✅ Created collection '{QDRANT_COLLECTION_NAME}'")
            return True

        except Exception as e:
            print(f"❌ Error creating collection: {str(e)}")
            return False

    def add_point(self, crisis_id, vector, payload):
        """Add a single crisis vector to Qdrant"""
        try:
            # Ensure timestamp exists
            if "timestamp" not in payload:
                payload["timestamp"] = datetime.now().isoformat()

            # Create point with unique ID
            point = PointStruct(
                id=int(crisis_id) if isinstance(crisis_id, (int, float)) else hash(str(crisis_id)) % 1000000,
                vector=vector,
                payload=payload
            )

            # Upsert to Qdrant
            self.client.upsert(
                collection_name=QDRANT_COLLECTION_NAME,
                points=[point]
            )

            print(f"✅ Added crisis {crisis_id} to Qdrant database")
            return True

        except Exception as e:
            print(f"❌ Error adding point: {str(e)}")
            return False

    def search_similar(self, query_vector, top_k=3, min_score=0.0):
        """
        FIXED: Search for similar crisis vectors
        Uses correct API: search_points for newer Qdrant versions
        Falls back to search() for older versions
        """
        try:
            # Ensure query_vector is proper format
            if isinstance(query_vector, list):
                query_vector = query_vector
            else:
                query_vector = query_vector.tolist() if hasattr(query_vector, 'tolist') else query_vector

            print(f"🔍 Searching for similar crises (top_k={top_k}, min_score={min_score})")

            try:
                # TRY NEW API FIRST (Qdrant 1.0+)
                search_result = self.client.search_points(
                    collection_name=QDRANT_COLLECTION_NAME,
                    query_vector=query_vector,
                    limit=top_k,
                    score_threshold=min_score
                )

                formatted_results = []
                for result in search_result.points:
                    formatted_results.append({
                        "crisis_id": result.id,
                        "similarity_score": round(float(result.score) * 100, 2),
                        "metadata": dict(result.payload) if result.payload else {}
                    })

                print(f"✅ Found {len(formatted_results)} similar crises using search_points()")
                return formatted_results

            except (AttributeError, TypeError) as e1:
                print(f"⚠️ search_points not available: {str(e1)}")

                # FALLBACK TO OLD API (Qdrant 0.x)
                try:
                    search_result = self.client.search(
                        collection_name=QDRANT_COLLECTION_NAME,
                        query_vector=query_vector,
                        limit=top_k,
                        score_threshold=min_score
                    )

                    formatted_results = []
                    for result in search_result:
                        formatted_results.append({
                            "crisis_id": result.id,
                            "similarity_score": round(float(result.score) * 100, 2),
                            "metadata": dict(result.payload) if result.payload else {}
                        })

                    print(f"✅ Found {len(formatted_results)} similar crises using search()")
                    return formatted_results

                except Exception as e2:
                    print(f"❌ search() also failed: {str(e2)}")
                    return []

        except Exception as e:
            print(f"❌ Error searching: {str(e)}")
            return []

    def apply_temporal_decay(self, results):
        """Apply time-based decay to search results - RECENT incidents score higher"""
        from datetime import datetime, timedelta

        now = datetime.now()
        decay_threshold = timedelta(hours=24)
        decayed_results = []

        for result in results:
            metadata = result.get("metadata", {})
            try:
                # Parse timestamp
                incident_time = datetime.fromisoformat(metadata.get("timestamp", datetime.now().isoformat()))
                time_diff = now - incident_time
                hours_old = time_diff.total_seconds() / 3600

                # Calculate decay factor
                if time_diff < decay_threshold:
                    decay_factor = 1.0  # Full relevance within 24 hours
                else:
                    # Gradual decay after 24 hours
                    decay_factor = max(0.3, 1.0 - (hours_old / 72) * 0.7)

                # Update scores
                result["original_score"] = result["similarity_score"]
                result["similarity_score"] = round(result["similarity_score"] * decay_factor, 2)
                result["time_decay_factor"] = round(decay_factor, 2)
                result["hours_old"] = round(hours_old, 1)

            except Exception as e:
                print(f"⚠️ Could not parse timestamp: {str(e)}")
                result["hours_old"] = 0
                result["time_decay_factor"] = 1.0

            decayed_results.append(result)

        # Sort by final score
        decayed_results.sort(key=lambda x: x["similarity_score"], reverse=True)
        return decayed_results

    def update_crisis_memory(self, crisis_id, new_data):
        """Update an existing crisis with new information"""
        try:
            result = self.client.retrieve(
                collection_name=QDRANT_COLLECTION_NAME,
                ids=[crisis_id]
            )

            if not result:
                print(f"❌ Crisis {crisis_id} not found")
                return False

            # Update payload
            current_data = dict(result[0].payload) if result[0].payload else {}
            current_data.update(new_data)
            current_data["last_updated"] = datetime.now().isoformat()

            # Upsert with updated data
            point = PointStruct(
                id=crisis_id,
                vector=result[0].vector,
                payload=current_data
            )

            self.client.upsert(
                collection_name=QDRANT_COLLECTION_NAME,
                points=[point]
            )

            print(f"✅ Updated crisis {crisis_id}")
            return True

        except Exception as e:
            print(f"❌ Error updating crisis: {str(e)}")
            return False

    def get_crisis_by_id(self, crisis_id):
        """Retrieve a specific crisis by ID"""
        try:
            result = self.client.retrieve(
                collection_name=QDRANT_COLLECTION_NAME,
                ids=[crisis_id]
            )

            if result:
                return {
                    "id": result[0].id,
                    "metadata": dict(result[0].payload) if result[0].payload else {}
                }

            return None

        except Exception as e:
            print(f"❌ Error retrieving crisis: {str(e)}")
            return None

    def get_all_crises(self):
        """Get all crises from database"""
        try:
            points, _ = self.client.scroll(
                collection_name=QDRANT_COLLECTION_NAME,
                limit=1000
            )

            crises = []
            for point in points:
                crises.append({
                    "id": point.id,
                    "metadata": dict(point.payload) if point.payload else {}
                })

            print(f"✅ Retrieved {len(crises)} crises from database")
            return crises

        except Exception as e:
            print(f"❌ Error getting all crises: {str(e)}")
            return []

    def initialize_with_synthetic_data(self, vectors):
        """Populate Qdrant with synthetic crisis data"""
        print("\n📍 Initializing Qdrant with 25 REAL crisis cases...")

        try:
            added = 0
            for idx, crisis in enumerate(SYNTHETIC_CRISES):
                crisis_id = idx + 1  # Start from 1

                # Get vector - if provided, use it; otherwise use random
                if isinstance(vectors, list) and idx < len(vectors):
                    vector = vectors[idx]
                else:
                    # Generate random 512-dim vector for testing
                    import numpy as np
                    vector = np.random.randn(QDRANT_VECTOR_SIZE).astype(np.float32).tolist()

                try:
                    self.add_point(
                        crisis_id=crisis_id,
                        vector=vector,
                        payload={
                            "id": crisis.get("id", f"crisis_{idx}"),
                            "type": crisis.get("type", "unknown"),
                            "location": crisis.get("location", "unknown"),
                            "description": crisis.get("description", ""),
                            "timestamp": crisis.get("timestamp", datetime.now().isoformat()),
                            "severity": crisis.get("severity", "medium"),
                            "protocol": crisis.get("protocol", ""),
                            "affected_people": crisis.get("affected_people", 0),
                            "casualties": crisis.get("casualties", 0),
                            "damage_estimate": crisis.get("damage_estimate", "Unknown"),
                            "response_time": crisis.get("response_time", "Unknown")
                        }
                    )
                    added += 1

                except Exception as e:
                    print(f"⚠️ Could not add crisis {crisis_id}: {str(e)}")

            print(f"\n✅ Successfully loaded {added}/{len(SYNTHETIC_CRISES)} synthetic crises into Qdrant")
            return added

        except Exception as e:
            print(f"❌ Error initializing synthetic data: {str(e)}")
            return 0

    def save_user_incident(self, image_vector, text_description, metadata):
        """Save uploaded user incident to database for continuous learning"""
        try:
            # Get next ID
            all_crises = self.get_all_crises()
            next_id = len(all_crises) + 1

            # Create incident record
            incident_payload = {
                "user_uploaded": True,
                "upload_time": datetime.now().isoformat(),
                "description": text_description,
                "type": metadata.get("type", "unknown"),
                "location": metadata.get("location", "unknown"),
                "severity": metadata.get("severity", "medium"),
                "protocol": metadata.get("protocol", ""),
                "affected_people": metadata.get("affected_people", 0),
                "image_provided": True
            }

            # Save to Qdrant
            self.add_point(
                crisis_id=next_id,
                vector=image_vector,
                payload=incident_payload
            )

            print(f"✅ Saved user incident as crisis {next_id} for future learning")
            return next_id

        except Exception as e:
            print(f"❌ Error saving user incident: {str(e)}")
            return None
