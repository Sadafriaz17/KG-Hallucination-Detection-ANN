# Interactive Knowledge Graph

The visualization reads the real rows from `dataset/triples.csv`; it does not
read `ground_truth.csv` or create example triples. Repeated entity labels share
one node, while `MultiDiGraph` preserves repeated/parallel triple edges.

## Generate

From the project root, activate the virtual environment and install the
declared dependencies:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m visualization.visualize_kg
```

The command writes `visualization/knowledge_graph.html`. Open that file in a
modern browser. To use another CSV or output path:

```powershell
python -m visualization.visualize_kg --input dataset\triples.csv --output visualization\knowledge_graph.html
```

## Explore

- Zoom with the mouse wheel or trackpad and drag the canvas to pan.
- Drag nodes to rearrange the layout; physics settles the graph automatically.
- Hover over a node for its entity and role, or over an edge for its relation
  and triple ID.
- Use the node selector to focus a connection and the filter menu to select
  `edge`, then `relation`, then one or more relation values.
- Colors distinguish subject-only nodes, object-only nodes, nodes serving both
  roles, and the dataset's “No objectively established answer” placeholder.
  Edge colors distinguish relations.

PyVis embeds its graph assets in the generated HTML. Its template may still
request Bootstrap styling from a CDN; the graph data itself comes only from the
local CSV.
