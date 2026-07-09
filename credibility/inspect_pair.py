# inspect_pair.py

import psycopg2
import sys

from collections import defaultdict

from preprocessing.normalization import canonicalize


GRAPH_ATTRIBUTES = {

    "ram_gb",
    "storage_gb",

    "cpu_model",
    "cpu_cores",

    "gpu_model",

    "wifi_standard",
    "bluetooth_version",

    "display_resolution",
    "screen_size",

    "battery_life_hr",

    "weight_lb",

    "operating_system",

    "touchscreen"
}


def load_source(
    conn,
    domain
):

    cursor = conn.cursor()

    cursor.execute("""
        SELECT id
        FROM sources
        WHERE domain = %s
    """, (domain,))

    row = cursor.fetchone()

    if row is None:
        raise ValueError(
            f"Unknown source: {domain}"
        )

    return row[0]


def load_assertions(
    conn,
    source_id
):

    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            product_id,
            canonical_attribute,
            value_string,
            value_numeric,
            unit
        FROM source_claims
        WHERE source_id = %s
    """, (source_id,))

    assertions = {}

    for (
        product_id,
        attribute,
        value_string,
        value_numeric,
        unit
    ) in cursor.fetchall():

        if attribute not in GRAPH_ATTRIBUTES:
            continue

        if value_numeric is not None:

            value = str(
                value_numeric
            )

        else:

            value = value_string

        value = canonicalize(
            attribute,
            value
        )

        if value is None:
            continue

        assertions[
            (
                product_id,
                attribute
            )
        ] = (
            value,
            unit
        )

    return assertions


def main():

    if len(sys.argv) != 3:

        print("usage:")
        print("python -m credibility.inspect_pair sourceA sourceB")
        return

    domain_a = sys.argv[1]
    domain_b = sys.argv[2]

    conn = psycopg2.connect(
        dbname="verity_dev",
        user="colehoke"
    )

    source_a = load_source(
        conn,
        domain_a
    )

    source_b = load_source(
        conn,
        domain_b
    )

    assertions_a = load_assertions(
        conn,
        source_a
    )

    assertions_b = load_assertions(
        conn,
        source_b
    )

    products = sorted({

        product_id

        for product_id, _ in assertions_a

    } & {

        product_id

        for product_id, _ in assertions_b

    })

    print()
    print(f"{domain_a} vs {domain_b}")
    print("-" * 60)

    total_matches = 0
    total_disagreements = 0

    for product_id in products:

        matches = []
        disagreements = []

        attributes = sorted({

            attribute

            for p, attribute in assertions_a

            if p == product_id

        } | {

            attribute

            for p, attribute in assertions_b

            if p == product_id

        })

        for attribute in attributes:

            key = (
                product_id,
                attribute
            )

            in_a = key in assertions_a
            in_b = key in assertions_b

            if not (
                in_a
                and
                in_b
            ):
                continue

            value_a, unit_a = assertions_a[key]
            value_b, unit_b = assertions_b[key]

            if (
                value_a == value_b
                and
                unit_a == unit_b
            ):

                matches.append(
                    (
                        attribute,
                        value_a,
                        unit_a
                    )
                )

            else:

                disagreements.append(
                    (
                        attribute,
                        value_a,
                        unit_a,
                        value_b,
                        unit_b
                    )
                )

        if not (
            matches
            or
            disagreements
        ):
            continue

        total_matches += len(
            matches
        )

        total_disagreements += len(
            disagreements
        )

        print()
        print(f"Product {product_id}")

        if matches:

            print("MATCH")

            for (
                attribute,
                value,
                unit
            ) in matches:

                if unit:

                    print(
                        f"{attribute:<25} {value} {unit}"
                    )

                else:

                    print(
                        f"{attribute:<25} {value}"
                    )

        if disagreements:

            print()
            print("DISAGREE")

            for (
                attribute,
                value_a,
                unit_a,
                value_b,
                unit_b
            ) in disagreements:

                left = value_a

                if unit_a:
                    left += f" {unit_a}"

                right = value_b

                if unit_b:
                    right += f" {unit_b}"

                print(attribute)
                print(f"  {domain_a:<20} {left}")
                print(f"  {domain_b:<20} {right}")

    print()
    print("-" * 60)
    print(f"matching assertions: {total_matches}")
    print(f"disagreements:       {total_disagreements}")

    conn.close()


if __name__ == "__main__":
    main()