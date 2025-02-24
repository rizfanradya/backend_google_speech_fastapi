import httpx
import asyncio
from .config import (
    KAFKA_CONNECT_URL,
    DB_HOSTNAME,
    DB_PORT,
    DB_USER,
    DB_PASSWORD,
    DB_NAME,
    ELASTICSEARCH_URL,
)


async def setup_connectors():
    async with httpx.AsyncClient() as client:
        print("🔍 Menjalankan setup_connectors()...")

        for _ in range(12):
            try:
                response = await client.get(KAFKA_CONNECT_URL, timeout=5)
                if response.status_code == 200:
                    print("✅ Kafka Connect sudah siap!")
                    break
            except httpx.RequestError:
                print("⏳ Kafka Connect belum siap, menunggu 5 detik...")
            await asyncio.sleep(5)
        else:
            print("❌ Kafka Connect tidak siap setelah 1 menit. Keluar...")
            return

        print(
            "✅ Kafka Connect sudah siap! Menunggu 10 detik sebelum menambahkan connector...")
        await asyncio.sleep(10)

        response = await client.get(KAFKA_CONNECT_URL, timeout=10)
        existing_connectors = response.json()

        if "postgres-connector" in existing_connectors:
            print("⚠️ PostgreSQL Connector sudah ada, tidak perlu menambahkan ulang.")
        else:
            print("🛠 Menambahkan PostgreSQL Connector...")
            postgres_payload = {
                "name": "postgres-connector",
                "config": {
                    "connector.class": "io.debezium.connector.postgresql.PostgresConnector",
                    "database.hostname": DB_HOSTNAME,
                    "database.port": DB_PORT,
                    "database.user": DB_USER,
                    "database.password": DB_PASSWORD,
                    "database.dbname": DB_NAME,
                    "database.server.name": "postgres_server",
                    "database.include.list": "public.role,public.user",
                    "plugin.name": "pgoutput",
                    "slot.name": "debezium_slot",
                    "topic.prefix": "postgres",
                    "key.converter": "org.apache.kafka.connect.json.JsonConverter",
                    "value.converter": "org.apache.kafka.connect.json.JsonConverter",
                    "heartbeat.interval.ms": "10000",
                    "snapshot.mode": "always"
                }
            }
            try:
                response = await client.post(KAFKA_CONNECT_URL, json=postgres_payload, timeout=30)
                if response.status_code == 201:
                    print("✅ PostgreSQL Connector berhasil ditambahkan!")
                else:
                    print(
                        f"❌ Gagal menambahkan PostgreSQL Connector. Response Code: {response.status_code}, Response: {response.text}")
            except httpx.RequestError as e:
                print(
                    f"❌ Gagal menghubungi Kafka Connect saat menambahkan PostgreSQL Connector. Error: {e}")

        if "es-connector" in existing_connectors:
            print("⚠️ Elasticsearch Connector sudah ada, tidak perlu menambahkan ulang.")
        else:
            print("🛠 Menambahkan Elasticsearch Connector...")
            es_payload = {
                "name": "es-connector",
                "config": {
                    "connector.class": "io.confluent.connect.elasticsearch.ElasticsearchSinkConnector",
                    "connection.url": ELASTICSEARCH_URL,
                    "tasks.max": "1",
                    "topics.regex": "postgres.public.role|postgres.public.user",
                    "key.ignore": "true",
                    "schema.ignore": "true",
                    "type.name": "_doc",
                    "name": "es-connector",
                    "behavior.on.null.values": "delete",
                    "ignore_key": "true"
                }
            }
            try:
                response = await client.post(KAFKA_CONNECT_URL, json=es_payload, timeout=30)
                if response.status_code == 201:
                    print("✅ Elasticsearch Connector berhasil ditambahkan!")
                else:
                    print(
                        f"❌ Gagal menambahkan Elasticsearch Connector. Response Code: {response.status_code}, Response: {response.text}")
            except httpx.RequestError as e:
                print(
                    f"❌ Gagal menghubungi Kafka Connect saat menambahkan Elasticsearch Connector. Error: {e}")
