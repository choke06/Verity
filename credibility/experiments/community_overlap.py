# community_overlap.py

from collections import defaultdict
from itertools import combinations

import networkx as nx

from ..db.connection import get_db
from ..graph_schema import GRAPH_ATTRIBUTES


def load_claims():

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            source_id,
            product_id,
            canonical_attribute,
            value_string,
            value_numeric,
            unit
        FROM source_claims
        WHERE canonical_attribute = ANY(%s)
    """, (list(GRAPH_ATTRIBUTES),))

    rows = cursor.fetchall()

    conn.close()

    return rows


def load_source_names():

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            id,
            domain
        FROM sources
    """)

    names = dict(cursor.fetchall())

    conn.close()

    return names


def build_source_claims(rows):

    source_claims = defaultdict(set)

    for (
        source_id,
        product_id,
        attribute,
        value_string,
        value_numeric,
        unit
    ) in rows:

        value = (
            value_numeric
            if value_numeric is not None
            else value_string
        )

        claim = (
            product_id,
            attribute,
            value,
            unit
        )

        source_claims[source_id].add(claim)

    return source_claims


def build_claim_sources(source_claims):

    claim_sources = defaultdict(set)

    for source_id, claims in source_claims.items():

        for claim in claims:

            claim_sources[claim].add(source_id)

    return claim_sources


def build_source_graph(claim_sources):

    graph = nx.Graph()

    # connect sources that assert the same claim
    for sources in claim_sources.values():

        if len(sources) < 2:
            continue

        for source_a, source_b in combinations(sorted(sources), 2):

            if graph.has_edge(source_a, source_b):

                graph[source_a][source_b]["weight"] += 1

            else:

                graph.add_edge(
                    source_a,
                    source_b,
                    weight=1
                )

    return graph


def find_communities(graph):

    return list(
        nx.community.louvain_communities(
            graph,
            weight="weight"
        )
    )


def print_communities(
    communities,
    source_names
):

    print()
    print("Communities")
    print("-" * 40)

    for i, community in enumerate(communities, start=1):

        print()
        print(f"Community {i}")

        for source in sorted(community):

            print(
                f"  {source_names.get(source, source)}"
            )


def print_edge_weights(
    graph,
    source_names
):

    print()
    print("Edge Weights")
    print("-" * 40)

    edges = sorted(
        graph.edges(data=True),
        key=lambda edge: edge[2]["weight"],
        reverse=True
    )

    for source_a, source_b, data in edges:

        print(
            f"{source_names[source_a]} ↔ "
            f"{source_names[source_b]} : "
            f"{data['weight']}"
        )


def print_bridge_edges(
    graph,
    communities,
    source_names
):

    print()
    print("Bridge Edges")
    print("-" * 40)

    community_map = {}

    for i, community in enumerate(communities):

        for source in community:

            community_map[source] = i

    bridges = []

    for source_a, source_b, data in graph.edges(data=True):

        if community_map[source_a] != community_map[source_b]:

            bridges.append(
                (
                    data["weight"],
                    source_a,
                    source_b
                )
            )

    bridges.sort(reverse=True)

    for weight, source_a, source_b in bridges:

        print(
            f"{source_names[source_a]} ↔ "
            f"{source_names[source_b]} : "
            f"{weight}"
        )


def main():

    rows = load_claims()

    source_claims = build_source_claims(rows)

    claim_sources = build_claim_sources(source_claims)

    graph = build_source_graph(claim_sources)

    communities = find_communities(graph)

    source_names = load_source_names()

    print_communities(communities, source_names)

    print_edge_weights(graph, source_names)

    print_bridge_edges(graph, communities, source_names)


if __name__ == "__main__":
    main()