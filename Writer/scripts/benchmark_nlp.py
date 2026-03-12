"""Benchmark comparing regex-based vs spaCy-based entity extraction.

This script compares the performance and accuracy of the current regex-based
entity extraction with spaCy-based NER for fictional text.
"""

import time
from typing import Any

# Test samples from different genres
TEST_SAMPLES = {
    "fantasy_short": """
    Sir Kael rode his horse Stormwind through the Forest of Elders.
    He carried the Ancient Sword of Power. Lady Elara waited at the Tower.
    """,
    "fantasy_long": """
    Sir Kael Thunderborn rode his mighty horse Stormwind through the ancient
    Forest of Elders, where the trees whispered secrets of the Old Magic.
    He carried the legendary Ancient Sword of Power, forged in the Age of Dragons
    by the master smiths of the Mountain Kingdom. Lady Elara Windrider waited
    at the Tower of the Sun, her magical staff glowing with ethereal light.
    The Great Wall of Arathor protected the kingdom from the Shadow Legion
    that lurked in the Dark Marshes. A mystical crystal known as the Heart
    of the Mountain pulsed with ancient energy, drawing power from the ley lines
    that crisscrossed the realm. King Aldric the Wise ruled from his throne
    in the Crystal Palace, while the wizard Merlin studied ancient tomes
    in the Library of Alexandria.
    """,
    "scifi": """
    Captain Zara Nexus piloted her starship Event Horizon through the asteroid belt.
    The quantum drive hummed as they approached the space station Orion Prime.
    Lieutenant Kaelen examined the alien artifact from the planet Xylos.
    Commander Sarah Chen ordered the deployment of combat drones.
    The neural interface helmet displayed holographic data streams.
    Dr. Marcus Webb analyzed samples from the Andromeda galaxy.
    """,
    "romance": """
    Eleanor gazed at the vintage locket from her grandmother.
    The rose garden at the Hampton Estate bloomed with crimson flowers.
    She wore the emerald necklace that once belonged to Lady Charlotte.
    The handwritten letter contained a secret message from her past.
    The silver bracelet with the heart charm was his first gift.
    """,
    "history": """
    General Marcus led his legion across the Rhine River into Germania.
    The Roman fortifications at Castra Regina stood against barbarian tribes.
    The bronze statue of Emperor Augustus watched over the forum.
    The scroll contained the edict from the Senate of Rome.
    The gladius sword was standard issue for legionnaires.
    """,
    "military": """
    Sergeant Miller checked his M4 carbine before the mission.
    The armored personnel carrier rolled through the desert terrain.
    The drone feed showed enemy positions near the airfield.
    The tactical map displayed coordinates for the extraction point.
    The encrypted radio transmitted coded messages to command.
    """,
}


def benchmark_regex_extractor(text: str) -> dict[str, Any]:
    """Benchmark the current regex-based extraction."""
    from src.novel.continuity import CharacterState, StoryState
    from src.novel.inventory_updater import InventoryUpdater

    updater = InventoryUpdater()

    # Create a story state
    story_state = StoryState(
        chapter=1,
        location="unknown",
        active_characters=["Protagonist"],
        character_states={
            "Protagonist": CharacterState(
                name="Protagonist", status="alive", location="unknown", physical_form="human"
            )
        },
    )

    start = time.time()
    entities = updater._extract_entities(text, story_state)
    elapsed = time.time() - start

    return {
        "time": elapsed,
        "entities": entities,
        "count": len(entities),
    }


def benchmark_nlp_extractor(text: str) -> dict[str, Any]:
    """Benchmark the new NLP-based extraction."""
    from src.utils.nlp import SPACY_AVAILABLE, EntityExtractor

    if not SPACY_AVAILABLE:
        return {
            "time": 0,
            "entities": [],
            "count": 0,
            "skipped": True,
        }

    extractor = EntityExtractor()

    start = time.time()
    entities = extractor.extract_entities(text)
    elapsed = time.time() - start

    return {
        "time": elapsed,
        "entities": entities,
        "count": len(entities),
        "skipped": False,
    }


def analyze_entity_quality(entities: list[dict], expected_entities: list[str]) -> dict:
    """Analyze the quality of extracted entities."""
    found_names = [e["text"] if isinstance(e, dict) else e[1] for e in entities]

    # Count matches
    matches = sum(
        1
        for expected in expected_entities
        if any(expected.lower() in found.lower() for found in found_names)
    )

    # False positives
    false_positives = [
        name
        for name in found_names
        if not any(
            exp.lower() in name.lower() or name.lower() in exp.lower() for exp in expected_entities
        )
    ]

    return {
        "precision": matches / len(found_names) if found_names else 0,
        "recall": matches / len(expected_entities) if expected_entities else 0,
        "found": found_names,
        "matches": matches,
        "false_positives": false_positives[:5],  # Limit output
    }


def main():
    """Run benchmarks and comparison."""
    print("=" * 80)
    print("NLP EXTRACTION BENCHMARK: Regex vs spaCy")
    print("=" * 80)

    # Check spaCy availability
    from src.utils.nlp import SPACY_AVAILABLE

    print(f"\nspaCy available: {SPACY_AVAILABLE}")
    if not SPACY_AVAILABLE:
        print("Note: spaCy tests will be skipped. Install with: pip install spacy")
        print("Then download model: python -m spacy download en_core_web_sm")
    print()

    # Expected entities for fantasy_long sample (for quality analysis)
    expected_fantasy = [
        "Kael",
        "Stormwind",
        "Forest of Elders",
        "Ancient Sword of Power",
        "Elara",
        "Tower of the Sun",
        "Great Wall of Arathor",
        "Heart of the Mountain",
        "Aldric",
        "Crystal Palace",
        "Merlin",
        "Library of Alexandria",
    ]

    results = []

    for genre, text in TEST_SAMPLES.items():
        print(f"\n{'-' * 60}")
        print(f"Genre: {genre.upper()}")
        print(f"Text length: {len(text)} characters, {len(text.split())} words")
        print(f"{'-' * 60}")

        # Benchmark regex
        print("\n[Regex Extraction]")
        regex_result = benchmark_regex_extractor(text)
        print(f"  Time: {regex_result['time']:.4f}s")
        print(f"  Entities found: {regex_result['count']}")

        # Show entities
        if regex_result["entities"]:
            print("  Entities:")
            for entity in regex_result["entities"][:10]:  # Limit output
                if isinstance(entity, tuple):
                    print(f"    - {entity[0]}: {entity[1]}")
                else:
                    print(f"    - {entity}")

        # Benchmark NLP
        print("\n[NLP Extraction]")
        nlp_result = benchmark_nlp_extractor(text)

        if nlp_result.get("skipped"):
            print("  Skipped (spaCy not installed)")
        else:
            print(f"  Time: {nlp_result['time']:.4f}s")
            print(f"  Entities found: {nlp_result['count']}")

            # Show entities
            if nlp_result["entities"]:
                print("  Entities:")
                for entity in nlp_result["entities"][:10]:
                    print(f"    - {entity['type']}: {entity['text']} ({entity['source']})")

        # Quality analysis for fantasy_long
        if genre == "fantasy_long":
            print("\n[Quality Analysis]")
            regex_quality = analyze_entity_quality(regex_result["entities"], expected_fantasy)
            print(f"  Regex precision: {regex_quality['precision']:.2%}")
            print(f"  Regex recall: {regex_quality['recall']:.2%}")

            if not nlp_result.get("skipped"):
                nlp_quality = analyze_entity_quality(nlp_result["entities"], expected_fantasy)
                print(f"  NLP precision: {nlp_quality['precision']:.2%}")
                print(f"  NLP recall: {nlp_quality['recall']:.2%}")

        # Store results
        results.append(
            {
                "genre": genre,
                "regex_time": regex_result["time"],
                "regex_count": regex_result["count"],
                "nlp_time": nlp_result.get("time", 0),
                "nlp_count": nlp_result.get("count", 0),
                "nlp_skipped": nlp_result.get("skipped", False),
            }
        )

    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"{'Genre':<15} {'Regex (ms)':<12} {'NLP (ms)':<12} {'Regex #':<10} {'NLP #':<10}")
    print("-" * 60)

    for r in results:
        genre = r["genre"]
        regex_ms = r["regex_time"] * 1000
        nlp_ms = r["nlp_time"] * 1000 if not r["nlp_skipped"] else 0
        regex_count = r["regex_count"]
        nlp_count = r["nlp_count"]

        nlp_str = f"{nlp_ms:.1f}" if not r["nlp_skipped"] else "N/A"
        nlp_count_str = str(nlp_count) if not r["nlp_skipped"] else "N/A"

        print(f"{genre:<15} {regex_ms:<12.1f} {nlp_str:<12} {regex_count:<10} {nlp_count_str:<10}")

    # Calculate averages
    avg_regex_time = sum(r["regex_time"] for r in results) / len(results)
    regex_only_results = [r for r in results if not r.get("nlp_skipped", False)]

    if regex_only_results:
        avg_nlp_time = sum(r["nlp_time"] for r in regex_only_results) / len(regex_only_results)
        print("\nAverage times:")
        print(f"  Regex: {avg_regex_time * 1000:.1f}ms")
        print(f"  NLP:   {avg_nlp_time * 1000:.1f}ms")
        print(f"  Ratio: {avg_nlp_time / avg_regex_time:.1f}x")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    main()
