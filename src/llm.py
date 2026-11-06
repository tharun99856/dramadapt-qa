"""OpenAI-compatible client with JSON validation and one retry. Malformed output is an error, never a silent pass."""

from __future__ import annotations

import hashlib
import json
import re
import time

from .config import api_key
from .runlog import RunLog


class LLMError(RuntimeError):
    pass


def parse_json_lenient(text: str):
    if text is None:
        raise LLMError("empty model response")
    body = text.strip()
    if body.startswith("```"):
        body = re.sub(r"^```[a-zA-Z]*\n?", "", body)
        body = re.sub(r"\n?```$", "", body)
    try:
        return json.loads(body)
    except json.JSONDecodeError:
        pass
    start = min((i for i in (body.find("{"), body.find("[")) if i != -1), default=-1)
    end = max(body.rfind("}"), body.rfind("]"))
    if start != -1 and end > start:
        try:
            return json.loads(body[start : end + 1])
        except json.JSONDecodeError as exc:
            raise LLMError(f"model returned text that is not valid JSON: {exc}") from exc
    raise LLMError("model returned no JSON object at all")


class LLM:
    def __init__(self, cfg: dict, log: RunLog, model: str | None = None, reuse: bool = True):
        self.cfg = cfg
        self.log = log
        self.provider = cfg["provider"]
        self.model = model or self.provider["model"]
        self.reuse = reuse and bool(self.provider.get("reuse_logged_calls", True))
        self.reused = 0
        self._client = None
        self._answers: dict[str, object] | None = None

    def _key(self, system: str, user: str) -> str:
        return hashlib.sha256(f"{self.model}\n{system}\n{user}".encode("utf-8")).hexdigest()[:24]

    def _cached(self, system: str, user: str):
        """The answer to this exact call, if this phase already paid for it."""
        if self._answers is None:
            self._answers = {}
            for entry in self.log.entries:
                if entry.get("response") and not entry.get("error") and entry.get("model") == self.model:
                    try:
                        data = parse_json_lenient(entry["response"])
                    except LLMError:
                        continue
                    self._answers[self._key(entry.get("system", ""), entry.get("user", ""))] = data
        return self._answers.get(self._key(system, user))

    def client(self):
        if self._client is None:
            try:
                from openai import OpenAI
            except ImportError as exc:
                raise LLMError("the openai package is not installed (pip install openai)") from exc
            self._client = OpenAI(
                base_url=self.provider.get("base_url") or None,
                api_key=api_key(self.cfg),
                timeout=float(self.provider.get("request_timeout_seconds", 180)),
            )
        return self._client

    def _wait_seconds(self, exc, try_no: int) -> float:
        """Use the provider's own reset hint when it sends one, otherwise ramp the wait.

        A Groq 429 on the daily token budget answers with `retry-after: 398`. Waiting 20 s in that
        case is a guaranteed second failure, so the hint wins - but a per-batch ceiling keeps one
        stubborn scene from eating the whole run.
        """
        headers = getattr(getattr(exc, "response", None), "headers", None) or {}
        ceiling = min(600.0, float(self.provider.get("max_wait_seconds_per_batch", 600)))
        for name in ("retry-after", "x-ratelimit-reset"):
            raw = headers.get(name) if hasattr(headers, "get") else None
            try:
                if raw is not None:
                    return max(1.0, min(float(raw), ceiling))
            except (TypeError, ValueError):
                continue
        base = float(self.provider.get("rate_limit_wait_seconds", 20))
        return min(base * (try_no + 1), ceiling)

    def _create(self, client, kwargs, messages):
        """JSON mode if the provider supports it; backoff on rate limit; everything else is a real error."""
        attempts = int(self.provider.get("rate_limit_retries", 4))
        budget = float(self.provider.get("max_wait_seconds_per_batch", 600))
        spent, last_status = 0.0, None
        for try_no in range(attempts):
            try:
                return client.chat.completions.create(**kwargs, response_format={"type": "json_object"})
            except Exception as exc:
                status = getattr(exc, "status_code", None)
                if status == 400 and "response_format" in str(exc):
                    return client.chat.completions.create(**kwargs)
                if status in (429, 503):
                    last_status = str(status)
                    wait = self._wait_seconds(exc, try_no)
                    if try_no + 1 >= attempts or spent + wait > budget:
                        break  # no attempt left, or the batch's wait budget is gone
                    spent += wait
                    time.sleep(wait)
                    continue
                raise LLMError(f"{type(exc).__name__} from {self.provider.get('base_url')} "
                               f"model {self.model}: {str(exc)[:220]}") from exc
        detail = f"{last_status} after {spent:.0f}s of waits" if last_status else "no attempt made"
        raise LLMError(f"still throttled ({detail}) - "
                       "lower batching.max_lines_per_request, raise provider.rate_limit_wait_seconds, "
                       "or run this check again later: the free tier caps tokens per day, "
                       "and a refused batch now costs only that batch")

    def raw(self, system: str, user: str) -> tuple[str, dict]:
        messages = [{"role": "system", "content": system}, {"role": "user", "content": user}]
        client = self.client()
        kwargs = {
            "model": self.model,
            "messages": messages,
            "temperature": float(self.provider.get("temperature", 0)),
            "max_tokens": int(self.provider.get("max_output_tokens", 3000)),
        }
        resp = self._create(client, kwargs, messages)
        text = (resp.choices[0].message.content or "").strip()
        finish = getattr(resp.choices[0], "finish_reason", None)
        if finish in ("length", "max_tokens") or not text:
            raise LLMError(f"response was cut off at max_output_tokens "
                           f"({self.provider.get('max_output_tokens')}) with finish_reason={finish}; "
                           "raise that limit or lower the batch size")
        usage = {}
        if getattr(resp, "usage", None):
            usage = {
                "prompt_tokens": getattr(resp.usage, "prompt_tokens", 0) or 0,
                "completion_tokens": getattr(resp.usage, "completion_tokens", 0) or 0,
            }
        return text, usage

    def ask_json(self, system: str, user: str, *, kind: str, batch: str):
        """One logical call, logged. Retries once on malformed JSON, then raises.

        A batch whose exact prompt is already in this phase's call log is answered from the log.
        The free tier throttles by tokens per minute, so a 36-request run has to be finishable in
        pieces; re-paying for a batch that already answered is what makes it unfinishable. The
        reused batch is not recorded again, so the token totals count every request exactly once.
        """
        cached = self._cached(system, user) if self.reuse else None
        if cached is not None:
            self.reused += 1
            return cached
        text, usage = self.raw(system, user)
        self.log.record(kind=kind, batch=batch, model=self.model, prompt={"system": system, "user": user},
                        response_text=text, usage=usage)
        try:
            return parse_json_lenient(text)
        except LLMError as first:
            retry_system = system + "\nReturn ONLY a valid JSON object. No prose, no code fences."
            text2, usage2 = self.raw(retry_system, user)
            self.log.record(kind=kind + "_retry", batch=batch, model=self.model,
                            prompt={"system": retry_system, "user": user}, response_text=text2, usage=usage2,
                            note=f"first response was not valid JSON: {first}")
            try:
                return parse_json_lenient(text2)
            except LLMError as second:
                raise LLMError(f"{kind} for batch {batch}: model output unusable after retry ({second})") from second
