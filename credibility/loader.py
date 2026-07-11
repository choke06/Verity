# loader.py

import csv

from collections import Counter
from collections import defaultdict


def load_from_csv(folder):

    source_names = load_sources(
        folder
    )

    (
        source_to_claims,
        claim_to_sources
    ) = load_assertions(
        folder
    )

    agreement_weights = load_agreement_weights(
        folder
    )

    return (
        source_to_claims,
        claim_to_sources,
        source_names,
        agreement_weights
    )


def load_sources(folder):

    source_names = {}

    path = f"{folder}/sources.csv"

    with open(
        path,
        newline="",
        encoding="utf-8"
    ) as f:

        reader = csv.DictReader(f)

        for row in reader:

            source_id = int(
                row["id"]
            )

            source_names[source_id] = row[
                "domain"
            ]

    return source_names


def load_assertions(folder):

    source_to_claims = defaultdict(set)
    claim_to_sources = defaultdict(set)

    path = f"{folder}/assertions.csv"

    with open(
        path,
        newline="",
        encoding="utf-8"
    ) as f:

        reader = csv.DictReader(f)

        for row in reader:

            source_id = int(
                row["source_id"]
            )

            claim_id = int(
                row["claim_id"]
            )

            source_to_claims[
                source_id
            ].add(
                claim_id
            )

            claim_to_sources[
                claim_id
            ].add(
                source_id
            )

    return (
        source_to_claims,
        claim_to_sources
    )


def load_agreement_weights(folder):

    claim_lookup = {}

    path = f"{folder}/claims.csv"

    with open(
        path,
        newline="",
        encoding="utf-8"
    ) as f:

        reader = csv.DictReader(f)

        for row in reader:

            claim_lookup[
                int(row["id"])
            ] = (
                row["product_id"],
                row["attribute"]
            )

    groups = defaultdict(list)

    path = f"{folder}/source_claims.csv"

    with open(
        path,
        newline="",
        encoding="utf-8"
    ) as f:

        reader = csv.DictReader(f)

        for row in reader:

            claim_id = int(
                row["claim_id"]
            )

            if claim_id not in claim_lookup:
                continue

            product_id, attribute = claim_lookup[
                claim_id
            ]

            value = row["value"]

            groups[
                (
                    product_id,
                    attribute
                )
            ].append(
                (
                    int(row["source_id"]),
                    claim_id,
                    value
                )
            )

    agreement_weights = {}

    for assertions in groups.values():

        counts = Counter(

            value

            for _, _, value
            in assertions

        )

        total = len(
            assertions
        )

        for (
            source_id,
            claim_id,
            value
        ) in assertions:

            agreement_weights[
                (
                    source_id,
                    claim_id
                )
            ] = (
                counts[value]
                / total
            )

    return agreement_weights