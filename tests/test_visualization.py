"""Tests for the standalone CSV-backed Knowledge Graph visualization."""

from __future__ import annotations

import pytest

from config.config import Config
from visualization.visualize_kg import (
    build_graph,
    load_triples,
    render_graph,
)


def test_actual_dataset_rows_are_all_graph_edges():
    triples = load_triples(Config.TRIPLES_CSV)
    graph = build_graph(triples)

    assert len(triples) == 80
    assert graph.number_of_edges() == len(triples)
    assert {
        data["triple_id"]
        for _, _, _, data in graph.edges(keys=True, data=True)
    } == {triple["triple_id"] for triple in triples}


def test_duplicate_entities_and_parallel_edges_are_preserved():
    graph = build_graph(
        [
            {
                "triple_id": "T1",
                "subject": "Paris",
                "relation": "Capital",
                "object": "France",
            },
            {
                "triple_id": "T1",
                "subject": "paris",
                "relation": "Capital",
                "object": "France",
            },
        ]
    )

    assert graph.number_of_nodes() == 2
    assert graph.number_of_edges() == 2
    assert len(
        {
            data["edge_id"]
            for _, _, _, data in graph.edges(keys=True, data=True)
        }
    ) == 2
    assert graph.nodes["paris"]["roles"] == {"subject"}


def test_generated_html_contains_triple_ids_and_relation_filter(tmp_path):
    graph = build_graph(
        [
            {
                "triple_id": "T0101",
                "subject": "Pakistan",
                "relation": "Capital",
                "object": "Islamabad",
            }
        ]
    )
    output = render_graph(graph, tmp_path / "nested" / "graph.html")

    content = output.read_text(encoding="utf-8")
    assert output.exists()
    assert "T0101" in content
    assert 'id="filter-menu"' in content
    assert "relation" in content
    assert "Pakistan" in content


def test_empty_entity_fields_are_rejected():
    with pytest.raises(ValueError, match="subject"):
        build_graph(
            [
                {
                    "triple_id": "T1",
                    "subject": " ",
                    "relation": "Capital",
                    "object": "Paris",
                }
            ]
        )
