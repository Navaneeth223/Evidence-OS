from django.core.management.base import BaseCommand
from evidence.models import DocumentVersion
from evidence.tasks import embed_evidence_for_version

class Command(BaseCommand):
    help = "Queue evidence vectors for the configured embedding model."

    def handle(self, *args, **options):
        count = 0
        for version_id in DocumentVersion.objects.values_list("id", flat=True).iterator(chunk_size=500):
            embed_evidence_for_version.delay(str(version_id))
            count += 1
        self.stdout.write(self.style.SUCCESS(f"Queued embedding refresh for {count} document versions."))
