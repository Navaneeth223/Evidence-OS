import re
from collections import defaultdict
from django.db import connection
from evidence.models import EvidenceAtom

STOP_WORDS = {"about", "after", "again", "also", "among", "been", "being", "does", "from", "have", "into", "more", "most", "only", "other", "over", "should", "that", "their", "there", "these", "they", "this", "those", "through", "under", "using", "what", "when", "where", "which", "while", "with", "your", "company"}

def _tokens(text):
    return {word for word in re.findall(r"[a-z0-9]+", text.lower()) if len(word) > 2 and word not in STOP_WORDS}

class SearchService:
    """Tenant-filtered keyword, semantic, and hybrid retrieval over verified evidence."""
    @staticmethod
    def keyword_search(organization, query, limit=100):
        terms = _tokens(query)
        if not terms: return []
        if connection.vendor == "postgresql":
            from django.contrib.postgres.search import SearchQuery, SearchRank, SearchVector
            vector = SearchVector("title", "content", config="simple")
            search = SearchQuery(query, search_type="websearch", config="simple")
            rows = EvidenceAtom.objects.filter(organization=organization, verification_status=EvidenceAtom.Verification.VERIFIED).annotate(search_rank=SearchRank(vector, search)).filter(search_rank__gt=0).order_by("-search_rank").select_related("document")[:limit]
            return [(float(atom.search_rank) / (float(atom.search_rank) + 0.05), atom) for atom in rows]
        rows = EvidenceAtom.objects.filter(organization=organization, verification_status=EvidenceAtom.Verification.VERIFIED).only("id", "title", "content", "source_locator", "document_id")[:2000]
        scored = []
        for atom in rows:
            content_terms = _tokens(f"{atom.title} {atom.content}")
            overlap = len(terms & content_terms)
            if overlap: scored.append((overlap / len(terms), atom))
        return sorted(scored, key=lambda item: item[0], reverse=True)[:limit]

    @staticmethod
    def semantic_search(organization, query, limit=50):
        if connection.vendor != "postgresql": return []
        from pgvector.django import CosineDistance
        from ai.embeddings import get_embedding_provider
        vector = get_embedding_provider().embed_many([query])[0]
        queryset = EvidenceAtom.objects.filter(organization=organization, verification_status=EvidenceAtom.Verification.VERIFIED, embedding__isnull=False)
        rows = queryset.annotate(distance=CosineDistance("embedding", vector)).order_by("distance").select_related("document")[:limit]
        return [(max(0.0, 1.0 - float(atom.distance)), atom) for atom in rows]

    @classmethod
    def hybrid_search(cls, organization, query, limit=8):
        keyword = cls.keyword_search(organization, query, limit=200)
        try: semantic = cls.semantic_search(organization, query, limit=100)
        except Exception:
            # A temporarily unavailable embedding provider must not erase usable keyword matches.
            semantic = []
        scores = defaultdict(float); atoms = {}
        for score, atom in keyword:
            atoms[atom.id] = atom; scores[atom.id] += 0.45 * score
        for similarity, atom in semantic:
            atoms[atom.id] = atom; scores[atom.id] += 0.55 * similarity
        ranked = sorted(((score, atoms[atom_id]) for atom_id, score in scores.items()), key=lambda item: item[0], reverse=True)
        return [(score, atom) for score, atom in ranked if score >= 0.12][:limit]
