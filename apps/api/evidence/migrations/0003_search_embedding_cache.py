import uuid
from django.db import migrations, models
import django.db.models.deletion
from pgvector.django import VectorField

class Migration(migrations.Migration):
    dependencies = [("evidence", "0002_evidence_embeddings"), ("core", "0001_initial")]
    operations = [
        migrations.CreateModel(name="SearchEmbeddingCache", fields=[
            ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
            ("query_hash", models.CharField(max_length=64)), ("embedding_model", models.CharField(max_length=120)),
            ("embedding", VectorField(dimensions=1536)), ("created_at", models.DateTimeField(auto_now_add=True)),
            ("organization", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="search_embedding_cache", to="core.organization")),
        ]),
        migrations.AddConstraint(model_name="searchembeddingcache", constraint=models.UniqueConstraint(fields=("organization", "query_hash", "embedding_model"), name="unique_tenant_search_embedding")),
    ]
