# Mem0 + Gemini Personal Assistant

A learning project: a multi-user Streamlit chat assistant backed by Mem0 Cloud
for long-term memory and Gemini 2.5 Flash for chat replies.

## Setup

1. Copy `.env.example` to `.env` and fill in `MEM0_API_KEY` (from app.mem0.ai)
   and `GEMINI_API_KEY` (from Google AI Studio).
2. Install dependencies: `uv sync`
3. Run the app: `uv run streamlit run app.py`

## How it works

- Each browser session has a `User ID` field in the sidebar. All memory reads
  and writes are scoped to that `user_id` via Mem0 Cloud.
- On every chat turn, the app searches Mem0 for memories relevant to your
  message, shows Gemini's reply, and lists which memories were used under an
  expandable "Memories used" section.
- After each turn, the conversation is sent to Mem0's `add` endpoint, which
  automatically extracts and stores any new durable facts.
- The "Memory browser" tab lists, searches, and deletes memories for the
  current user directly — useful for seeing Mem0's API surface outside the
  chat flow. You can also view stored memories in the Mem0 dashboard at
  app.mem0.ai.

## Manual smoke test

1. In the sidebar, enter user id `alice`. In the Chat tab, tell the assistant
   a fact about yourself (e.g. "I'm allergic to nuts").
2. Switch the sidebar user id to `bob`. Ask the assistant if it knows
   anything about your allergies — it should NOT know, confirming memories
   are scoped per user.
3. Switch back to `alice` and ask about allergies again — it should recall
   the fact, and the "Memories used" expander under the reply should list it.
4. Open the "Memory browser" tab for `alice`, click "Show all memories", and
   confirm the allergy fact is listed.
5. Type "allerg" in the search box, click "Search", and confirm it's found.
6. Click "Delete" on that memory, then "Show all memories" again to confirm
   it's gone.
