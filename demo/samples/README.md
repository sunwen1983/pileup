# Demo sample pile (fallback)

These five files are **generated samples**, not the user's real items.
They exist so the demo runs end-to-end even if no real pile is provided.
If real items are available, use those instead — the story is the same,
only the files change.

- `science-fair-flyer.png` — school flyer: Science Fair, Dec 12, 9 AM,
  bring a poster board
- `utility-bill.pdf` — city utility bill: $86.40 due Dec 5, account ending 4417
- `voice-memo.mp3` — voice memo: call the plumber back about the water
  heater before Friday
- `landlord-chat-screenshot.png` — landlord: water heater flush done,
  check the tap aerator
- `piano-note.png` — handwritten note: Amelia piano Mon 4:30, bring the
  blue book

`../pile-samples.json` is the manifest (id, kind, mime, file). The UI
accepts these files directly via the file picker. Verified Nov 24: the
full 5-item sample pile runs through `/api/run` (mock transport) with
plan + tool execution intact.
