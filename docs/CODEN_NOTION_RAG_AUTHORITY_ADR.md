# ADR: Source-of-truth selection between GitHub and Notion for CODEN RAG

**Status:** Proposed, synthetic-only prototype. **Decision authority:** human-owned catalog + approved source revision.  
**Related:** Issues [#123](https://github.com/Mohamedalhindawan/coden-national-dpi/issues/123) (permission-aware RAG), [#143](https://github.com/Mohamedalhindawan/coden-national-dpi/issues/143) (Notion/Seam/Templates research).  
**Implementation:** `ai_factory/knowledge_authority.py`, `tests/test_knowledge_authority.py` in this PR.

## Problem / example

A design ADR might be approved as GitHub file `architecture/adr/015-dpi-consent.md` at commit C. A Notion page could contain a beautiful but outdated summary of the same ADR. The RAG assistant must **not** cite the summary as current authority just because Notion has a later `last_edited_time` or an attractive title.

The authoritative source is **per document and per domain**, not a blanket claim that GitHub always outranks Notion. For this synthetic exercise the approved GitHub ADR revision is designated canonical by an independently controlled registry.

## Proposed trust chain

```text
authenticated person/service + ACL/policy
             |
        versioned Authority Registry  <-- independent owner approval
             |
   source system + object ID + revision + SHA-256
             |
    verify exact current source bytes (NOT yet implemented)
             |
     ACL-filtered retrieval and source citation
             |
       evidence-based answer or abstain
```

### Truth selection rules

1. Resolve an approved source authority from an **authenticated and operator-controlled registry**; no Notion page or retrieved text may change its own authority.
2. Select an exact version + digest, not the newest edit timestamp. If approved source is deleted, revoked or superseded, refuse/abstain until an approved successor is registered.
3. Enforce the user's and agent's current ACL **before** retrieving content into LLM context. A Notion filtered view or a client's self-reported identity is not an ACL.
4. Compare content hashes with actual immutable source bytes and verify signatures/audit evidence where production requirements warrant it. The current prototype **only matches metadata**, so it returns `source_content_verified: false`.
5. Deny or refuse on conflicting versions, duplicate canonical candidates, stale summaries, missing source, approval ambiguity or unauthorized principal.
6. Cite `source system + immutable revision + document identifier + consulted chunk position` once a trusted retrieval connector actually provides this evidence. Never fabricate a citation.
7. Propagate revocation/deletion downstream to vector/search indexes and caches, and verify the source is no longer retrievable across tenants or with stale tokens.
8. Do not transfer real government, citizen, medical, identity or financial data to Notion, GitHub or external models without data classification, authorizations and residency assessment.

## Current implementation scope

`resolve_candidate(authority, records, principal)` validates **synthetic, strictly typed metadata** and emits only a candidate source revision or `blocked/deny`. It never emits page text or reads any connected account. Crucially, **`retrieval_authorized: false` and `authority_authenticated: false` remain constant**: a proposed ACL array supplied as a function argument is NOT a real IAM session.

Nine initial unit tests cover exact GitHub selection, stale Notion summaries, checksum/revision mismatch, denied principals, revoked and deleted authority, duplicate sources, unknown fields, cross-source conflict and bounded inputs.

## Required next milestones before a real RAG knowledge service

- Use official read-only Notion and GitHub connectors to create a source list, **without bulk importing private user data**. Do not silently mirror source bodies.
- Design a source authority registry with signed/approved revisions and system-specific identifiers, separate from source content and model prompts.
- Integrate current IAM/SSO principal and scope checks; tenant boundaries and group membership changes must be enforced before data retrieval.
- Implement actual hash checks on a protected read-only snapshot and version-stable source reads. Metadata comparison alone is insufficient.
- Implement retrieval with citations, ACL-preserving chunk boundaries, deletion/tombstone propagation and query-side audit without leaking request content to inappropriate logs.
- Run held-out multilingual Arabic/English RAG evaluations: abstention on missing content, contradictory ADR versions, prompt injection, unauthorized page, deletion and stale source.
- Put any Notion workspace database or cross-product sync behind an explicit approved destination and owner review. **GitHub issues remain the engineering task source of truth.**

## Non-goals

No Notion page created, no connected user content read, no production source selected, no automated GitHub merge, no external RAG service deployed. This ADR is a proposed engineering control, not legal or institutional authorization.
