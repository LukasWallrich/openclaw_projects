# Klettersteige page — how to change it

`index.html` is **generated**. Never edit it: the next build silently discards your work.

```
routes.json   <- the only data file. Edit this.
build.py      <- python3 build.py   (regenerates index.html)
photos/       <- local images, if any
index.html    <- GENERATED OUTPUT
```

Workflow for any change: edit `routes.json` → `python3 build.py` → open `index.html` and
**look at it** → commit and push. GitHub Pages serves it about a minute later at
<https://lukaswallrich.github.io/openclaw_projects/projects/klettersteige-ch/>.

## Adding or replacing a photo

Image fields on a route object:

```json
"img":       "photos/tierbergli-1.jpg",
"imgs":      ["photos/tierbergli-1.jpg", "photos/tierbergli-2.jpg"],
"imgCredit": "Lukas Wallrich · personal photos",
"imgPage":   "https://commons.wikimedia.org/wiki/File:Sulzfluh.jpg",
"imgPos":    "center 30%"
```

- **`imgs`** (array) — two or more photos become a **carousel**: it cross-fades every 3.5 s,
  gets clickable dots, and pauses on hover/focus and while the lightbox is open. Respects
  `prefers-reduced-motion`. Set `img` to the first one as well, for anything reading a single image.
- **`img`** (string) — used when there is no `imgs`. Absolute URL **or** repo-relative path.
- **`imgCredit`** — renders as the chip on the image and as the lightbox caption. Always fill it in.
- **`imgPage`** — provenance only. Optional for own photos.
- **`imgPos`** — optional `object-position` for the card crop, e.g. `"center 30%"` to bias the
  visible band upward. Only needed to rescue an awkward crop; see below.

### Landscape, please

Cards crop to **16:9**, so a portrait photo loses most of its height in the thumbnail.
The lightbox always shows the full uncropped frame, so nothing is lost — but the card
still reads better with landscape. **Prefer landscape shots.** If a portrait one has to go
in and the crop lands badly, nudge it with `imgPos` rather than editing CSS.

**For a photo Lukas supplies**, put the file in `photos/` and use a relative path.
Name files `<route-id>-<n>.jpg` (the route's `id`) so they stay matchable.
Resize to about 1600 px on the long edge and strip EXIF before committing —
phone originals are 4–8 MB each and will bloat the repo:

```bash
sips -Z 1600 -s format jpeg in.jpg --out photos/<route-id>-1.jpg   # macOS, also drops most EXIF
exiftool -all= photos/<route-id>-1.jpg                              # if available, to be sure
```

**For a replacement from the web**, prefer Wikimedia Commons (`upload.wikimedia.org`
thumb URLs) — freely licensed and stable. `scratch_images.py` in the session scratchpad
shows the Commons search-and-pick approach if you need it in bulk.

After any image change, verify **every** image still resolves — a broken hotlink is
invisible in the source:

```js
// paste in the browser console on the built page
[...document.querySelectorAll('.card img')].forEach(i => i.loading = 'eager');
setTimeout(() => console.log('broken:',
  [...document.querySelectorAll('.card img')]
    .filter(i => i.complete && !i.naturalWidth)
    .map(i => i.closest('.card').dataset.id)), 8000);
```

## The lightbox

Every card image is clickable and opens a full-screen viewer showing the photo **uncropped**
(`object-fit: contain`). It is automatic — there is nothing to configure per route. It picks up
whatever is in `img` / `imgs`, and the caption comes from the route name plus `imgCredit`.

Behaviour, if you touch it: opens on click, Enter or Space (each `.shot` is `tabindex="0"
role="button"`); arrows and swipe move between a carousel's photos; Escape, the backdrop, or
the × closes it and returns focus to the card. Arrows and the counter hide for single-image
routes. Opening pauses the carousel and locks page scroll; closing restores both.

Two traps if you edit the overlay CSS:

- **No `backdrop-filter` on the full-screen overlay.** Blurring a 62-card page behind it is
  expensive enough to lock the renderer. The background is 97% opaque; the blur bought nothing.
- Keep `.lb img` on `object-fit: contain`. `cover` would reintroduce the exact crop the
  lightbox exists to escape.

## Two things that are easy to get wrong

1. **The repo is public.** Anything in `photos/` is public, regardless of the page's
   `noindex`. Do not commit photos with people in them, or anything Lukas has not
   cleared for that.
2. **`noindex` must survive.** The `<meta name="robots" content="noindex,…">` is emitted
   by `build.py`. Don't remove it.

## Other fields worth knowing

- `driveMin` / `driveKm` / `driveTo` — road routing from Bergdietikon. If a new route is
  added, these must be filled in or the card shows "—" and it sorts last.
- `type: "secured"` — marks a route that is a cable-protected path rather than a true
  ferrata (no continuous cable to clip). Renders a red badge.
- `thin: true` — marks a route whose figures could not be verified. Renders a warning.
- `grade` drives the colour band automatically; the highest K-number in the string wins.
- `doneFor` / `doneDate` — `doneFor: ["Lukas"]` pre-marks the route as Done for anyone who
  enters that name, without needing a click. `doneDate` is a record for us, not rendered.
  Server state still wins: if that person later un-marks it, their click sticks.

## Verifying a change

`index.html` is heavy enough that the browser extension sometimes reports the tab as frozen
right after load; it is usually just busy. Headless Chrome is the reliable way to test
interaction — append a small script to a copy of the page, then read the result out of the DOM:

```bash
python3 build.py
python3 -m http.server 8777 &
# copy index.html to scratch_test.html with a <script> that clicks and writes to #TESTOUT
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless=new --disable-gpu \
  --virtual-time-budget=12000 --dump-dom http://localhost:8777/scratch_test.html \
  | grep -o 'id="TESTOUT"[^>]*>[^<]*'
```

Dispatch keyboard events on `document.activeElement`, not `window` — events fired at `window`
never reach the `document` listeners, so working code will look broken. Delete `scratch_*.html`
afterwards.
