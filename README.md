# biosbi

GNN Final Project: A mariage between cryo-TEM and SBI.

## Roadmap

`src/roadmap.ipynb` features the main goals for this project and implements them in a static fashion – both for clarity and for reliability.

## Local web playground

A small FastAPI playground is available under `src/playground/`, run by `main.py`.

Features:

- separate HTML and CSS files served by FastAPI
- markdown blog-style notes rendered as HTML
- editable simulation parameters JSON for forward simulation (ugly und funktionieren noch nicht)

Key files:

- `src/playground/templates/page.html` (the landing page layout)
- `src/playground/static/styles.css` (styling and making it somewhat pretty)
- `src/playground/app.py` (FastAPI server with endpoints)
- `src/playground/content/` (directory with individual .md files)
- `src/layout.yaml` (block type and order for display on the site)

### Test it

Run it with:

```bash

python src.main
```

Then open http://127.0.0.1:8000
You can see blocks ordered by the `layout.yaml`, with the content provided in `content/`. An interaction is implemented as a FastAPI endpoint accessing the backend (but currently not functional).
