#!/usr/bin/env python3
"""
Validate that all skill scripts can import their dependencies.
Run this after any changes to catch broken imports early.
"""
import sys
import os
import importlib.util

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
SKILLS_DIR = os.path.join(PROJECT_DIR, "skills")

# Map of skill scripts and their expected imports
SKILL_IMPORTS = {
    "skills/game-price/scripts/price_lookup.py": [
        "def get_gg_price",
        "def get_itad_price",
        "def search_steam",
    ],
    "skills/game-watchlist/scripts/watchlist_manager.py": [
        "price_lookup",
        "database",
    ],
    "skills/steam-link/scripts/steam_linker.py": [
        "database",
    ],
    "skills/common-games/scripts/common_games.py": [
        "database",
    ],
    "skills/game-news/scripts/news_fetcher.py": [
        "database",
    ],
    "skills/should-buy/scripts/should_buy.py": [
        "price_lookup",
        "common_games",
        "database",
    ],
    "skills/game-suggest/scripts/game_suggester.py": [
        "price_lookup",
        "database",
    ],
    "skills/weekly-recap/scripts/recap_generator.py": [
        "database",
    ],
    "skills/weekly-recap/scripts/refresh_playtime.py": [
        "database",
    ],
}

CRITICAL_FILES = {
    "db/database.py": "SQLite schema + DB operations",
    "skills/_load_env.py": "Environment variable loader",
    ".env.example": "Template for .env",
}


def check_critical_files():
    """Verify critical files exist."""
    print("📁 Checking critical files...")
    missing = []
    for filepath, description in CRITICAL_FILES.items():
        full_path = os.path.join(PROJECT_DIR, filepath)
        if os.path.exists(full_path):
            print(f"  ✓ {filepath}")
        else:
            print(f"  ✗ {filepath} — {description}")
            missing.append(filepath)
    return len(missing) == 0


def check_syntax():
    """Compile-check all Python files."""
    print("\n🐍 Checking Python syntax...")
    errors = []
    for root, dirs, files in os.walk(SKILLS_DIR):
        # Skip venv
        if "venv" in root or "__pycache__" in root:
            continue
        for file in files:
            if file.endswith(".py"):
                filepath = os.path.join(root, file)
                try:
                    with open(filepath) as f:
                        compile(f.read(), filepath, "exec")
                    rel_path = os.path.relpath(filepath, PROJECT_DIR)
                    print(f"  ✓ {rel_path}")
                except SyntaxError as e:
                    rel_path = os.path.relpath(filepath, PROJECT_DIR)
                    print(f"  ✗ {rel_path}: {e}")
                    errors.append((rel_path, str(e)))
    return len(errors) == 0


def check_imports():
    """Verify skill scripts can import their dependencies (without running them)."""
    print("\n📦 Checking imports...")
    # This is a static check — we're not actually running skills
    errors = []
    for skill_path, required_imports in SKILL_IMPORTS.items():
        full_path = os.path.join(PROJECT_DIR, skill_path)
        if not os.path.exists(full_path):
            print(f"  ✗ {skill_path} — FILE NOT FOUND")
            errors.append((skill_path, "File not found"))
            continue

        with open(full_path) as f:
            content = f.read()
            missing = []
            for imp in required_imports:
                # Support both "import X" and "def X" patterns
                if imp.startswith("def "):
                    if imp not in content:
                        missing.append(imp)
                else:
                    if f"from {imp} import" not in content and f"import {imp}" not in content:
                        missing.append(imp)

            if missing:
                print(f"  ✗ {skill_path} — missing: {', '.join(missing)}")
                errors.append((skill_path, f"Missing imports: {missing}"))
            else:
                print(f"  ✓ {skill_path}")
    return len(errors) == 0


def main():
    print("=" * 60)
    print("🔍 Dependency Check")
    print("=" * 60)

    results = {
        "Critical files": check_critical_files(),
        "Python syntax": check_syntax(),
        "Import declarations": check_imports(),
    }

    print("\n" + "=" * 60)
    print("📊 Results")
    print("=" * 60)
    for check, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{check}: {status}")

    all_passed = all(results.values())
    if all_passed:
        print("\n✅ All checks passed!")
        return 0
    else:
        print("\n❌ Some checks failed. Review output above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
