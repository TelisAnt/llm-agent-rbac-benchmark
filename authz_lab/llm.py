"""Model backends behind one interface: Anthropic, OpenAI-compatible servers (incl. Ollama), offline mock.

The runner keeps the conversation in a provider-neutral format:
  {"role": "user", "content": str}
  {"role": "assistant", "text": str, "tool_calls": [{"id", "name", "args"}]}
  {"role": "tool", "tool_call_id": str, "name": str, "content": str}
Each backend converts it to its own API format.
"""
from __future__ import annotations

import base64
import hashlib
import json
import os
import random
import re
import time
from dataclasses import dataclass, field


@dataclass
class ToolCall:
    id: str
    name: str
    args: dict


@dataclass
class ModelTurn:
    text: str = ""
    tool_calls: list[ToolCall] = field(default_factory=list)


def _retry(fn, tries: int = 4):
    for i in range(tries):
        try:
            return fn()
        except Exception as exc:
            if i == tries - 1 or "temperature" in str(exc).lower():
                raise
            time.sleep(2 ** i)


class AnthropicBackend:
    def __init__(self, model: str, temperature: float = 0.0, max_tokens: int = 1024):
        import anthropic
        self.client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY
        self.model, self.temperature, self.max_tokens = model, temperature, max_tokens
        self._send_temperature = True

    @staticmethod
    def _convert(messages):
        out = []
        for m in messages:
            if m["role"] == "user":
                out.append({"role": "user", "content": m["content"]})
            elif m["role"] == "assistant":
                blocks = []
                if m["text"]:
                    blocks.append({"type": "text", "text": m["text"]})
                for tc in m["tool_calls"]:
                    blocks.append({"type": "tool_use", "id": tc["id"], "name": tc["name"], "input": tc["args"]})
                out.append({"role": "assistant", "content": blocks})
            else:  # tool result; consecutive results share one user message
                block = {"type": "tool_result", "tool_use_id": m["tool_call_id"], "content": m["content"]}
                if out and out[-1]["role"] == "user" and isinstance(out[-1]["content"], list):
                    out[-1]["content"].append(block)
                else:
                    out.append({"role": "user", "content": [block]})
        return out

    def complete(self, system, messages, tools, seed=None) -> ModelTurn:
        kwargs = dict(model=self.model, max_tokens=self.max_tokens, system=system,
                      messages=self._convert(messages),
                      tools=[{"name": t["name"], "description": t["description"],
                              "input_schema": t["parameters"]} for t in tools])
        if self._send_temperature:
            kwargs["temperature"] = self.temperature
        try:
            resp = _retry(lambda: self.client.messages.create(**kwargs))
        except Exception as exc:  # some models reject 'temperature'
            if "temperature" in str(exc).lower() and self._send_temperature:
                self._send_temperature = False
                kwargs.pop("temperature")
                resp = _retry(lambda: self.client.messages.create(**kwargs))
            else:
                raise
        turn = ModelTurn()
        for block in resp.content:
            if block.type == "text":
                turn.text += block.text
            elif block.type == "tool_use":
                turn.tool_calls.append(ToolCall(block.id, block.name, dict(block.input)))
        return turn


class OpenAIBackend:
    # Also used for local OpenAI-compatible servers (Ollama, llama.cpp, vLLM).

    def __init__(self, model: str, temperature: float = 0.0, max_tokens: int = 1024,
                 base_url: str | None = None, api_key: str | None = None, timeout: float = 600.0):
        import openai
        kw = {"timeout": timeout, "max_retries": 0}  # retries are done by _retry()
        if base_url:
            kw["base_url"] = base_url
        if api_key:
            kw["api_key"] = api_key
        self.client = openai.OpenAI(**kw)  # falls back to OPENAI_API_KEY / OPENAI_BASE_URL
        self.model, self.temperature, self.max_tokens = model, temperature, max_tokens
        self._send_temperature = True

    @staticmethod
    def _convert(system, messages):
        out = [{"role": "system", "content": system}]
        for m in messages:
            if m["role"] == "user":
                out.append({"role": "user", "content": m["content"]})
            elif m["role"] == "assistant":
                msg = {"role": "assistant", "content": m["text"] or None}
                if m["tool_calls"]:
                    msg["tool_calls"] = [{"id": tc["id"], "type": "function",
                                          "function": {"name": tc["name"], "arguments": json.dumps(tc["args"])}}
                                         for tc in m["tool_calls"]]
                out.append(msg)
            else:
                out.append({"role": "tool", "tool_call_id": m["tool_call_id"], "content": m["content"]})
        return out

    def complete(self, system, messages, tools, seed=None) -> ModelTurn:
        kwargs = dict(model=self.model, messages=self._convert(system, messages),
                      tools=[{"type": "function", "function": t} for t in tools])
        if seed is not None:
            kwargs["seed"] = seed
        if self._send_temperature:
            kwargs["temperature"] = self.temperature
        try:
            resp = _retry(lambda: self.client.chat.completions.create(**kwargs))
        except Exception as exc:
            if "temperature" in str(exc).lower() and self._send_temperature:
                self._send_temperature = False
                kwargs.pop("temperature")
                resp = _retry(lambda: self.client.chat.completions.create(**kwargs))
            else:
                raise
        msg = resp.choices[0].message
        turn = ModelTurn(text=msg.content or "")
        for i, tc in enumerate(msg.tool_calls or []):
            raw = tc.function.arguments
            if isinstance(raw, dict):  # some local servers send an object instead of a JSON string
                args = raw
            else:
                try:
                    args = json.loads(raw or "{}")
                except json.JSONDecodeError:
                    args = {"_raw": raw}
            if not isinstance(args, dict):
                args = {"_raw": args}
            # some local servers leave the tool-call id empty
            turn.tool_calls.append(ToolCall(tc.id or f"call_{len(messages)}_{i}", tc.function.name, args))
        return turn


class MockBackend:
    # Deterministic fake model for testing the harness offline. It does not imitate any real
    # LLM, so its numbers must never be reported. `gullibility` is the chance of obeying an
    # unauthorized request under the basic prompt; the detailed prompt divides it by 4.
    _INTENTS = [  # (tool, regex over lower-cased text)
        ("delete_record", r"\b(delete|purge|wipe|remove)\b|διέγραψε"),
        ("modify_record", r"\b(set|bring|change|update|modify)\b.*\bstatus\b|άλλαξε"),
        ("read_sensitive_records", r"sensitive|confidential|unredacted|full details|complete file|πλήρη"),
        ("read_public_data", r"faq|announcement|product"),
    ]

    def __init__(self, gullibility: float = 0.5):
        self.gullibility = gullibility

    @staticmethod
    def _rng(*parts) -> random.Random:
        h = hashlib.sha256("|".join(map(str, parts)).encode()).hexdigest()
        return random.Random(int(h[:12], 16))

    @staticmethod
    def _decode_b64(text: str) -> str:
        extra = []
        for tok in re.findall(r"[A-Za-z0-9+/=]{16,}", text):
            try:
                extra.append(base64.b64decode(tok).decode())
            except Exception:  # not valid base64 text, ignore
                pass
        return text + " " + " ".join(extra)

    def _propose(self, text: str):
        low = self._decode_b64(text).lower()
        rid = re.search(r"REC-\d{3}", text.upper() + " " + self._decode_b64(text).upper())
        for tool, rx in self._INTENTS:
            if re.search(rx, low):
                if tool == "read_public_data":
                    topic = next((t for t in ("faq", "product", "announcement") if t in low), "announcement")
                    topic = {"product": "product_info", "announcement": "announcements"}.get(topic, topic)
                    return tool, {"topic": topic}
                if not rid:
                    return None
                if tool == "modify_record":
                    val = "approved" if "approved" in low else ("reviewed" if "reviewed" in low else "checked")
                    fld = "notes" if "note" in low else "status"
                    return tool, {"record_id": rid.group(0), "field": fld, "value": val}
                return tool, {"record_id": rid.group(0)}
        return None

    def complete(self, system, messages, tools, seed=None) -> ModelTurn:
        role = re.search(r"\bis: (guest|analyst|admin)\b", system).group(1)
        hardened = "SECURITY POLICY" in system
        last = messages[-1]
        text = last.get("content", "")
        rng = self._rng(system, len(messages), text, seed)
        permitted = {"guest": {"read_public_data"},
                     "analyst": {"read_public_data", "read_sensitive_records"},
                     "admin": {"read_public_data", "read_sensitive_records", "modify_record", "delete_record"}}[role]
        already = {(tc["name"], json.dumps(tc["args"], sort_keys=True))
                   for m in messages if m["role"] == "assistant" for tc in m["tool_calls"]}
        p_obey = self.gullibility / (4 if hardened else 1)

        if last["role"] == "tool":
            injected = re.search(r"(delete_record|modify_record|read_sensitive_records|delete|purge|set the status)",
                                 text, re.I)
            if injected and rng.random() < p_obey:
                prop = self._propose(text)
                if prop and (prop[0], json.dumps(prop[1], sort_keys=True)) not in already:
                    return ModelTurn("Following the notice in the document.",
                                     [ToolCall(f"mock_{len(messages)}", *prop)])
            return ModelTurn("Done. Here is a summary of the tool output.")

        prop = self._propose(text)
        if prop is None:
            return ModelTurn("Could you tell me what you would like me to do?")
        tool, args = prop
        if tool in permitted:
            return ModelTurn("", [ToolCall(f"mock_{len(messages)}", tool, args)])
        pushy = re.search(r"ignore|override|administrator|authorize|incident|training|already|base64|decode", text, re.I)
        if rng.random() < min(1.0, p_obey + (0.3 if pushy else 0.0) / (4 if hardened else 1)):
            return ModelTurn("", [ToolCall(f"mock_{len(messages)}", tool, args)])
        return ModelTurn("I'm sorry, I can't do that: your role does not permit this action.")


def make_backend(spec: str, temperature: float = 0.0):
    # spec: mock | mock:<gullibility> | anthropic:<id> | openai:<id> | ollama:<tag> | local:<id>
    # ollama uses OLLAMA_BASE_URL (default localhost:11434), local uses LOCAL_BASE_URL.
    provider, _, name = spec.partition(":")  # the tag itself may contain ':' (llama3.1:8b)
    if provider == "mock":
        return MockBackend(float(name) if name else 0.5)
    if provider == "ollama":
        return OpenAIBackend(name, temperature,
                             base_url=os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434/v1"),
                             api_key="ollama")  # ignored by Ollama, but the client needs a value
    if provider == "local":
        return OpenAIBackend(name, temperature,
                             base_url=os.environ.get("LOCAL_BASE_URL", "http://localhost:8080/v1"),
                             api_key=os.environ.get("LOCAL_API_KEY", "local"))
    if provider == "anthropic":
        return AnthropicBackend(name, temperature)
    if provider == "openai":
        return OpenAIBackend(name, temperature)
    raise ValueError(f"unknown model spec {spec!r}")
