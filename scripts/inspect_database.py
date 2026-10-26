"""
TruthLens Database Inspector Utility
Inspect stored analysis records, extracted claims, and rhetorical techniques via CLI.
"""

import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from database.db_manager import list_analyses, get_analysis, get_dashboard_stats


def main():
    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

    print("=" * 70)
    print("TruthLens -- Database Record Inspector")
    print("=" * 70)

    stats = get_dashboard_stats()
    print(f"Total Saved Analyses : {stats['total_analyses']}")
    print(f"Total Factual Claims : {stats['total_claims']}")
    print(f"Total Techniques     : {stats['total_techniques']}")
    print("-" * 70)

    analyses = list_analyses(limit=10)
    if not analyses:
        print("[INFO] No records currently stored in the database.")
        print("       Open http://127.0.0.1:8765 to analyze your first news story.")
        return

    print("Recent Analyses (Top 10):")
    for idx, item in enumerate(analyses, 1):
        print(f"\n[{idx}] ID: {item['id']}")
        print(f"    Headline: {item['title']}")
        print(f"    Language: {item['language']} | Claims: {item['claims_count']} | Techniques: {item['techniques_count']}")
        print(f"    Analyzed: {item['created_at']}")
        if item.get("source_url"):
            print(f"    URL:      {item['source_url']}")

    print("\n" + "=" * 70)


if __name__ == "__main__":
    main()
