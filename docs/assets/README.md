# Visual assets

| File | Used in | Status |
|---|---|---|
| `screenshots/order-detail.png`, `screenshots/queue.png` | README | captured |
| `social-preview.png` (`.svg` is the source) | GitHub Settings → Social preview (upload by hand; there is no API) | ready |
| `rescore.gif` | README, under the screenshots | **not captured yet** |

## Capturing `rescore.gif` (HIGH 87 → LOW 16)

No headless-browser tooling is in the repo, so this is a manual capture.

1. `make setup && make web && make demo`, then open http://localhost:8000/.
2. Open the sample order #2601 (HIGH 87, awaiting reply).
3. Start a screen recorder (for example Peek, Kooha or ScreenToGif) on the browser window only, about 1000 px wide.
4. Use the simulated reply with: `ey behi. Douar Ouled Ali, triq el jemaa, dar 14, el bab lazra9 9odem el pharmacie.`
5. Stop once the order shows LOW 16 and the reason diff. Keep it under 10 s and under 2 MB.
6. Save as `docs/assets/rescore.gif`, then add this under the screenshots in `README.md`:

   ```md
   ![Replying with a full address rescores the order from HIGH 87 to LOW 16 and shows the reason diff](docs/assets/rescore.gif)
   ```
