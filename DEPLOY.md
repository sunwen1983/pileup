# Deploy — PileUp on fly.io

## Why fly.io

This VM's egress proxy blocks `api.meta.ai` (CONNECT 403; worked Nov 2,
blocked since). The PileUp server must run somewhere with normal egress to
call Ember. fly.io is that place (its API is reachable from here, and the
server is stdlib-only Python, so the image is tiny).

## One-time setup (needs Wen)

1. Install flyctl (his Mac: `brew install flyctl`; or
   `curl -L https://fly.io/install.sh | sh`).
2. `flyctl auth login` (his fly.io account).
3. In this repo: `flyctl launch --name pileup-ember --region dfw --no-deploy`
   (accepts the `fly.toml` here; if the name is taken, pick another and
   update `fly.toml`).
4. Set the key — **never commit it, never paste it in chat**:
   `flyctl secrets set MODEL_API_KEY=<his Meta Model API key>`.
   Any key on his Meta account works; the account holds $149 from October.
5. `flyctl deploy`.
6. Verify: `curl https://pileup-ember.fly.dev/api/health` should return
   `{"ok": true, "transport": "live"}`.

## Live check

From any machine that can reach `api.meta.ai` (fly.io, his Mac — not this VM):

```bash
PILEUP_TRANSPORT=live MODEL_API_KEY=... python3 scripts/ember_probe.py
```

Or open the deployed UI and run the demo pile; the cost meter must stay
under $10 of in-window Ember spend (see PLAN.md §8).

## Notes

- `fly.toml` sets `PILEUP_TRANSPORT=live`; the server binds `0.0.0.0:$PORT`
  (fly.io sets `PORT=8080`).
- Traces land in `traces/` on the machine (ephemeral on fly.io); the
  `/api/run` response already carries the full ledger, so export it from
  there for the submission.
- If fly.io is unavailable, the fallback is running the server on his Mac
  (same commands, `PORT=8000`).
