from django.db import migrations
from django.db import models
from django.contrib.postgres.indexes import GinIndex
from django.contrib.postgres.search import SearchVector
from pgvector.django import HnswIndex, VectorField

def enable_vector_extension(apps, schema_editor):
    if schema_editor.connection.vendor == "postgresql":
        schema_editor.execute("CREATE EXTENSION IF NOT EXISTS vector")

def create_hnsw_index(apps, schema_editor):
    if schema_editor.connection.vendor == "postgresql":
        schema_editor.execute("CREATE INDEX evidence_embedding_hnsw ON evidence_evidenceatom USING hnsw (embedding vector_cosine_ops) WITH (m = 16, ef_construction = 64)")

def drop_hnsw_index(apps, schema_editor):
    if schema_editor.connection.vendor == "postgresql":
        schema_editor.execute("DROP INDEX IF EXISTS evidence_embedding_hnsw")

def create_fts_index(apps, schema_editor):
    if schema_editor.connection.vendor == "postgresql":
        schema_editor.execute("CREATE INDEX evidence_content_gin ON evidence_evidenceatom USING gin (to_tsvector('simple', coalesce(title, '') || ' ' || coalesce(content, '')))")

def drop_fts_index(apps, schema_editor):
    if schema_editor.connection.vendor == "postgresql":
        schema_editor.execute("DROP INDEX IF EXISTS evidence_content_gin")

class Migration(migrations.Migration):
    dependencies = [("evidence", "0001_initial")]
    operations = [
        migrations.RunPython(enable_vector_extension, migrations.RunPython.noop),
        migrations.AddField(model_name="evidenceatom", name="embedding", field=VectorField(blank=True, dimensions=1536, null=True)),
        migrations.AddField(model_name="evidenceatom", name="embedding_model", field=models.CharField(blank=True, max_length=120)),
        migrations.AddField(model_name="evidenceatom", name="embedding_hash", field=models.CharField(blank=True, max_length=64)),
        migrations.SeparateDatabaseAndState(
            database_operations=[migrations.RunPython(create_hnsw_index, drop_hnsw_index)],
            state_operations=[migrations.AddIndex(model_name="evidenceatom", index=HnswIndex(name="evidence_embedding_hnsw", fields=["embedding"], m=16, ef_construction=64, opclasses=["vector_cosine_ops"]))],
        ),
        migrations.SeparateDatabaseAndState(
            database_operations=[migrations.RunPython(create_fts_index, drop_fts_index)],
            state_operations=[migrations.AddIndex(model_name="evidenceatom", index=GinIndex(SearchVector("title", "content", config="simple"), name="evidence_content_gin"))],
        ),
    ]
