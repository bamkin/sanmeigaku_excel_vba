"""六十の風景 — 算出層（決定的・LLM不使用・依存なしの純Python）。

入口は :func:`sanmei.destiny.compute_destiny`。
"""
from .destiny import compute_destiny  # noqa: F401

__all__ = ["compute_destiny"]
