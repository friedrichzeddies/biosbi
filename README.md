# biosbi

GNN Final Project: A mariage between cryo-TEM and SBI

## Local web playground

A small FastAPI playground is available under `src/playground/`.

Features:

- separate HTML and CSS files served by FastAPI
- markdown blog-style notes rendered as HTML (denke das is gar nicht so gut so, bisschen missverstanden worden. Wollte eigentlich eher so nen wir schreiben markdown und das wird da displayed für die narration, dazwischen sind dann code und executable blocks, damit wir nicht markdown schreiben müssen, aber das kann man dann ja sehen.)
- editable simulation parameters JSON for forward simulation (ugly und funktionieren noch nicht)
- relay endpoint for forwarding generated JSON payloads to local programs

Key files:

- `src/playground/templates/index.html`
- `src/playground/static/styles.css`
- `src/playground/static/app.js`
- `src/playground/content.md`
- `src/forward_sim/simulation_parameters.json`

### Test it

Run it with:

```bash
uvicorn src.main:app --reload
```

Then open http://127.0.0.1:8000

The relay endpoint is intentionally restricted to loopback targets such as:

- http://127.0.0.1:8001/ingest
- http://localhost:9000/api
