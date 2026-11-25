# PileUp — spec (v1, 2026-11-24)

> Hackathon: Meta Muse Ember Hackathon (Cerebral Valley, solo, $5,000: 2× $2,500).
> Build window: Nov 23–Dec 2, 2026. Deadline: **Dec 2, 2026, 9:00 PM ET (8:00 PM CT)**.
> Repo: https://github.com/sunwen1983/pileup (public, MIT). **All code in this repo is written
> inside the window** (new-work-only rule; demo shows only window-built features).

## 1. Problem

Everyone has a messy pile: a flyer photo, a bill PDF, a voice memo, a chat screenshot,
a handwritten note. Each item holds a date, an amount, a person, something to do — but
getting that out means opening five apps and retyping everything. The pile grows because
extracting it costs more attention than ignoring it.

## 2. Solution (one sentence)

Dump the pile in; three Muse Ember agents turn it into one structured action plan.

## 3. Demo story (the 3-minute video)

Saturday morning pile, five real items:
1. School flyer photo — "Science Fair, Dec 12, 9 AM, bring a poster board"
2. Utility bill PDF — $86.40 due Dec 5
3. Voice memo (30 s) — "call the plumber back about the water heater"
4. Chat screenshot — landlord: "water heater flush done, check the tap aerator"
5. Handwritten note photo — "Amelia piano Mon 4:30, bring the blue book"

What the viewer sees: each item lands in the pile → the Classifier names it → the
Extractor pulls structured fields (dates, amounts, people, actions) → the Planner
dedupes, orders by date, flags the conflict (two things Dec 5), and files the actions
(calendar entry, reminder) through tools. Trace panel shows every agent call with
prompt + tokens + cost; a cost meter shows the whole pile cost under $0.05.

## 4. The three agents (all Muse Ember, muse-ember-1.0, Responses API)

| Agent | Input | Output |
|---|---|---|
| Classifier | one raw item (text / image / audio / PDF) | item type + which extractor path + confidence |
| Extractor | item + type | structured JSON: dates, amounts, people, actions, source span per field |
| Planner | all extracted items | ordered action plan: dedupe, date order, conflict flags, tool calls to file actions |

Why three agents instead of one prompt: the trace is the product — judges see the team
work, and each agent's prompt/token/cost is separately auditable for the submission.
Ember's native multimodality is the point: one model reads all four input kinds, no
separate OCR/ASR pipeline.

## 5. Architecture

```
Browser (upload pile, watch trace, read the plan)
  │  HTTPS
  ▼
PileUp server (Go; holds the Meta key server-side, never in the browser)
  ├─ Agent loop: Classifier → Extractor → Planner (Responses API, muse-ember-1.0)
  ├─ Trace + cost ledger: every call logged (model, prompt, input/output tokens, $)
  ├─ Budget guard: hard stop before $10 in-window Ember spend; live cost meter in UI
  └─ Tools via mcpgate (dependency, not hackathon work): mock Calendar + Reminders MCP
      backends — tools are real MCP calls, data is mock (no real account writes in demo)
```

- Backend holds the key: the browser never sees it (the account holds $149 from the
  October FixLens credits; a leaked key could drain it).
- Structured output: Ember returns JSON per a declared schema; a failed parse retries
  once, then the item is flagged "needs a human look" — never silently dropped.
- No dashboard-as-main-feature: the plan (actions) is the product; trace is evidence,
  not the point.

## 6. Scope

Must-have (M): pile upload (image / PDF / audio / text), 3-agent pipeline, structured
JSON per item, ordered plan with conflicts, tool calls through mcpgate, trace + cost
ledger, budget guard, 3-min video, submission pack.
Nice-to-have (N): public deploy for judges to try (fly.io); video input item; "add your
own item" in the demo.
Not doing: payments, real calendar/account writes, user accounts, mobile app, RAG,
a second pile type.

## 7. Milestones

| Slice | Dates | Exit |
|---|---|---|
| E1 Ember wiring | Nov 25–26 | one text + one image item end-to-end, tokens + $ recorded |
| E2 team + tools + UI | Nov 27–28 | full 5-item pile runs; plan + trace + cost meter visible |
| E3 harden (light) | Nov 29–30 | demo pile frozen and rehearsed 3×; in-window Ember spend ≤ $10 verified |
| E4 video + submit | Dec 1–2 | video < 3 min (screen + voiceover, no on-camera needed); repo + description + traces + usage screenshot submitted by Dec 2 8:00 PM CT |

SDS interview sprint starts Nov 29 — E3/E4 are deliberately light.

## 8. Budget guard (hard rule)

- In-window Ember spend must stay ≤ $10 (going over = disqualification; the submission
  screenshot measures Nov 23–Dec 2 Ember usage).
- Server enforces a hard cap and refuses new calls past it; UI shows a live meter.
- Dev/test calls are tiny (a probe is a few hundred tokens, <$0.001) and count toward
  the same window total — keep them few and small.
- Ember pricing: $0.10 / 1M input tokens, $0.50 / 1M output tokens.

## 9. Submission pack (per Participant Guide §08)

- Public GitHub repo (this one), project description
- 3-minute demo video (YouTube link; only window-built features)
- Prompt/token trace showing Muse Ember usage and amount spent
- Usage screenshot: Meta Model API Usage page, dates Nov 23–Dec 2, filtered to Muse Ember
- No Muse Code use → no trajectory JSON needed

## 10. Decisions (locked Nov 24)

- Fresh repo, window-only code (new-work-only rule; agent-bazaar M1 is NOT the submission).
- Mixed life-admin pile (not one vertical) — shows all four input kinds in one demo.
- mcpgate as a tool dependency; mock Calendar/Reminders backends.
- Video: screen recording + voiceover; no on-camera requirement stated.
- Ember via Responses API (`POST https://api.meta.ai/v1/responses`, model `muse-ember-1.0`,
  1M-token context, inputs text/image/video/audio/PDF).

## 11. Open (needs Wen)

- $10 credit claim form — **by Nov 25, 11:00 AM CT** (his account already exists from Oct).
- Demo pile: real items from his own pile (strongest) vs. public samples (fallback).
  Real items must contain no sensitive data (no account numbers, no IDs, no private mail).
