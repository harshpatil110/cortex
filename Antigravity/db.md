# Cortex Database Architecture & Configuration Spec (db.md)

This document establishes the exact schemas, structural configurations, indexing strategies, and multi-vector search architectures for **Cortex**. It governs both the relational storage layer (Supabase PostgreSQL) and the high-dimensional vector space (ChromaDB).

---

## 1. Database Stack Overview

Cortex implements a dual-engine storage model to handle structural, text-lexical, and high-dimensional semantic data in perfect sync.

              ┌────────────────────────────────────────┐
              │          INGESTION CONTROLLER          │
              └───────────────────┬────────────────────┘
                                  │
         ┌────────────────────────┴────────────────────────┐
         ▼                                                 ▼
┌─────────────────────────┐                       ┌─────────────────────────┐
│  SUPABASE (POSTGRESQL)  │                       │        CHROMADB         │
├─────────────────────────┤                       ├─────────────────────────┤
│ • Relational Integrity  │                       │ • Vector Embeddings     │
│ • JSONB Extracted Intel │                       │ • Cosine Similarity Space│
│ • BM25 Full-Text Search │                       │ • Dynamic Meta Filters  │
└─────────────────────────┘                       └─────────────────────────┘


---

## 2. Supabase PostgreSQL Relational Schema

Execute the following SQL DDL script to initialize the relational extensions, tables, constraints, security configurations, and indexing layers.

```sql
-- Enable necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Drop existing tables if rewriting
DROP TABLE IF EXISTS generated_learning_paths CASCADE;
DROP TABLE IF EXISTS entity_relationships CASCADE;
DROP TABLE IF EXISTS user_memories CASCADE;

-- 1. Core Memory Assets Table
CREATE TABLE user_memories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL, -- Isolated user boundary constraint
    content_type VARCHAR(50) NOT NULL, -- 'instagram_reel', 'pdf', 'screenshot', 'web_page'
    source_url TEXT,
    storage_path TEXT, -- Pointer to Supabase Storage Bucket binary payload
    
    -- Extracted creator profile data
    creator_metadata JSONB NOT NULL DEFAULT '{}'::jsonb, 
    -- Expected structure: { "handle": "@username", "platform": "instagram", "post_id": "XYZ" }

    -- Raw text outputs from localized extraction blocks
    raw_transcript TEXT DEFAULT '',
    ocr_extracted_text TEXT DEFAULT '',

    -- Structured AI Analysis (NVIDIA NIM Output Object)
    ai_summary JSONB NOT NULL DEFAULT '{}'::jsonb,
    -- Expected structural validation:
    -- {
    --   "abstract": "string",
    --   "key_takeaways": ["string"],
    --   "code_blocks": [{ "language": "string", "code": "string" }],
    --   "topics": ["string"],
    --   "difficulty_level": "Beginner" | "Intermediate" | "Advanced"
    -- }

    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL
);

-- 2. Knowledge Graph Relational Edges Table
CREATE TABLE entity_relationships (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_asset_id UUID NOT NULL REFERENCES user_memories(id) ON DELETE CASCADE,
    target_asset_id UUID NOT NULL REFERENCES user_memories(id) ON DELETE CASCADE,
    relationship_type VARCHAR(100) NOT NULL, -- 'shares_dependency', 'author_overlap', 'conceptual_link'
    weight REAL DEFAULT 1.0 NOT NULL, -- Relational mathematical score between nodes
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL,
    
    CONSTRAINT unique_node_pairing UNIQUE (source_asset_id, target_asset_id)
);

-- 3. Automated Syllabus / Curated Paths Table
CREATE TABLE generated_learning_paths (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    title VARCHAR(255) NOT NULL,
    topic_context VARCHAR(100) NOT NULL,
    
    -- Sequential course architecture map
    syllabus_structure JSONB NOT NULL DEFAULT '[]'::jsonb,
    -- Expected structural validation:
    -- [
    --   { "step": 1, "asset_id": "uuid", "module_title": "string", "objectives": ["string"] }
    -- ]

    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL
);

---
--- Performance Optimization Indexing Matrix
---

-- Multi-tenant User Boundary Fast Indexes
CREATE INDEX idx_memories_user ON user_memories(user_id);
CREATE INDEX idx_learning_paths_user ON generated_learning_paths(user_id);

-- Graph Edge Fast Traversal Indexes
CREATE INDEX idx_edges_source ON entity_relationships(source_asset_id);
CREATE INDEX idx_edges_target ON entity_relationships(target_asset_id);

-- Lexical Keyword Search Optimization Index (PostgreSQL Full-Text Search Vector)
CREATE INDEX idx_memories_lexical_search ON user_memories 
USING GIN (to_tsvector('english', raw_transcript || ' ' || ocr_extracted_text || ' ' || COALESCE((ai_summary->>'abstract'), '')));
3. ChromaDB Vector Database Configuration
ChromaDB acts as the dense semantic vector search repository. It tracks similarity scores to surface relevant elements missing exact keyword matches.

3.1. Collection Parameters
Collection Name: cortex_knowledge_nodes

Distance Metric: cosine (Cosine Similarity Matrix)

Embedding Space Scale: 1024 dimensions (optimized for high-density contextual text arrays generated by NVIDIA Retrieval Embedding NIM).

3.2. Data Payload Metadata Schema
Every vector transaction must be strictly bundled with metadata parameters to allow high-speed structural pre-filtering.

JSON
{
  "user_id": "string (UUID validation boundary)",
  "content_type": "string ('instagram_reel' | 'pdf' | 'screenshot' | 'web_page')",
  "created_at_timestamp": 1780694400
}
3.3. Document Serialization Protocol (Vector Target Input)
Before generating an embedding via the NVIDIA NIM layer, compile and serialize the document payload into the following unified text structure:

Plaintext
[TYPE]: instagram_reel
[CREATOR]: @dev_guru
[ABSTRACT]: A 60-second tutorial on integrating pgvector with Neon database using Drizzle ORM.
[TAKEAWAYS]: Enable pgvector extension in Postgres first. Use cosine distance for semantic similarity.
[TRANSCRIPT]: Alright guys today we're building vector stores using drizzle orm first open up your neon console...
[EXTRACTED VISUAL CODE]: import { vector } from 'drizzle-orm/pg-core'; npm i drizzle-orm pgvector
4. Hybrid Search Layer Blueprint (Reciprocal Rank Fusion)
To provide an optimal retrieval experience, the system combines Postgres lexical lookups and ChromaDB semantic lookups into a single result array via a Python-based Reciprocal Rank Fusion (RRF) utility.

Python
def calculate_rrf(postgres_rankings: list, chromadb_rankings: list, k: int = 60) -> list:
    """
    Calculates unified relevance rankings across sparse lexical indicators 
    and dense vector coordinates to eliminate result positioning discrepancies.
    """
    scores = {}
    
    # Process BM25 Keyword Rank
    for rank, asset_id in enumerate(postgres_rankings):
        scores[asset_id] = scores.get(asset_id, 0.0) + (1.0 / (k + (rank + 1)))
        
    # Process Dense Vector Similarity Rank
    for rank, asset_id in enumerate(chromadb_rankings):
        scores[asset_id] = scores.get(asset_id, 0.0) + (1.0 / (k + (rank + 1)))
        
    # Output sorted list of UUIDs matching descending score calculations
    return sorted(scores, key=scores.get, reverse=True)

<FollowUp label="Ready for skill.md" query="Please provide skill.md detailing all required AI and developer skil