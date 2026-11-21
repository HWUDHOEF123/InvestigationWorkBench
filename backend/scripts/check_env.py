"""Environment self-check for the IntelGraph backend.

Run from backend/:  python scripts/check_env.py
Reads backend/.env and verifies each dependency independently, so one missing
key does not hide the status of the others. Exit code 0 only if all pass.
"""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

ENV_PATH = Path(__file__).resolve().parent.parent / ".env"


def load_env(path: Path) -> None:
    if not path.exists():
        print(f"[FAIL] {path} not found. Copy .env.example to .env first.")
        sys.exit(1)
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip())


results: list[tuple[str, bool, str]] = []

# Thinking level -> extra_body for each provider profile (docs/requirements/07-architecture.md).
# DeepSeek enables thinking by default, so every call must state a level explicitly.
# Mirrors what the app's provider profile will do; kept inline so this script has no app imports.
THINKING_PROFILES: dict[str, dict[str, dict]] = {
    "deepseek": {
        "off": {"thinking": {"type": "disabled"}},
        "low": {"reasoning_effort": "low"},
        "medium": {"reasoning_effort": "medium"},
        "high": {"reasoning_effort": "high"},
    },
}


def record(name: str, ok: bool, detail: str) -> None:
    results.append((name, ok, detail))
    print(f"[{'PASS' if ok else 'FAIL'}] {name}: {detail}")


def check_python() -> None:
    ok = sys.version_info >= (3, 11)
    record("python", ok, sys.version.split()[0])


def check_graphiti_import() -> None:
    # Telemetry must be off before graphiti_core is imported (07-architecture).
    telemetry = os.environ.get("GRAPHITI_TELEMETRY_ENABLED", "true").lower()
    if telemetry not in ("false", "0", "no", "off"):
        record(
            "graphiti telemetry",
            False,
            f"GRAPHITI_TELEMETRY_ENABLED={telemetry}; must be false",
        )
    try:
        from importlib.metadata import version

        import graphiti_core  # noqa: F401

        v = version("graphiti-core")
        record("graphiti-core", v == "0.31.2", f"version {v} (pinned 0.31.2)")
    except Exception as exc:  # noqa: BLE001 - a diagnostic reports any failure
        record("graphiti-core", False, repr(exc))


async def check_neo4j() -> None:
    from neo4j import AsyncGraphDatabase

    uri = os.environ.get("NEO4J_URI", "")
    try:
        driver = AsyncGraphDatabase.driver(
            uri,
            auth=(
                os.environ.get("NEO4J_USER", ""),
                os.environ.get("NEO4J_PASSWORD", ""),
            ),
        )
        async with driver:
            records, _, _ = await driver.execute_query(
                "CALL dbms.components() YIELD name, versions, edition "
                "RETURN name, versions[0] AS version, edition"
            )
            row = records[0]
            version = row["version"]
            major = int(version.split(".")[0])
            ok = major >= 2025 or tuple(int(p) for p in version.split(".")[:2]) >= (
                5,
                26,
            )
            record("neo4j", ok, f"{row['name']} {version} {row['edition']} at {uri}")
    except Exception as exc:  # noqa: BLE001 - a diagnostic reports any failure
        record("neo4j", False, f"{uri}: {exc!r}")


async def check_llm() -> None:
    from openai import AsyncOpenAI

    key = os.environ.get("LLM_API_KEY", "")
    if not key:
        record("llm", False, "LLM_API_KEY is empty")
        return
    model = os.environ.get("LLM_MODEL", "")
    profile = os.environ.get("LLM_PROVIDER_PROFILE", "deepseek")
    level = "off"  # the self-check always runs at thinking level off
    if profile not in THINKING_PROFILES:
        record("llm", False, f"unknown LLM_PROVIDER_PROFILE={profile!r}")
        return
    extra_body = THINKING_PROFILES[profile].get(level)
    try:
        client = AsyncOpenAI(api_key=key, base_url=os.environ.get("LLM_BASE_URL"))
        resp = await client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": '只输出 JSON：{"ok": true}'}],
            response_format={"type": "json_object"},
            temperature=0,
            max_tokens=20,
            extra_body=extra_body,
        )
        text = (resp.choices[0].message.content or "").strip()
        details = resp.usage.completion_tokens_details if resp.usage else None
        reasoning = (details.reasoning_tokens or 0) if details else 0
        ok = bool(text) and reasoning == 0
        record(
            "llm",
            ok,
            f"{model} replied {text[:40]!r} (json_object, profile={profile}, "
            f"thinking={level}, reasoning_tokens={reasoning})",
        )
    except Exception as exc:  # noqa: BLE001 - a diagnostic reports any failure
        record("llm", False, f"{model}: {exc!r}")


async def check_embedding() -> None:
    from openai import AsyncOpenAI

    key = os.environ.get("EMBEDDING_API_KEY", "")
    if not key:
        record("embedding", False, "EMBEDDING_API_KEY is empty")
        return
    model = os.environ.get("EMBEDDING_MODEL", "")
    expected = int(os.environ.get("EMBEDDING_DIM", "0") or 0)
    try:
        client = AsyncOpenAI(api_key=key, base_url=os.environ.get("EMBEDDING_BASE_URL"))
        # No `dimensions` argument on purpose: Graphiti's OpenAIEmbedder does not send one and
        # truncates to EMBEDDING_DIM, so the model's native dimension must equal EMBEDDING_DIM.
        resp = await client.embeddings.create(
            model=model, input=["黄仁勋", "Jensen Huang", "苹果公司"]
        )
        vecs = [d.embedding for d in resp.data]
        dim = len(vecs[0])

        def cos(a: list[float], b: list[float]) -> float:
            dot = sum(x * y for x, y in zip(a, b))
            na = sum(x * x for x in a) ** 0.5
            nb = sum(y * y for y in b) ** 0.5
            return dot / (na * nb)

        same, other = cos(vecs[0], vecs[1]), cos(vecs[0], vecs[2])
        record(
            "embedding",
            dim == expected,
            f"{model} dim={dim} (expected {expected}); "
            f"cos(黄仁勋, Jensen Huang)={same:.3f} vs cos(黄仁勋, 苹果公司)={other:.3f}",
        )
    except Exception as exc:  # noqa: BLE001 - a diagnostic reports any failure
        record("embedding", False, f"{model}: {exc!r}")


async def main() -> int:
    load_env(ENV_PATH)
    check_python()
    check_graphiti_import()
    await check_neo4j()
    await check_llm()
    await check_embedding()
    failed = [name for name, ok, _ in results if not ok]
    print()
    print("ALL PASS" if not failed else f"FAILED: {', '.join(failed)}")
    return 0 if not failed else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
