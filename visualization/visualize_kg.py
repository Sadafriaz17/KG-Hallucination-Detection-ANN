"""Generate an interactive HTML view of the project's triples."""

from __future__ import annotations

import argparse
import csv
import html
import json
import unicodedata
from collections.abc import Mapping, Sequence
from pathlib import Path

import networkx as nx
from pyvis.network import Network

from config.config import Config


_REQUIRED_COLUMNS = ("triple_id", "subject", "relation", "object")
_OUTPUT_PATH = Path(__file__).resolve().parent / "knowledge_graph.html"
_RELATION_COLORS = (
    "#2563eb",
    "#059669",
    "#d97706",
    "#7c3aed",
    "#db2777",
    "#0891b2",
    "#4f46e5",
    "#65a30d",
)


def load_triples(csv_path: Path | str = Config.TRIPLES_CSV) -> list[dict[str, str]]:
    """Load and minimally validate the triple columns used by the graph."""
    path = Path(csv_path)
    with path.open(encoding="utf-8-sig", newline="") as csv_file:
        reader = csv.DictReader(csv_file)
        if reader.fieldnames is None:
            raise ValueError(f"Triples CSV has no header: {path}")
        missing = set(_REQUIRED_COLUMNS) - set(reader.fieldnames)
        if missing:
            raise ValueError(
                f"Triples CSV is missing required columns: {sorted(missing)}"
            )
        triples = list(reader)

    if not triples:
        raise ValueError(f"Triples CSV contains no records: {path}")
    for row_number, triple in enumerate(triples, start=2):
        for field in _REQUIRED_COLUMNS:
            value = triple.get(field)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(
                    f"Triples CSV row {row_number} has an empty {field!r}."
                )
    return triples


def _entity_id(label: str) -> str:
    """Canonicalize labels so repeated entities share one graph node."""
    return unicodedata.normalize("NFC", label.strip()).casefold()


def _is_placeholder(label: str) -> bool:
    return label.strip().casefold() == "no objectively established answer"


def build_graph(triples: Sequence[Mapping[str, str]]) -> nx.MultiDiGraph:
    """Build a directed multigraph, retaining repeated triples as edges."""
    graph = nx.MultiDiGraph()
    for row_index, triple in enumerate(triples):
        if not isinstance(triple, Mapping):
            raise TypeError(f"Triple at index {row_index} must be a mapping.")
        values = {
            field: triple.get(field)
            for field in _REQUIRED_COLUMNS
        }
        for field, value in values.items():
            if not isinstance(value, str) or not value.strip():
                raise ValueError(
                    f"Triple at index {row_index} has an empty {field!r}."
                )

        triple_id = values["triple_id"].strip()
        subject = values["subject"].strip()
        relation = values["relation"].strip()
        object_value = values["object"].strip()
        subject_id = _entity_id(subject)
        object_id = _entity_id(object_value)

        for node_id, label, role in (
            (subject_id, subject, "subject"),
            (object_id, object_value, "object"),
        ):
            if node_id not in graph:
                graph.add_node(
                    node_id,
                    label=label,
                    roles=set(),
                    kind="placeholder" if _is_placeholder(label) else "entity",
                )
            graph.nodes[node_id]["roles"].add(role)

        edge_key = f"{row_index}:{triple_id}"
        graph.add_edge(
            subject_id,
            object_id,
            key=edge_key,
            edge_id=edge_key,
            triple_id=triple_id,
            relation=relation,
        )
    return graph


def render_graph(graph: nx.MultiDiGraph, output_path: Path | str) -> Path:
    """Write a self-contained PyVis graph with node and relation filters."""
    destination = Path(output_path).resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    network = Network(
        height="850px",
        width="100%",
        directed=True,
        neighborhood_highlight=True,
        select_menu=True,
        filter_menu=True,
        bgcolor="#f8fafc",
        font_color="#1f2937",
        cdn_resources="in_line",
    )

    relation_names = sorted(
        {
            data["relation"]
            for _, _, _, data in graph.edges(keys=True, data=True)
        },
        key=str.casefold,
    )
    relation_colors = {
        relation: _RELATION_COLORS[index % len(_RELATION_COLORS)]
        for index, relation in enumerate(relation_names)
    }

    for node_id, data in graph.nodes(data=True):
        roles = sorted(data["roles"])
        if data["kind"] == "placeholder":
            color, shape, group = "#94a3b8", "diamond", "placeholder"
            role_description = "Dataset placeholder; not an entity"
        elif roles == ["subject", "object"]:
            color, shape, group = "#8b5cf6", "dot", "subject and object"
            role_description = "Subject and object"
        elif roles == ["subject"]:
            color, shape, group = "#3b82f6", "dot", "subject"
            role_description = "Subject"
        else:
            color, shape, group = "#10b981", "dot", "object"
            role_description = "Object"
        safe_label = html.escape(data["label"])
        network.add_node(
            node_id,
            label=data["label"],
            title=f"<b>{safe_label}</b><br>Role: {role_description}",
            group=group,
            color=color,
            shape=shape,
            size=22 + min(graph.degree(node_id), 12),
            borderWidth=2,
        )

    for source, target, _, data in graph.edges(keys=True, data=True):
        relation = data["relation"]
        color = relation_colors[relation]
        title = (
            f"<b>{html.escape(relation)}</b><br>"
            f"Triple ID: {html.escape(data['triple_id'])}<br>"
            f"{html.escape(graph.nodes[source]['label'])} "
            f"&rarr; {html.escape(graph.nodes[target]['label'])}"
        )
        network.add_edge(
            source,
            target,
            id=data["edge_id"],
            label=relation,
            relation=relation,
            title=title,
            arrows="to",
            color={"color": color, "highlight": color},
            font={"align": "middle", "size": 12},
            smooth={"type": "dynamic"},
        )

    network.set_options(
        json.dumps(
            {
                "interaction": {
                    "hover": True,
                    "tooltipDelay": 120,
                    "navigationButtons": True,
                    "keyboard": {"enabled": True},
                },
                "nodes": {
                    "font": {"size": 16, "face": "Arial"},
                    "borderWidth": 2,
                },
                "edges": {
                    "font": {"align": "middle"},
                    "smooth": {"type": "dynamic"},
                },
                "physics": {
                    "barnesHut": {
                        "gravitationalConstant": -7000,
                        "centralGravity": 0.25,
                        "springLength": 170,
                        "springConstant": 0.04,
                        "damping": 0.09,
                    },
                    "stabilization": {"iterations": 300},
                },
            }
        )
    )
    destination.write_text(network.generate_html(), encoding="utf-8")
    return destination


def main(argv: Sequence[str] | None = None) -> int:
    """Load the project CSV and generate the requested HTML file."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input",
        type=Path,
        default=Config.TRIPLES_CSV,
        help="Triples CSV (defaults to dataset/triples.csv).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=_OUTPUT_PATH,
        help="HTML destination (defaults to visualization/knowledge_graph.html).",
    )
    args = parser.parse_args(argv)
    triples = load_triples(args.input)
    graph = build_graph(triples)
    output = render_graph(graph, args.output)
    print(
        f"Generated {output} with {graph.number_of_nodes()} nodes and "
        f"{graph.number_of_edges()} directed edges."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
