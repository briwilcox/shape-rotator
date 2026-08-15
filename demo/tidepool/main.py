"""Tidepool, a tiny aquarium monitoring service (demo codebase).

This project exists so you can try shape-rotator without pointing it at
your own code. It is intentionally small but has a real import structure:
entrypoints, a middle service layer, and a shared core.
"""
from config import load_config
from routes import build_routes


def main():
    cfg = load_config()
    routes = build_routes(cfg)
    print(f"tidepool listening on port {cfg['port']} with {len(routes)} routes")
    for path, handler in routes.items():
        print(f"  {path} -> {handler.__name__}")


if __name__ == "__main__":
    main()
