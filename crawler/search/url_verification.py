# search/url_verification.py

from fetch_page import fetch_page
from extraction.product_data import extract_product_data
from extraction.home_depot import extract_home_depot_specs

from identity.gtin import normalize_gtin
from search.discovery import (
    gtin_overlap_score,
    model_overlap_score
)


async def verify_candidate(url, seed_product):

    print(f"\nchecking {url}")

    try:
        crawl_result = await fetch_page(url)

        html = crawl_result["html"]
        next_specs = crawl_result["next_specs"]
        generic_specs = crawl_result["generic_specs"]
        extracted_specs = crawl_result["extracted_specs"]
        spec_payloads = crawl_result["spec_payloads"]

        extracted_specs = extract_home_depot_specs(
            spec_payloads
        )

        product_data = extract_product_data(
            html=html,
            extracted_specs=extracted_specs,
            next_specs=next_specs,
            generic_specs=generic_specs
        )

        product = product_data["product"]

        candidate_gtin = normalize_gtin(
            product_data.get("gtin")
        )

        candidate_model = product_data.get("model")

        structured_found = bool(
            product
            or next_specs
            or extracted_specs
        )

        if not structured_found:
            print("no structured product data")
            return {"approved": False}

        print("structured product data found")

        seed_gtin = normalize_gtin(
            seed_product.get("gtin")
        )

        seed_model = seed_product.get("model")

        if seed_gtin and candidate_gtin:

            score = gtin_overlap_score(
                seed_gtin,
                candidate_gtin
            )

            print(f"gtin score: {score:.2f}")

            return {
                "approved": score >= 0.85
            }

        if seed_model and candidate_model:

            score = model_overlap_score(
                seed_model,
                candidate_model
            )

            print(f"model score: {score:.2f}")

            return {
                "approved": score >= 0.70
            }

        print("structured page approved")

        return {
            "approved": True
        }

    except Exception as e:

        print(f"verification failed: {e}")

        return {
            "approved": False
        }