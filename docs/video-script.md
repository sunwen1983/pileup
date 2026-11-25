# PileUp — demo video script (3:00)

Submission video: 3 minutes, YouTube URL. Screen recording (his Mac,
Chrome, PileUp UI) + generated voiceover, cut together with ffmpeg.
The demo must show only functionality built in the hackathon window
(Nov 23–Dec 2); the mock transport is never shown as live.

## The pile (5 items, the Saturday-morning story)

1. School flyer photo — Science Fair, Dec 12, 9 AM, bring a poster board
2. Utility bill PDF — $86.40 due Dec 5
3. Voice memo — call the plumber back about the water heater
4. Chat screenshot — landlord: water heater flush done, check the tap aerator
5. Handwritten note — Amelia piano Mon 4:30, bring the blue book

The plan orders actions by date (plumber Nov 27, piano book Nov 30,
bill Dec 5, fair Dec 12) and splits them: dated actions become calendar
events, undated ones become reminders. This pile has no same-date
overlap, so the planner reports no conflicts — the conflict flagging
is a capability, not something this pile triggers. Target pile cost:
under $0.05 (the on-screen meter shows the real number).

## Beats

| Time | On screen | Narration |
| --- | --- | --- |
| 0:00–0:12 | The 5 pile items in the UI | "Saturday morning. Five things landed in a pile — a school flyer, a utility bill, a voice memo, a chat from my landlord, and a handwritten note. None of them is a task yet." |
| 0:12–0:30 | Close-ups of the items | "Each one hides a date, an amount, or something I have to do. Reading them all and making a plan takes longer than doing the chores." |
| 0:30–0:50 | PileUp UI, empty state | "PileUp takes the whole pile and turns it into a plan. Three Ember agents do the work: one classifies each item, one pulls out the dates, amounts and actions, and one orders everything and flags conflicts." |
| 0:50–1:35 | Upload the 5 items (or Load demo pile), click Run; traces appear live | "I drop the pile in and hit run. Watch the trace: every agent call, its tokens, and its cost, live. Nothing is hidden." |
| 1:35–2:20 | The plan, ordered by date; the Executed section (calendar events created for dated actions, reminders for undated ones) | "Here's the plan, ordered by date. Dated actions became calendar events; the ones without a date became reminders — all through real M C P tools." |
| 2:20–2:45 | The cost meter | "The whole pile cost less than five cents. Ember charges ten cents per million input tokens and fifty cents per million output — at this price, the messy pile is a rounding error." |
| 2:45–3:00 | PileUp title + repo URL | "PileUp. Dump the pile in, get a plan out. Built with Muse Ember, in the hackathon window." |

## Recording (his Mac)

- Start the server first: `MODEL_API_KEY=... PILEUP_TRANSPORT=live python3 -m pileup.server` (from `~/pileup`), keep the Terminal window open.
- Record with Cmd+Shift+5 (whole screen, or the Chrome window). Do one
  clean take per beat if needed; cuts hide the joins.
- Click through the UI yourself following the beats, or let Mila drive the
  browser while you record. Narration is added in the edit — no live
  talking needed while recording.
- Send the recording file to Mila after; she cuts it to 3:00, lays the
  voiceover over it, and hands back the finished video for YouTube.

## Edit plan

- Voiceover: generated narration (the text in the table above), one track
  per beat in `demo/voiceover/beat1.mp3` … `beat7.mp3` (Helio voice).
  Durations verified Nov 24: 11.9 / 7.2 / 12.2 / 8.4 / 11.4 / 10.1 / 5.8 s —
  each fits its beat window, total ~67 s of narration in the 180 s video.
  Beat 6 ("less than five cents") is the estimate to re-check against the
  real live-run cost; re-record that beat alone if the meter says otherwise.
- Cuts: trim dead time (uploads, agent waits) but keep the traces visible
  long enough to read; the cost meter must be legible in the final frame.
- Export: 1080p, H.264, under 3:00. Verify the final file plays end to
  end before uploading.
