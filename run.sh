#!/bin/bash
set -e
cd "$(dirname "$0")"

if [ -z "$(docker ps -q -f name=^neo4j-nlp$)" ]; then
    if [ -z "$(docker ps -aq -f name=^neo4j-nlp$)" ]; then
        echo "Error: no 'neo4j-nlp' container found. Create one first, e.g.:" >&2
        echo "  docker run -d --name neo4j-nlp -p 7474:7474 -p 7687:7687 -e NEO4J_AUTH=neo4j/password neo4j:latest" >&2
        exit 1
    fi
    echo "Starting Neo4j (neo4j-nlp) container..."
    docker start neo4j-nlp
    echo "Waiting for Neo4j to accept connections..."
    ready=0
    for i in $(seq 1 20); do
        .venv/bin/python -c "
from src.data_pipeline.graph_db import Neo4jGraphStore
import sys
sys.exit(0 if Neo4jGraphStore().connect() else 1)
" 2>/dev/null && { ready=1; break; }
        sleep 2
    done
    if [ "$ready" -ne 1 ]; then
        echo "Error: Neo4j did not become reachable within 40s. Check 'docker logs neo4j-nlp'." >&2
        exit 1
    fi
fi

.venv/bin/streamlit run app.py --server.port 8502
