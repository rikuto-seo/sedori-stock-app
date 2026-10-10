"""Copy Flask assets to Vercel's public directory without importing the app."""
from pathlib import Path
from shutil import copytree

ROOT = Path(__file__).resolve().parents[1]


def main():
    copytree(ROOT / "static", ROOT / "public" / "static", dirs_exist_ok=True)
    print("Static assets prepared in public/static.")


if __name__ == "__main__":
    main()
