"""Minimal package entry point for ``python -m drosophila_pd``."""

from . import __version__


def main() -> int:
    print(f"drosophila-pd-flygym {__version__}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
