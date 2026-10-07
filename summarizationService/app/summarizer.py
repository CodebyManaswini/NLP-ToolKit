"""
Chunking + map-reduce summarization logic.

distilbart-cnn-12-6 has a ~1024 token input limit. Long documents are
split into chunks, each summarized independently (the "map" step),
and — if there was more than one chunk — the chunk summaries are
concatenated and summarized once more (the "reduce" step) to produce
one coherent final summary.
"""

WORDS_PER_CHUNK = 700  # conservative margin under the ~1024 token limit


def chunk_text(text: str, words_per_chunk: int = WORDS_PER_CHUNK) -> list[str]:
    words = text.split()
    if len(words) <= words_per_chunk:
        return [text]

    chunks = []
    for i in range(0, len(words), words_per_chunk):
        chunk_words = words[i : i + words_per_chunk]
        chunks.append(" ".join(chunk_words))
    return chunks


def summarize_document(text: str, summarizer, max_length: int = 130, min_length: int = 30) -> dict:
    """
    summarizer: a callable matching the HF summarization pipeline signature —
    summarizer(text, max_length=, min_length=, do_sample=) -> [{"summary_text": ...}]
    """
    chunks = chunk_text(text)

    chunk_summaries = []
    for chunk in chunks:
        result = summarizer(chunk, max_length=max_length, min_length=min_length, do_sample=False)
        chunk_summaries.append(result[0]["summary_text"].strip())

    if len(chunk_summaries) == 1:
        final_summary = chunk_summaries[0]
    else:
        combined = " ".join(chunk_summaries)
        result = summarizer(combined, max_length=max_length, min_length=min_length, do_sample=False)
        final_summary = result[0]["summary_text"].strip()

    return {
        "summary": final_summary,
        "chunk_count": len(chunks),
        "chunk_summaries": chunk_summaries if len(chunks) > 1 else None,
    }