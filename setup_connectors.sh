#!/bin/bash

echo "Menunggu Kafka Connect siap..."

MAX_RETRIES=12
RETRY_COUNT=0

while ! curl -s http://connect:8083/connectors | grep -q "\[\|\{"; do
  echo "⏳ Kafka Connect belum siap, menunggu 5 detik..."
  sleep 5
  RETRY_COUNT=$((RETRY_COUNT+1))

  if [ "$RETRY_COUNT" -ge "$MAX_RETRIES" ]; then
    echo "❌ Kafka Connect tidak siap setelah 1 menit. Keluar..."
    exit 1
  fi
done

echo "✅ Kafka Connect sudah siap!"

if curl -s http://connect:8083/connectors | grep -q "postgres-connector"; then
  echo "⚠️  PostgreSQL Connector sudah ada, tidak perlu menambahkan ulang."
else
  echo "🛠 Menambahkan PostgreSQL Connector..."
  RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" -X POST -H "Content-Type: application/json" --data '{
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
  }' http://connect:8083/connectors)

  if [ "$RESPONSE" -eq 201 ]; then
    echo "✅ PostgreSQL Connector berhasil ditambahkan!"
  else
    echo "❌ Gagal menambahkan PostgreSQL Connector. Response Code: $RESPONSE"
  fi
fi

if curl -s http://connect:8083/connectors | grep -q "es-connector"; then
  echo "⚠️  Elasticsearch Connector sudah ada, tidak perlu menambahkan ulang."
else
  echo "🛠 Menambahkan Elasticsearch Connector..."
  RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" -X POST -H "Content-Type: application/json" --data '{
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
  }' http://connect:8083/connectors)

  if [ "$RESPONSE" -eq 201 ]; then
    echo "✅ Elasticsearch Connector berhasil ditambahkan!"
  else
    echo "❌ Gagal menambahkan Elasticsearch Connector. Response Code: $RESPONSE"
  fi
fi

echo "🎉 Semua Kafka Connector telah diperiksa dan ditambahkan jika diperlukan!"
