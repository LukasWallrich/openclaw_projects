# Crossroads

Crossroads is a zero-build prototype for an adaptive spatial lobby that routes people into persistent video-call rooms. It is designed for events where attendance is unpredictable and pre-assigned breakout groups would be brittle.

## What the prototype demonstrates

- Topic streets crossed with conversation-intent avenues
- Visible room occupancy and target capacity
- Adaptive room opening at different attendance levels
- Interest-aware routing toward under-filled rooms
- A consented "doorway" that offers a captioned conversation pulse before entry
- A Google Meet handoff that leaves the participant visibly parked at the room
- Keyboard, mouse, touch, responsive, and reduced-motion support

The deployed prototype uses synthetic participants and captioned conversation pulses. It contains no real meeting links, accounts, analytics, backend, or captured audio.

## Production architecture

1. Keep this static client and room configuration.
2. Replace the synthetic scenario state with ephemeral Supabase Realtime presence.
3. Put attendee access and room-link delivery behind a small authenticated edge function.
4. Let people visibly stand at a room's doorway; expose only a room-controlled text pulse by default.
5. Open Google Meet in a new tab; do not embed or proxy video.
6. Retain a static, accessible room list as the event fallback.

Literal Meet-audio previews are intentionally out of scope. The real-time Google Meet Media API is currently a restricted Developer Preview that requires the project and all conference participants to be enrolled. Relaying room audio would also require explicit, legible consent from everyone in that room.

## Run locally

Open `index.html` directly or serve this folder with any static HTTP server.

For the interaction tests:

```sh
npm install
npm test
```

Set `CROSSROADS_URL` to run the same tests against a deployment.

## License

MIT. See `LICENSE`.
