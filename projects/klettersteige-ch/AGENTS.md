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

Each route object carries three image fields:

```json
"img":       "https://upload.wikimedia.org/.../800px-Sulzfluh.jpg",
"imgPage":   "https://commons.wikimedia.org/wiki/File:Sulzfluh.jpg",
"imgCredit": "Photographer name · CC BY-SA 4.0"
```

- `img` is what renders. It may be an absolute URL **or** a repo-relative path.
- `imgCredit` renders as the caption chip on the image. Always fill it in.
- `imgPage` is provenance only. Optional for own photos.

**For a photo Lukas supplies**, put the file in `photos/` and use a relative path:

```json
"img": "photos/sulzfluh-2026.jpg",
"imgCredit": "Lukas Wallrich"
```

Name files `<route-id>.jpg` (the `id` field of the route) so they stay matchable.
Resize to about 1200 px on the long edge and strip EXIF before committing —
phone originals are 4–8 MB each and will bloat the repo:

```bash
sips -Z 1200 -s format jpeg in.jpg --out photos/<route-id>.jpg   # macOS, also drops most EXIF
exiftool -all= photos/<route-id>.jpg                              # if available, to be sure
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
