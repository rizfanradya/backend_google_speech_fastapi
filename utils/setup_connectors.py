import httpx
import asyncio
from .config import KAFKA_CONNECT_URL


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
