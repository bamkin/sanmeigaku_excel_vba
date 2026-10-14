"""鑑定書の生成（Claude API）。"""
from __future__ import annotations

import datetime as dt
import os
from dataclasses import dataclass, field

from .checker import Issue, check_report
from .landscape import load_landscapes
from .prompt import build_system_prompt, build_user_message, insert_landscapes

DEFAULT_MODEL = os.environ.get("SEISEI_MODEL", "claude-opus-5-5")
DEFAULT_EFFORT = os.environ.get("SEISEI_EFFORT", "high")
MAX_TOKENS = 32000


@dataclass
class GenerationResult:
    markdown: str              # 風景差し込み後
    raw: str                   # モデル出力そのまま
    system_prompt: str
    user_message: str
    model: str
    stop_reason: str | None = None
    usage: dict = field(default_factory=dict)
    issues: list[Issue] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not any(i.level == "error" for i in self.issues)


def build_request(destiny: dict, answers: dict, name: str | None, docs_dir: str,
                  today: dt.date | None = None) -> tuple[str, str]:
    today = today or dt.date.today()
    landscapes = load_landscapes(docs_dir)
    return build_system_prompt(docs_dir), build_user_message(destiny, answers, name, today, landscapes)


def _call_claude(system: str, user: str, model: str, effort: str, client=None) -> tuple[str, str | None, dict]:
    import anthropic

    client = client or anthropic.Anthropic()
    kwargs = dict(
        model=model,
        max_tokens=MAX_TOKENS,
        system=[{"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}],
        messages=[{"role": "user", "content": user}],
        thinking={"type": "adaptive"},
        output_config={"effort": effort},
    )
    if os.environ.get("SEISEI_FALLBACK", "1") != "0":
        # 安全分類器による拒否時に代替モデルへ自動で切り替える（サーバー側フォールバック）
        with client.beta.messages.stream(betas=["server-side-fallback-2026-07-01"], fallbacks="default",
                                         **kwargs) as stream:
            msg = stream.get_final_message()
    else:
        with client.messages.stream(**kwargs) as stream:
            msg = stream.get_final_message()
    text = "".join(b.text for b in msg.content if b.type == "text")
    usage = msg.usage.to_dict() if hasattr(msg.usage, "to_dict") else dict(msg.usage)
    return text, msg.stop_reason, usage


def postprocess(raw: str, destiny: dict, docs_dir: str) -> tuple[str, list[str], list[Issue]]:
    landscapes = load_landscapes(docs_dir)
    md = raw.strip()
    if md.startswith("```"):
        md = md.strip("`").split("\n", 1)[1] if "\n" in md else md
    md, notes = insert_landscapes(md, destiny, landscapes)
    exempt = tuple(landscapes[destiny["rokuju"][k]["number"]].body for k in ("day", "month", "year"))
    return md, notes, check_report(md, docs_dir, exempt)


def generate_report(destiny: dict, answers: dict, name: str | None = None, *, docs_dir: str,
                    model: str = DEFAULT_MODEL, effort: str = DEFAULT_EFFORT,
                    today: dt.date | None = None, client=None) -> GenerationResult:
    system, user = build_request(destiny, answers, name, docs_dir, today)
    raw, stop_reason, usage = _call_claude(system, user, model, effort, client)
    res = GenerationResult(markdown="", raw=raw, system_prompt=system, user_message=user,
                           model=model, stop_reason=stop_reason, usage=usage)
    if stop_reason == "refusal":
        res.issues.append(Issue("error", "refusal", "モデルが生成を拒否した"))
        return res
    if stop_reason == "max_tokens":
        res.issues.append(Issue("error", "max_tokens", "出力が上限で切れた"))
    res.markdown, res.notes, issues = postprocess(raw, destiny, docs_dir)
    res.issues.extend(issues)
    return res
