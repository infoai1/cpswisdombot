# Brainstorm: Reference-Centric RAG for 145 Books

## Problem Statement

When Maulana Wahiduddin Khan cites a hadith or Quran verse in his books, he often includes the reference (e.g., "Sahih Bukhari, Hadith 6018" or "Quran 2:255"). Currently, LightRAG:

1. Chunks the text without preserving reference context
2. Returns synthesized answers without source citations
3. Loses the connection between content and its Islamic references

**Goal**: When a user asks about a hadith, the agent should return:
- The teaching/explanation from the books
- The original reference (e.g., "Bukhari 6018", "Quran 5:32")
- Optionally, the book/page where Maulana discussed it

---

## Solution Approaches

### Approach 1: Reference-Aware Chunking (Pre-Processing)

**Concept**: Modify PDF processing to detect and preserve references within chunks.

**Implementation**:
```
1. When processing PDFs, use regex to detect reference patterns:
   - Hadith: "Bukhari \d+", "Muslim \d+", "Tirmidhi", etc.
   - Quran: "Surah .+ \d+:\d+", "(\d+:\d+)", "Quran \d+:\d+"

2. When chunking, ensure reference stays with its context:
   - If chunk boundary would split a reference from its explanation, adjust
   - Prepend chunk with: "[REF: Bukhari 6018]" marker

3. Store reference as chunk metadata in LightRAG
```

**Pros**:
- Preserves references at source
- No runtime overhead
- Works with existing LightRAG

**Cons**:
- Requires re-processing all 145 PDFs
- Complex regex for Arabic/English mixed text
- Reference might be sentences away from explanation

---

### Approach 2: Reference Extraction Database (Parallel System)

**Concept**: Build a separate reference index alongside LightRAG.

**Implementation**:
```
Database Schema:
├── references
│   ├── id
│   ├── type (hadith/quran/scholarly)
│   ├── citation (e.g., "Bukhari 6018")
│   ├── source_book (e.g., "Age-of-Peace.pdf")
│   ├── page_number
│   ├── context_text (surrounding paragraph)
│   └── embedding (for similarity search)

Query Flow:
1. User asks: "What does Islam say about kindness to neighbors?"
2. LightRAG returns: "The Prophet taught that one should be kind..."
3. Post-process: Search reference DB for related citations
4. Return: "As mentioned in Sahih Bukhari 6018..."
```

**Pros**:
- Clean separation of concerns
- Can add references without re-indexing LightRAG
- Searchable reference catalog

**Cons**:
- Additional database to maintain
- Requires initial extraction pass over all PDFs
- Matching LightRAG output to reference DB is fuzzy

---

### Approach 3: Structured Document Format (Pre-Indexing)

**Concept**: Convert PDFs to structured JSON before LightRAG ingestion.

**Implementation**:
```json
{
  "book": "The-Age-of-Peace.pdf",
  "chapter": "Chapter 3: Peace in Daily Life",
  "page": 42,
  "sections": [
    {
      "content": "The Prophet Muhammad taught that kindness to neighbors is essential...",
      "references": [
        {"type": "hadith", "source": "Bukhari", "number": "6018"},
        {"type": "quran", "verse": "4:36"}
      ]
    }
  ]
}
```

**Text sent to LightRAG**:
```
[Book: The Age of Peace, Page 42, Chapter 3]
[Refs: Bukhari 6018, Quran 4:36]
The Prophet Muhammad taught that kindness to neighbors is essential...
```

**Pros**:
- References preserved in chunk text
- LLM sees references naturally in context
- Structured and parseable

**Cons**:
- Significant preprocessing effort
- Requires accurate PDF parsing
- May increase chunk size

---

### Approach 4: Two-Stage RAG with Reference Lookup

**Concept**: First retrieve content, then lookup references separately.

**Implementation**:
```python
async def search_with_references(query: str):
    # Stage 1: Normal LightRAG query
    content = await query_lightrag(query)

    # Stage 2: Extract any references mentioned in response
    references = extract_references(content)  # regex extraction

    # Stage 3: Enrich with full citation info
    enriched_refs = await lookup_references(references)

    return {
        "answer": content,
        "citations": enriched_refs
    }

def extract_references(text: str) -> list:
    patterns = [
        r'Bukhari\s*(\d+)',
        r'Muslim\s*(\d+)',
        r'Quran\s*(\d+:\d+)',
        r'Surah\s+[\w-]+\s*(\d+:\d+)',
    ]
    # Extract all matches
    ...
```

**Pros**:
- Works with current LightRAG output
- No re-indexing needed
- Incremental improvement

**Cons**:
- Only finds references already in LightRAG response
- Can't find references LightRAG didn't retrieve
- Post-hoc rather than native

---

### Approach 5: LLM-Based Reference Extraction (Preprocessing)

**Concept**: Use LLM to extract and tag references during PDF processing.

**Implementation**:
```
For each PDF page:
1. Send to LLM: "Extract all hadith and Quran references from this text.
   Format: {reference: 'Bukhari 123', context: 'surrounding text'}"

2. Build reference index from LLM output

3. When chunking for LightRAG, embed reference markers:
   "<<REF:bukhari:6018>> The Prophet said... <<END_REF>>"
```

**Pros**:
- LLM understands context better than regex
- Can handle variations in citation format
- Extracts semantic relationships

**Cons**:
- Expensive (LLM calls for 145 books)
- Potential for hallucinated references
- Requires verification pass

---

## Recommended Hybrid Approach

Combine Approaches 1 + 2 + 4 for best results:

### Phase 1: Build Reference Index (One-Time)
```
1. Process all 145 PDFs with regex + LLM extraction
2. Create reference database:
   - All hadith citations with source book/page
   - All Quran verses with source book/page
   - Full-text search on reference context
3. Store in SQLite or Redis for fast lookup
```

### Phase 2: Enhance Chunk Text (Re-Index LightRAG)
```
1. Modify chunking to prepend reference markers:
   "[REFS: Bukhari 6018, Quran 4:36] Original text..."

2. Re-index all documents into LightRAG

3. References now appear naturally in RAG responses
```

### Phase 3: Post-Process Agent Response
```python
@function_tool
async def search_knowledge(context: RunContext, question: str):
    # Get LightRAG response
    result = await query_lightrag_cached(question)

    # Extract references from response
    refs = extract_islamic_references(result)

    # Enrich with full citation details from reference DB
    if refs:
        enriched = await get_reference_details(refs)
        result += f"\n\nReferences: {format_references(enriched)}"

    return result
```

---

## Reference Pattern Library

Common patterns to detect in Maulana's books:

### Hadith Collections
```regex
# Sahih Bukhari
(Sahih\s+)?Bukhari[,:]?\s*(Hadith\s*)?\d+
(Sahih\s+)?Bukhari[,:]?\s*Vol\.?\s*\d+[,:]?\s*(Book\s*)?\d+[,:]?\s*(Hadith\s*)?\d+

# Sahih Muslim
(Sahih\s+)?Muslim[,:]?\s*(Hadith\s*)?\d+

# Other Collections
Tirmidhi[,:]?\s*\d+
Abu\s+Dawud[,:]?\s*\d+
Ibn\s+Majah[,:]?\s*\d+
Nasa'i[,:]?\s*\d+
Muwatta\s+Malik[,:]?\s*\d+
Musnad\s+Ahmad[,:]?\s*\d+
```

### Quran Verses
```regex
# Standard format
Quran\s*\d+:\d+(-\d+)?
Surah\s+[\w\s-]+[,:]?\s*\d+:\d+

# Arabic names
Al-Baqarah\s*\d+:\d+
An-Nisa\s*\d+:\d+
Al-Ma'idah\s*\d+:\d+

# Parenthetical
\(\d+:\d+(-\d+)?\)
```

### Scholarly References
```regex
# Islamic scholars
Ibn\s+Kathir
Al-Ghazali
Ibn\s+Taymiyyah

# Books
Tafsir\s+[\w\s]+
Fiqh\s+[\w\s]+
```

---

## Implementation Priority

### Quick Win (1-2 days)
- Add regex-based reference extraction to `search_knowledge` tool
- Append detected references to response
- No re-indexing needed

### Medium Effort (1 week)
- Build reference extraction script for all PDFs
- Create SQLite reference database
- Add reference lookup to agent

### Full Solution (2-3 weeks)
- LLM-assisted reference extraction for all 145 books
- Re-index LightRAG with reference-enhanced chunks
- Build searchable reference catalog
- Add "search by reference" feature (e.g., "What does Bukhari 6018 say?")

---

## Example User Interactions

### Current Behavior
```
User: "What does Islam teach about neighbors?"
Agent: "Maulana Wahiduddin Khan teaches that treating neighbors
       with kindness is a fundamental Islamic principle..."
```

### With Reference-Centric RAG
```
User: "What does Islam teach about neighbors?"
Agent: "Maulana Wahiduddin Khan teaches that treating neighbors
       with kindness is a fundamental Islamic principle. As stated
       in Sahih Bukhari (Hadith 6018), the Prophet Muhammad said
       'He is not a believer whose neighbor is not safe from his harm.'

       📖 Reference: Bukhari 6018
       📚 Source: The Age of Peace, Page 42"
```

---

## Next Steps

1. **Analyze sample PDFs**: Check how references are formatted in actual books
2. **Build regex patterns**: Create comprehensive pattern library
3. **Test extraction**: Run extraction on 5-10 sample books
4. **Evaluate accuracy**: Verify extracted references are correct
5. **Design database schema**: Plan reference storage
6. **Implement MVP**: Quick-win extraction in agent

---

## Questions to Resolve

1. Are references consistently formatted across all 145 books?
2. Are references in English, Arabic, or mixed?
3. Should we verify extracted references against hadith databases?
4. How to handle references that span multiple lines?
5. Should the agent cite book/page, or just the Islamic reference?
