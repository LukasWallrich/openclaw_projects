# Crossroads — six-model frontend brief

Create one visually opinionated, interactive frontend draft for **Crossroads**, an open orchestration layer for networking at an online research conference. Conversations happen in persistent Google Meet rooms; this frontend handles discovery, visible self-reported presence, low-pressure approach, and the handoff.

## Product idea

- About 100 registered researchers; actual attendance is unpredictable.
- Rooms are persistent themed conversations, not pre-assigned breakout groups.
- Nine rooms combine three topic families with three intentions: bring a puzzle, compare methods, find collaborators.
- Room supply and occupancy cues adapt to attendance. A useful target is 3–5 people per conversation.
- Visitors can approach a room before joining. Show a **consented doorway pulse**: a short synthetic caption/summary and clear visible-listener state. Never imply covert audio interception.
- “Take me somewhere” should recommend an under-filled relevant room without silently joining it.
- Joining opens/simulates a Google Meet handoff in a new tab. This prototype contains no real Meet links.
- All people, occupancy and conversation snippets are clearly synthetic.

## Required interactions

1. Inspect at least six named rooms and see occupancy before joining.
2. Select or approach a room and see who is there plus its current prompt/pulse.
3. Enter a doorway/listening state, then join or return.
4. Try “Take me somewhere”.
5. Change between at least two attendance scenarios so room supply or status visibly adapts.
6. Work with mouse/touch and at 390px wide. Use semantic buttons, visible focus, and reduced-motion support.

## Delivery constraints

- Write one self-contained `index.html` in the assigned folder.
- No external assets, frameworks, fonts, CDNs, build steps, real meeting links, network requests, analytics, or secrets.
- Inline CSS and JavaScript are fine. Runtime must work from `file://` and GitHub Pages.
- Do not modify any other file, folder, git state, or the existing Crossroads prototype.
- Do not copy the current prototype’s visual system. The point is an independent design direction.
- Label the page with the provided concept name and model attribution.
- Aim for a polished reviewable draft, not production architecture.
