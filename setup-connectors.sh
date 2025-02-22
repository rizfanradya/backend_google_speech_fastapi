#!/bin/bash

echo "Menunggu Kafka Connect siap..."
sleep 10

echo "Menambahkan PostgreSQL Connector..."
curl -X POST -H "Content-Type: application/json" --data @debezium_postgres_connector.json http://connect:8083/connectors

echo "Menambahkan Elasticsearch Connector..."
curl -X POST -H "Content-Type: application/json" --data @kafka_es_connector.json http://connect:8083/connectors

echo "✅ Semua Kafka Connector telah ditambahkan!"
