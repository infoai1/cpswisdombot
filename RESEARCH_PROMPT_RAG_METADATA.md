# Deep Research Prompt: RAG Source Attribution & Metadata Problem

## Background Context

I am building a voice AI assistant that uses **LightRAG** (by HKUDS) for retrieval-augmented generation over a knowledge base of 23 PDF books by Maulana Wahiduddin Khan. The system works well for answering questions, but I need to **display clickable links to source PDFs** in the response.

### Current Problem

LightRAG returns only the synthesized answer text. It does NOT return:
- Source document filename (e.g., "The-Age-of-Peace.pdf")
- Page numbers where the information was found
- Chapter or section names
- Any structured metadata

### What I Need

When a user asks "What is peace in Islam?", I want the response to include:
```json
{
  "answer": "Peace in Islam means...",
  "sources": [
    {"book": "The-Age-of-Peace.pdf", "page": 42, "chapter": "Chapter 3"},
    {"book": "Islam-and-Peace.pdf", "page": 15, "chapter": "Introduction"}
  ]
}
```

This would allow me to create clickable links like:
`📚 Source: The Age of Peace, Page 42`

---

## Research Questions

### Part 1: LightRAG Specific Solutions

1. **LightRAG Architecture Analysis**
   - How does LightRAG store documents internally? (nano_vectordb, networkx graph, etc.)
   - When documents are indexed, what metadata is preserved vs discarded?
   - Is source document information stored in the vector database but just not returned?
   - What is the exact data structure of a stored chunk/node in LightRAG?

2. **LightRAG Code Modification**
   - Where in the LightRAG codebase is the query response constructed?
   - Which files/functions would need modification to return source metadata?
   - Is there a way to modify the query endpoint to return both answer AND source documents?
   - Has anyone successfully forked LightRAG to add this feature? (Check GitHub forks)

3. **LightRAG Indexing Options**
   - Can I add custom metadata during document insertion/indexing?
   - Is there a way to tag each chunk with its source filename during PDF processing?
   - Would re-indexing with modified chunk metadata solve the problem?

4. **LightRAG Issues & Community**
   - GitHub Issue #468 requested this feature but was closed as "not planned" - WHY?
   - GitHub Issue #137 discusses source referencing - any workarounds mentioned?
   - Are there any forks or PRs that implement metadata return?
   - What did the LightRAG maintainers suggest as alternatives?

### Part 2: Alternative RAG Frameworks with Source Attribution

Research these alternatives that DO support source attribution:

5. **LlamaIndex**
   - Does LlamaIndex return source document metadata with queries?
   - How does it handle PDF source attribution?
   - Can it be a drop-in replacement for LightRAG?
   - Performance comparison: LlamaIndex vs LightRAG for 23 PDFs

6. **LangChain**
   - How does LangChain handle document source tracking?
   - Does it preserve PDF filename and page numbers?
   - What retriever types support metadata return?
   - Integration complexity vs LightRAG

7. **Haystack by deepset**
   - Source attribution capabilities in Haystack 2.0
   - PDF processing with page-level metadata
   - Performance and accuracy comparison

8. **Ragas / RAGatouille / Chroma**
   - Do any of these support structured metadata return?
   - Which is best for PDF-based knowledge bases?

9. **GraphRAG (Microsoft)**
   - Does GraphRAG preserve source information better than LightRAG?
   - Is it suitable for a 23-PDF knowledge base?
   - Setup complexity comparison

### Part 3: Hybrid & Workaround Solutions

10. **Hybrid Approach**
    - Can I use LightRAG for retrieval but add a separate metadata lookup?
    - Could I hash the retrieved text and look up source in a separate database?
    - Is there a way to inject source information into the LLM prompt?

11. **Post-Processing Heuristics**
    - Can I match retrieved text against original PDFs to find source?
    - How accurate would fuzzy string matching be for source attribution?
    - Are there any tools that do "reverse PDF search" given a text chunk?

12. **Re-indexing Strategy**
    - If I modify my PDF preprocessing to prepend "SOURCE: filename.pdf" to each chunk, would LightRAG preserve this?
    - Could I structure my documents so source info appears in the answer naturally?

---

## Specific Technical Questions

### For Code Analysis:
```
1. In LightRAG's query flow, where is the final response text assembled?
2. What database/storage does LightRAG use and does it support metadata fields?
3. Is there a retrieval step that returns document IDs before synthesis?
4. Can I intercept the retrieval results before they go to the LLM?
```

### For Alternative Evaluation:
```
1. Which RAG framework has the BEST source attribution out-of-the-box?
2. What's the migration effort from LightRAG to [alternative]?
3. Will I lose the graph-based retrieval benefits of LightRAG?
4. Are there any hosted RAG services with built-in source tracking?
```

### For Implementation:
```
1. If I fork LightRAG, what's the minimal code change needed?
2. Can I create a wrapper API that enriches LightRAG responses with source info?
3. Is there a metadata sidecar approach that doesn't require modifying LightRAG?
```

---

## Constraints & Requirements

- **Must work with**: 23 PDF books (Islamic wisdom literature)
- **Current stack**: LightRAG API on port 9621, LiveKit voice agents, FastAPI server
- **Performance requirement**: Query response < 2 seconds
- **Budget**: Prefer open source / self-hosted solutions
- **Skill level**: Non-coder, need clear step-by-step solutions or developer-ready specs
- **Risk tolerance**: LOW - don't want to break working system

---

## Desired Research Output

Please provide:

1. **Feasibility Assessment**: Is modifying LightRAG realistic, or should I switch frameworks?

2. **Recommended Solution**: The best path forward with effort/benefit analysis

3. **Code Examples**: If modification is suggested, provide specific code snippets or file locations

4. **Migration Guide**: If switching RAG frameworks, provide step-by-step migration plan

5. **Comparison Table**:
   | Framework | Source Attribution | Graph Support | PDF Handling | Migration Effort |
   |-----------|-------------------|---------------|--------------|------------------|
   | LightRAG  | ❌                | ✅            | ✅           | N/A              |
   | LlamaIndex| ?                 | ?             | ?            | ?                |
   | etc.      | ?                 | ?             | ?            | ?                |

6. **Risk Analysis**: What could go wrong with each approach?

7. **Demo/POC**: Any working examples or repositories demonstrating source attribution in RAG?

---

## Keywords for Research

```
LightRAG source attribution
LightRAG document metadata
LightRAG citation
RAG source tracking
RAG PDF page reference
LlamaIndex source nodes
LangChain document metadata
Haystack document store metadata
GraphRAG source attribution
RAG provenance tracking
PDF chunk metadata preservation
Vector database metadata return
nano_vectordb metadata
```

---

## Reference Links

- LightRAG GitHub: https://github.com/HKUDS/LightRAG
- Issue #468 (metadata request - closed): https://github.com/HKUDS/LightRAG/issues/468
- Issue #137 (source referencing): https://github.com/HKUDS/LightRAG/issues/137
- LightRAG Paper: arXiv:2410.05779

---

## Success Criteria

The research is successful if it answers:

1. **Can I get source PDFs from LightRAG?** → Yes (how) / No (why)
2. **Should I switch to a different RAG?** → Yes (which one) / No (workaround)
3. **What's the implementation effort?** → Hours / Days / Weeks
4. **Will it break my current system?** → Yes (risks) / No (safe path)
