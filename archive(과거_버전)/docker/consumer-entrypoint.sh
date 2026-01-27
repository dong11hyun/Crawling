#!/bin/bash
set -e
echo "Starting Kafka Consumer..."
echo "   Type: $CONSUMER_TYPE"
echo "   Kafka: $KAFKA_BOOTSTRAP_SERVERS"
if [ "$CONSUMER_TYPE" = "postgres" ]; then
    echo "Starting PostgreSQL Consumer..."
    python -m src.kafka_client.consumer_postgres
elif [ "$CONSUMER_TYPE" = "opensearch" ]; then
    echo "Starting OpenSearch Consumer..."
    python -m src.kafka_client.consumer_opensearch
else
    echo "Unknown CONSUMER_TYPE: $CONSUMER_TYPE"
    exit 1
fi
