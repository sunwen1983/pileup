# PileUp

Dump the pile in; get a plan out.

PileUp takes a messy pile — a flyer photo, a bill PDF, a voice memo, a chat
screenshot, a handwritten note — and turns it into one structured action plan.
Three Muse Ember agents do the work: one classifies each item, one extracts
structured fields (dates, amounts, people, actions), one plans (dedupes, orders,
flags conflicts, files the actions through tools). Every call is traced with
prompt, tokens and cost.

Built for the **Meta Muse Ember Hackathon** (Cerebral Valley, solo, Nov 23–Dec 2,
2026). All code in this repo was written inside the hackathon window.

## Status

- Nov 24: spec written (`PLAN.md`), repo created. E1 (Ember wiring) next.

## Run it

Requires a Meta Model API key in `MODEL_API_KEY` (never commit one).

```bash
# E1 probe (one Ember call, tokens + cost printed)
python3 scripts/ember_probe.py
```

See `PLAN.md` for the full spec, milestones and budget guard.
