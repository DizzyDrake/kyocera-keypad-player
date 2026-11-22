# WQB322 — metadata-only duplicate-song candidates

Offline source derivative of WQA321. Adds `duplicate_candidates.py` and six tests, without connecting to GUI, invoking Gemma, scanning audio or deleting files. Call `candidate_groups(data['tracks'])` on a validated Playlist Desk metadata object. Results are *review-required candidate pairs*, not proof of duplicate recordings. Title+artist+duration within 2 seconds is an assistant-selected heuristic, not an owner rule. Missing duration/title/artist is not inferred. Album/version differences can create false positives; same recording with inconsistent tags can create false negatives. Never auto-delete based on this heuristic.

This is a small deterministic foundation for future owner-requested local-model review. A model-based audio-content comparison is NOT implemented. Parent WQA321 ZIP unchanged; no Windows GUI test or owner data.
