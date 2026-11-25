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
# Tests (stdlib unittest, no live API call)
python3 -m unittest discover -s tests

# E1 probe (one Ember call, tokens + cost printed)
python3 scripts/ember_probe.py
```

The probe uses `MODEL_API_KEY` when set; on this VM it falls back to the
registered Meta Model API connection. Note: this VM's egress currently
blocks api.meta.ai, so live calls run off-VM (fly.io / laptop) until that
changes — the client, pipeline and tests are transport-agnostic.

See `PLAN.md` for the full spec, milestones and budget guard.
