"""Subject-scoped keyword + dense retrieval with SQLite vectors and explicit sufficiency gating."""
import math
import re
from collections import Counter

from study.models import ModelError


def terms(text):
    return re.findall(r"\w+", text.casefold())


def cosine(a, b):
    if len(a) != len(b):
        raise ValueError("embedding model changed; reindex before comparing")
    denominator = math.sqrt(sum(x*x for x in a)*sum(x*x for x in b))
    return sum(x*y for x, y in zip(a, b, strict=True))/denominator if denominator else 0


def lexical_ranking(units, query):
    words = set(terms(query))
    docs = [Counter(terms(u["text"])) for u in units]
    avg_len = sum(sum(d.values()) for d in docs)/max(1, len(docs)) or 1
    frequencies = {w: sum(w in d for d in docs) for w in words}
    scores = []
    for doc in docs:
        size = sum(doc.values())
        scores.append(sum(math.log(1+(len(docs)-frequencies[w]+0.5)/(frequencies[w]+0.5))*
                          doc[w]*2.2/(doc[w]+1.2*(0.25+0.75*size/avg_len)) for w in words if doc[w]))
    return [(units[i]["id"], scores[i]) for i in sorted(range(len(units)), key=lambda i: scores[i],
                                                     reverse=True) if scores[i] > 0]


def fuse(units, rankings, count):
    by_id = {u["id"]: u for u in units}
    scores = Counter()
    for ranking in rankings:
        for rank, (ident, _) in enumerate(ranking):
            if ident in by_id:  # Hydrate only live SQL units; never trust stale external metadata.
                scores[ident] += 1/(60+rank+1)
    return [{**by_id[ident], "retrieval_score": score} for ident, score in scores.most_common(count)]


def retrieve(units, query, vector, count=8):
    """In-memory reference path for isolated tests and deliberate small-corpus use."""
    dense = sorted([(u["id"], cosine(vector, u["embedding"])) for u in units],
                   key=lambda r: r[1], reverse=True)
    return fuse(units, [lexical_ranking(units, query)[:40], dense[:40]], count)


def retrieve_evidence(units, query, model_client, settings):
    if not units:
        return []
    if any(u["embedding_model"] != model_client.roles["embedding"] for u in units):
        raise ModelError("Embedding model changed. Re-upload documents to rebuild their local index.")
    vector = model_client.embed([query], query=True)[0]
    return retrieve(units, query, vector, settings.retrieval_top_k)
