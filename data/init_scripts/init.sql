ALTER SYSTEM SET wal_level = logical;
ALTER SYSTEM SET max_replication_slots = 4;
ALTER SYSTEM SET max_wal_senders = 4;
SELECT pg_reload_conf();

SELECT * FROM pg_create_logical_replication_slot('debezium_slot', 'pgoutput');
