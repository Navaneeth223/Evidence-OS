import logging
from django.db.backends.signals import connection_created
from django.dispatch import receiver

logger = logging.getLogger(__name__)

@receiver(connection_created)
def register_pgvector_adapter(sender, connection, **kwargs):
    if connection.vendor != "postgresql": return
    try:
        from pgvector.psycopg import register_vector
        register_vector(connection.connection)
    except Exception as exc:
        # During the initial migration the extension is not installed yet; the migration registers it after creation.
        logger.debug("pgvector adapter registration deferred: error_type=%s", type(exc).__name__)
