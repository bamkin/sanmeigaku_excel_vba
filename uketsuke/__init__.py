"""受付：申込 → 決済 → 生成 → 承認 → 送付（開発順序4）。

周辺サービス（決済・メール・生成）はアダプタ越し。鍵が無ければダミーで全導線が通る（uketsuke/adapters.py）。
データは SQLite 一つ（uketsuke/db.py）。Web の経路は uketsuke/routes.py（shindan.app に組み込む）。
"""
from .flow import approve, create_order, mark_paid, regenerate, run_generation, send  # noqa: F401
