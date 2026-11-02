"""
Comprehensive 150-Test Stress Benchmark for Neapolitan Art Dialogue System.
Evaluates:
- Inconsistency Detection (Artist, Venue, City, Out-of-scope)
- Ground Truth Factual Retrieval Accuracy
- Multi-turn Coreference and Context Tracking
- Latency and Error Diagnostics
"""

import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

# Ensure project root is in path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.dialogue.chatbot import NeapolitanArtChatbot
from src.dialogue.inconsistency import InconsistencyDetector, InconsistencyType


def build_150_test_suite() -> List[Dict[str, Any]]:
    tests: List[Dict[str, Any]] = []

    # =========================================================================
    # CATEGORY 1: ARTIST ATTRIBUTION INCONSISTENCIES (30 TESTS)
    # =========================================================================
    caravaggio_works = [
        "The Seven Works of Mercy",
        "The Flagellation of Christ",
        "The Martyrdom of Saint Ursula",
        "Seven Works of Mercy",
        "Flagellation of Christ",
        "Martyrdom of Saint Ursula",
    ]
    battistello_works = [
        "The Liberation of Saint Peter",
        "The Washing of the Feet",
        "Christ at the Column",
        "Trinitas Terrestris",
        "Frescoes of the Chapel of the Assunta",
        "Liberation of Saint Peter",
        "Washing of the Feet",
    ]

    for work in caravaggio_works:
        tests.append({
            "id": f"ART_MIS_{len(tests)+1:03d}",
            "category": "Artist Mismatch",
            "query": f"Did Battistello Caracciolo paint {work}?",
            "expected_inconsistent": True,
            "expected_type": "artist_mismatch",
            "expected_entities": ["Caravaggio", work],
        })
        tests.append({
            "id": f"ART_MIS_{len(tests)+1:03d}",
            "category": "Artist Mismatch",
            "query": f"Is {work} a masterpiece created by Caracciolo in Naples?",
            "expected_inconsistent": True,
            "expected_type": "artist_mismatch",
            "expected_entities": ["Caravaggio"],
        })
        tests.append({
            "id": f"ART_MIS_{len(tests)+1:03d}",
            "category": "Artist Mismatch",
            "query": f"Tell me about Battistello's {work}.",
            "expected_inconsistent": True,
            "expected_type": "artist_mismatch",
            "expected_entities": ["Caravaggio"],
        })

    for work in battistello_works[:4]:
        tests.append({
            "id": f"ART_MIS_{len(tests)+1:03d}",
            "category": "Artist Mismatch",
            "query": f"Did Caravaggio paint {work}?",
            "expected_inconsistent": True,
            "expected_type": "artist_mismatch",
            "expected_entities": ["Battistello Caracciolo"],
        })
        tests.append({
            "id": f"ART_MIS_{len(tests)+1:03d}",
            "category": "Artist Mismatch",
            "query": f"Can I see Caravaggio's {work} in Naples?",
            "expected_inconsistent": True,
            "expected_type": "artist_mismatch",
            "expected_entities": ["Battistello Caracciolo"],
        })
        tests.append({
            "id": f"ART_MIS_{len(tests)+1:03d}",
            "category": "Artist Mismatch",
            "query": f"Show me Caravaggio's canvas of {work}.",
            "expected_inconsistent": True,
            "expected_type": "artist_mismatch",
            "expected_entities": ["Battistello Caracciolo"],
        })

    # =========================================================================
    # CATEGORY 2: VENUE / LOCATION INCONSISTENCIES WITHIN NAPLES (30 TESTS)
    # =========================================================================
    location_pairs = [
        ("The Seven Works of Mercy", "Capodimonte", "Pio Monte della Misericordia"),
        ("The Seven Works of Mercy", "Palazzo Zevallos", "Pio Monte della Misericordia"),
        ("The Seven Works of Mercy", "Certosa di San Martino", "Pio Monte della Misericordia"),
        ("The Seven Works of Mercy", "Pietà dei Turchini", "Pio Monte della Misericordia"),
        ("The Flagellation of Christ", "Pio Monte della Misericordia", "Museo Nazionale di Capodimonte"),
        ("The Flagellation of Christ", "Palazzo Zevallos", "Museo Nazionale di Capodimonte"),
        ("The Flagellation of Christ", "Certosa di San Martino", "Museo Nazionale di Capodimonte"),
        ("The Martyrdom of Saint Ursula", "Pio Monte della Misericordia", "Gallerie d'Italia (Palazzo Zevallos Stigliano)"),
        ("The Martyrdom of Saint Ursula", "Capodimonte", "Gallerie d'Italia (Palazzo Zevallos Stigliano)"),
        ("The Martyrdom of Saint Ursula", "Certosa di San Martino", "Gallerie d'Italia (Palazzo Zevallos Stigliano)"),
        ("The Liberation of Saint Peter", "Capodimonte", "Pio Monte della Misericordia"),
        ("The Liberation of Saint Peter", "Palazzo Zevallos", "Pio Monte della Misericordia"),
        ("The Liberation of Saint Peter", "Certosa di San Martino", "Pio Monte della Misericordia"),
        ("The Washing of the Feet", "Pio Monte della Misericordia", "Certosa di San Martino"),
        ("The Washing of the Feet", "Capodimonte", "Certosa di San Martino"),
        ("Christ at the Column", "Pio Monte della Misericordia", "Museo Nazionale di Capodimonte"),
        ("Christ at the Column", "Certosa di San Martino", "Museo Nazionale di Capodimonte"),
        ("Trinitas Terrestris", "Capodimonte", "Chiesa della Pietà dei Turchini"),
        ("Trinitas Terrestris", "Pio Monte della Misericordia", "Chiesa della Pietà dei Turchini"),
        ("Frescoes of the Chapel of the Assunta", "Capodimonte", "Certosa di San Martino"),
        ("Frescoes of the Chapel of the Assunta", "Pio Monte della Misericordia", "Certosa di San Martino"),
        ("Seven Works of Mercy", "Capodimonte", "Pio Monte della Misericordia"),
        ("Flagellation of Christ", "Pio Monte", "Museo Nazionale di Capodimonte"),
        ("Martyrdom of Saint Ursula", "Capodimonte", "Gallerie d'Italia (Palazzo Zevallos Stigliano)"),
        ("Liberation of Saint Peter", "Capodimonte", "Pio Monte della Misericordia"),
        ("Washing of the Feet", "Capodimonte", "Certosa di San Martino"),
        ("The Seven Works of Mercy", "Museo di Capodimonte", "Pio Monte della Misericordia"),
        ("The Flagellation of Christ", "Zevallos", "Museo Nazionale di Capodimonte"),
        ("The Martyrdom of Saint Ursula", "San Martino", "Gallerie d'Italia (Palazzo Zevallos Stigliano)"),
        ("Christ at the Column", "Pio Monte", "Museo Nazionale di Capodimonte"),
    ]

    for work, false_venue, true_venue in location_pairs:
        tests.append({
            "id": f"LOC_MIS_{len(tests)+1:03d}",
            "category": "Location Mismatch",
            "query": f"Can I visit {work} at {false_venue}?",
            "expected_inconsistent": True,
            "expected_type": "location_mismatch",
            "expected_entities": [true_venue],
        })

    # =========================================================================
    # CATEGORY 3: CITY / GEOGRAPHIC INCONSISTENCIES (30 TESTS)
    # =========================================================================
    non_neapolitan = [
        ("The Calling of Saint Matthew", "Rome"),
        ("Calling of Saint Matthew", "Rome"),
        ("The Martyrdom of Saint Matthew", "Rome"),
        ("The Inspiration of Saint Matthew", "Rome"),
        ("Judith Beheading Holofernes", "Rome"),
        ("The Conversion of Saint Paul", "Rome"),
        ("Conversion of Saint Paul", "Rome"),
        ("Crucifixion of Saint Peter", "Rome"),
        ("David with the Head of Goliath", "Rome"),
        ("Boy with a Basket of Fruit", "Rome"),
        ("Bacchus", "Florence"),
        ("Medusa", "Florence"),
        ("The Sacrifice of Isaac", "Florence"),
        ("Sacrifice of Isaac", "Florence"),
        ("Death of the Virgin", "Paris"),
        ("The Fortune Teller", "Paris"),
        ("Fortune Teller", "Paris"),
        ("The Beheading of Saint John the Baptist", "Valletta"),
        ("Beheading of Saint John the Baptist", "Valletta"),
        ("The Burial of Saint Lucy", "Syracuse"),
        ("Burial of Saint Lucy", "Syracuse"),
        ("Mona Lisa", "Paris"),
        ("The Last Supper", "Milan"),
        ("The School of Athens", "Vatican City"),
        ("The Calling of Saint Matthew", "Rome"),
        ("Judith Beheading Holofernes", "Rome"),
        ("Bacchus", "Florence"),
        ("Medusa", "Florence"),
        ("Death of the Virgin", "Paris"),
        ("The Last Supper", "Milan"),
    ]

    for title, city in non_neapolitan:
        tests.append({
            "id": f"CITY_MIS_{len(tests)+1:03d}",
            "category": "City Mismatch",
            "query": f"Where can I see {title} in Naples?",
            "expected_inconsistent": True,
            "expected_type": "city_mismatch",
            "expected_entities": [city],
        })

    # =========================================================================
    # CATEGORY 4: OUT-OF-SCOPE ARTIST INCONSISTENCIES (15 TESTS)
    # =========================================================================
    disallowed_artists = [
        "Leonardo da Vinci",
        "Leonardo",
        "Michelangelo Buonarroti",
        "Raphael",
        "Raffaello",
        "Bernini",
        "Titian",
        "Tiziano",
        "Rembrandt",
        "Vermeer",
        "Velazquez",
        "Picasso",
        "Monet",
        "Leonardo da Vinci",
        "Raphael",
    ]

    for artist in disallowed_artists:
        tests.append({
            "id": f"SCOPE_MIS_{len(tests)+1:03d}",
            "category": "Out of Scope Artist",
            "query": f"Are there any paintings by {artist} in this Neapolitan exhibition tour?",
            "expected_inconsistent": True,
            "expected_type": "out_of_scope_artist",
            "expected_entities": [],
        })

    # =========================================================================
    # CATEGORY 5: VALID GROUND TRUTH FACTUAL INQUIRIES (25 TESTS)
    # =========================================================================
    valid_queries = [
        ("Tell me about The Seven Works of Mercy.", ["Caravaggio", "Pio Monte della Misericordia"]),
        ("Where is The Seven Works of Mercy located in Naples?", ["Pio Monte della Misericordia", "Tribunali"]),
        ("Who painted The Flagellation of Christ in Capodimonte?", ["Caravaggio"]),
        ("Tell me about The Flagellation of Christ.", ["Capodimonte", "Caravaggio"]),
        ("What is Caravaggio's last painting in Naples?", ["Ursula", "Palazzo Zevallos"]),
        ("Tell me about The Martyrdom of Saint Ursula.", ["Caravaggio", "Zevallos", "Toledo"]),
        ("What works by Caravaggio can I visit in Naples?", ["Seven Works of Mercy", "Flagellation", "Saint Ursula"]),
        ("What paintings by Battistello Caracciolo are in Naples?", ["Liberation of Saint Peter", "Washing of the Feet"]),
        ("Tell me about The Liberation of Saint Peter.", ["Battistello Caracciolo", "Pio Monte della Misericordia"]),
        ("Where can I find The Washing of the Feet by Battistello?", ["Certosa di San Martino"]),
        ("Tell me about Christ at the Column by Battistello Caracciolo.", ["Capodimonte"]),
        ("Where is Trinitas Terrestris preserved?", ["Pietà dei Turchini"]),
        ("Tell me about Frescoes of the Chapel of the Assunta.", ["Certosa di San Martino"]),
        ("What works can I see at Pio Monte della Misericordia?", ["The Seven Works of Mercy", "The Liberation of Saint Peter"]),
        ("What Caravaggio works are at Capodimonte?", ["The Flagellation of Christ"]),
        ("What is the address of Pio Monte della Misericordia?", ["Tribunali"]),
        ("What are the dimensions of The Seven Works of Mercy?", ["390 cm x 260 cm", "Oil on canvas"]),
        ("When was The Flagellation of Christ painted?", ["1607"]),
        ("What year was The Martyrdom of Saint Ursula completed?", ["1610"]),
        ("Who painted The Washing of the Feet in San Martino?", ["Battistello Caracciolo"]),
        ("What can I visit at Certosa di San Martino?", ["Washing of the Feet", "Assunta"]),
        ("Tell me about the painter Battistello Caracciolo.", ["Naples", "Caravaggio"]),
        ("What art movement did Caravaggio belong to?", ["Baroque", "Chiaroscuro", "Tenebrism"]),
        ("Where is Gallerie d'Italia located in Naples?", ["Via Toledo 185"]),
        ("Hello, can you give me an overview of Caravaggio and Battistello in Naples?", ["Caravaggio", "Battistello", "Naples"]),
    ]

    for q, expected_kws in valid_queries:
        tests.append({
            "id": f"VALID_{len(tests)+1:03d}",
            "category": "Factual Ground Truth",
            "query": q,
            "expected_inconsistent": False,
            "expected_type": "no_inconsistency",
            "expected_entities": expected_kws,
        })

    # =========================================================================
    # CATEGORY 6: MULTI-TURN DISCOURSE & COREFERENCE SEQUENCES (20 TESTS)
    # =========================================================================
    # 5 dialogue conversations with 4 turns each = 20 tests
    multi_turn_dialogues = [
        # Dialogue 1: Caravaggio at Pio Monte -> Coreference -> Inconsistency check
        [
            ("Tell me about The Seven Works of Mercy.", False, "no_inconsistency", ["Caravaggio", "Pio Monte"]),
            ("Where is it located?", False, "no_inconsistency", ["Pio Monte della Misericordia"]),
            ("What are its dimensions?", False, "no_inconsistency", ["390 cm x 260 cm"]),
            ("Did Battistello paint it?", True, "artist_mismatch", ["Caravaggio"]),
        ],
        # Dialogue 2: Capodimonte Flagellation -> Coreference -> Venue inconsistency
        [
            ("Tell me about The Flagellation of Christ.", False, "no_inconsistency", ["Caravaggio", "Capodimonte"]),
            ("Who is the artist?", False, "no_inconsistency", ["Caravaggio"]),
            ("Can I visit it at Pio Monte?", True, "location_mismatch", ["Capodimonte"]),
            ("What year was it painted?", False, "no_inconsistency", ["1607"]),
        ],
        # Dialogue 3: Battistello -> Coreference -> Outside Naples inquiry
        [
            ("Tell me about The Liberation of Saint Peter.", False, "no_inconsistency", ["Battistello", "Pio Monte"]),
            ("Where can I see it?", False, "no_inconsistency", ["Pio Monte della Misericordia"]),
            ("Who painted this work?", False, "no_inconsistency", ["Battistello Caracciolo"]),
            ("Can I also see The Calling of Saint Matthew there?", True, "city_mismatch", ["Rome"]),
        ],
        # Dialogue 4: Certosa di San Martino -> Followup
        [
            ("What works are located at Certosa di San Martino?", False, "no_inconsistency", ["Washing of the Feet", "Assunta"]),
            ("Tell me about The Washing of the Feet.", False, "no_inconsistency", ["Battistello", "San Martino"]),
            ("Who painted it?", False, "no_inconsistency", ["Battistello Caracciolo"]),
            ("Did Caravaggio paint it?", True, "artist_mismatch", ["Battistello"]),
        ],
        # Dialogue 5: Gallerie d'Italia (Saint Ursula) -> Out of scope check
        [
            ("Tell me about The Martyrdom of Saint Ursula.", False, "no_inconsistency", ["Caravaggio", "Zevallos"]),
            ("Where is it located?", False, "no_inconsistency", ["Toledo", "Zevallos"]),
            ("What is its significance?", False, "no_inconsistency", ["final painting", "1610"]),
            ("Can I also see paintings by Rembrandt here?", True, "out_of_scope_artist", []),
        ],
    ]

    for d_idx, seq in enumerate(multi_turn_dialogues, 1):
        for turn_idx, (q, exp_inc, exp_type, exp_ents) in enumerate(seq, 1):
            tests.append({
                "id": f"SEQ_{d_idx}_{turn_idx:02d}_{len(tests)+1:03d}",
                "category": "Multi-Turn Discourse",
                "dialogue_id": f"D{d_idx}",
                "turn_in_dialogue": turn_idx,
                "query": q,
                "expected_inconsistent": exp_inc,
                "expected_type": exp_type,
                "expected_entities": exp_ents,
            })

    return tests


def run_benchmark():
    print("=" * 70)
    print("INITIALIZING 150-TEST COMPREHENSIVE STRESS SUITE")
    print("Neapolitan Art Dialogue System — Academic Robustness & Accuracy")
    print("=" * 70)

    test_suite = build_150_test_suite()
    print(f"Total Test Cases Compiled: {len(test_suite)}")
    assert len(test_suite) == 150, f"Expected exactly 150 tests, got {len(test_suite)}"

    # Category counts
    cat_counts = {}
    for t in test_suite:
        cat = t["category"]
        cat_counts[cat] = cat_counts.get(cat, 0) + 1
    print("\nTest Distribution by Category:")
    for cat, cnt in cat_counts.items():
        print(f"  - {cat}: {cnt} tests")

    # Initialize bot
    bot = NeapolitanArtChatbot()

    # Results tracking
    passed_tests = 0
    failed_tests = 0
    failures: List[Dict[str, Any]] = []
    latencies: List[float] = []

    # Confusion matrix for inconsistency detection
    tp = 0  # True Positive: Inconsistency expected & detected correctly
    fp = 0  # False Positive: Normal query incorrectly flagged as inconsistent
    tn = 0  # True Negative: Normal query correctly identified as consistent
    fn = 0  # False Negative: Inconsistency expected but missed

    current_dialogue_id = None

    print("\nExecuting Test Suite...")
    start_total_time = time.time()

    for idx, test in enumerate(test_suite, 1):
        # Manage dialogue context for multi-turn sequences
        if "dialogue_id" in test:
            if test["dialogue_id"] != current_dialogue_id:
                bot.reset_dialogue()
                current_dialogue_id = test["dialogue_id"]
        else:
            # Single-turn independent tests
            bot.reset_dialogue()
            current_dialogue_id = None

        t0 = time.time()
        result = bot.process_utterance(test["query"])
        latency = (time.time() - t0) * 1000.0
        latencies.append(latency)

        inc = result.inconsistency_report
        actual_inconsistent = inc.is_inconsistent
        actual_type = inc.inconsistency_type.value if actual_inconsistent else "no_inconsistency"

        # Check correctness
        test_passed = True
        fail_reasons = []

        # 1. Check inconsistency binary flag
        if actual_inconsistent != test["expected_inconsistent"]:
            test_passed = False
            fail_reasons.append(
                f"Binary mismatch: expected is_inconsistent={test['expected_inconsistent']}, got {actual_inconsistent}"
            )

        # 2. Check inconsistency type
        if test["expected_inconsistent"] and actual_type != test["expected_type"]:
            test_passed = False
            fail_reasons.append(
                f"Type mismatch: expected type '{test['expected_type']}', got '{actual_type}'"
            )

        # 3. Check expected entities in response if specified
        combined_text = (result.system_response + " " + inc.explanation + " " + inc.suggested_correction).lower()
        for expected_ent in test.get("expected_entities", []):
            if expected_ent.lower() not in combined_text:
                test_passed = False
                fail_reasons.append(f"Missing expected entity or keyword: '{expected_ent}'")

        # Update confusion matrix
        if test["expected_inconsistent"]:
            if actual_inconsistent and actual_type == test["expected_type"]:
                tp += 1
            else:
                fn += 1
        else:
            if not actual_inconsistent:
                tn += 1
            else:
                fp += 1

        if test_passed:
            passed_tests += 1
        else:
            failed_tests += 1
            failures.append({
                "test_id": test["id"],
                "category": test["category"],
                "query": test["query"],
                "expected": {
                    "inconsistent": test["expected_inconsistent"],
                    "type": test["expected_type"],
                    "entities": test.get("expected_entities", []),
                },
                "actual": {
                    "inconsistent": actual_inconsistent,
                    "type": actual_type,
                    "response": result.system_response[:150],
                },
                "reasons": fail_reasons,
            })

    total_duration = time.time() - start_total_time
    avg_latency = sum(latencies) / len(latencies) if latencies else 0

    # Calculate Metrics
    accuracy = (passed_tests / len(test_suite)) * 100.0
    precision = (tp / (tp + fp)) * 100.0 if (tp + fp) > 0 else 0.0
    recall = (tp / (tp + fn)) * 100.0 if (tp + fn) > 0 else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0.0

    print("\n" + "=" * 70)
    print("STRESS BENCHMARK RESULTS & METRICS SUMMARY")
    print("=" * 70)
    print(f"Total Tests Executed: {len(test_suite)}")
    print(f"Tests Passed:         {passed_tests} ({accuracy:.2f}%)")
    print(f"Tests Failed:         {failed_tests}")
    print(f"Total Runtime:        {total_duration:.3f} s")
    print(f"Average Latency:      {avg_latency:.2f} ms / query")

    print("\n--- Inconsistency Detection Performance ---")
    print(f"True Positives (TP):  {tp}")
    print(f"True Negatives (TN):  {tn}")
    print(f"False Positives (FP): {fp}")
    print(f"False Negatives (FN): {fn}")
    print(f"Precision:            {precision:.2f}%")
    print(f"Recall:               {recall:.2f}%")
    print(f"F1-Score:             {f1:.2f}%")

    # Output Failures Details
    if failures:
        print("\n" + "=" * 70)
        print("DIAGNOSTICS: FAILED TEST CASES")
        print("=" * 70)
        for f in failures:
            print(f"[{f['test_id']}] ({f['category']}) Query: \"{f['query']}\"")
            for r in f["reasons"]:
                print(f"  * {r}")
            print(f"  Response: {f['actual']['response']}")
            print("-" * 50)
    else:
        print("\nPERFECT RUN: ZERO FAILURES ACROSS ALL 150 TEST CASES!")

    # Save artifact report
    report_data = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "total_tests": len(test_suite),
        "passed": passed_tests,
        "failed": failed_tests,
        "accuracy_pct": accuracy,
        "precision_pct": precision,
        "recall_pct": recall,
        "f1_score_pct": f1,
        "avg_latency_ms": avg_latency,
        "confusion_matrix": {"tp": tp, "tn": tn, "fp": fp, "fn": fn},
        "failures": failures,
    }

    report_path = project_root / "data" / "stress_test_report_150.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report_data, f, indent=2)
    print(f"\nDetailed report saved to: {report_path}")

    return report_data


if __name__ == "__main__":
    run_benchmark()
