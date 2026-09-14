# Crossroads

Crossroads is a zero-build prototype for an adaptive spatial lobby that routes people into persistent video-call rooms. It is designed for events where attendance is unpredictable and pre-assigned breakout groups would be brittle.

## What the prototype demonstrates

- Topic streets crossed with conversation-intent avenues
- Visible room occupancy and target capacity
- Adaptive room opening at different attendance levels
- Interest-aware routing toward under-filled rooms
- A Google Meet handoff that leaves the participant visibly parked at the room
- Keyboard, mouse, touch, responsive, and reduced-motion support

The deployed prototype uses synthetic participants and contains no real meeting links, accounts, analytics, or backend.

## Production architecture

1. Keep this static client and room configuration.
2. Replace the synthetic scenario state with ephemeral Supabase Realtime presence.
3. Put attendee access and room-link delivery behind a small authenticated edge function.
4. Open Google Meet in a new tab; do not embed or proxy video.
5. Retain a static, accessible room list as the event fallback.

## Run locally

Open `index.html` directly or serve this folder with any static HTTP server.

For the interaction tests:

```sh
npm install
npm test
```

## License

MIT. See `LICENSE`.
