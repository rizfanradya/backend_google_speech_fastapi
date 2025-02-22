#!/bin/bash

echo "Menunggu Kafka Connect siap..."
while ! curl -s http://connect:8083/connectors; do
  echo "⏳ Kafka Connect belum siap, menunggu 5 detik..."
  sleep 5
done
echo "✅ Kafka Connect sudah siap!"

echo "Menambahkan PostgreSQL Connector..."
curl -X POST -H "Content-Type: application/json" --data '{
  "name": "postgres-connector",
  "config": {
    "connector.class": "io.debezium.connector.postgresql.PostgresConnector",
    "database.hostname": "postgres",
    "database.port": "5432",
    "database.user": "google_speech",
    "database.password": "O8IfbjmMtQek06kBsy8WzveVxu0GLGMo5RExBZadbn5AUA0UQh",
    "database.dbname": "google_speech",
    "database.server.name": "postgres_server",
    "database.include.list": "public",
    "plugin.name": "pgoutput",
    "slot.name": "debezium_slot",
    "table.include.list": "public.role",
    "topic.prefix": "postgres",
    "key.converter": "org.apache.kafka.connect.json.JsonConverter",
    "value.converter": "org.apache.kafka.connect.json.JsonConverter",
    "heartbeat.interval.ms": "10000"
  }
}' http://connect:8083/connectors

echo "Menambahkan Elasticsearch Connector..."
curl -X POST -H "Content-Type: application/json" --data '{
  "name": "es-connector",
  "config": {
    "connector.class": "io.confluent.connect.elasticsearch.ElasticsearchSinkConnector",
    "connection.url": "http://elasticsearch:9200",
    "tasks.max": "1",
    "topics": "postgres.public.role",
    "key.ignore": "true",
    "schema.ignore": "true",
    "type.name": "_doc",
    "name": "es-connector",
    "behavior.on.null.values": "delete",
    "ignore_key": "true"
  }
}' http://connect:8083/connectors

echo "✅ Semua Kafka Connector telah ditambahkan!"
