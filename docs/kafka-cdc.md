# Change data capture with Kafka

Change data capture (CDC) streams row-level changes — inserts, updates, and
deletes — from a source database into Kafka topics, so downstream systems can
react to changes without polling the source.

A common setup pairs a CDC connector (for example a Debezium-style source
connector or a database-native connector) with Kafka Connect. The connector
reads the source database's transaction log, which means changes are captured
in order and with low latency, and the source database takes almost no extra
query load compared with polling.

Schema Registry matters in CDC pipelines because schemas evolve. Producers
register each event schema, consumers validate against it, and compatibility
rules (backward, forward, or full) decide whether a schema change is safe to
deploy before it can break a consumer in production.

Downstream, a sink connector or a stream processor such as ksqlDB or Spark
Structured Streaming applies the change stream to the target system. For
database migrations, the pattern is: take a consistent snapshot of the source,
replay the CDC stream to catch up, validate with reconciliation checks, then
cut reads over to the target while the stream keeps writes in sync until the
source is decommissioned.

Exactly-once semantics are achievable within Kafka, but most migration
pipelines are designed to be idempotent and at-least-once instead, because the
target apply step is simpler to reason about and safe to replay.
