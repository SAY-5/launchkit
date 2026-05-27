"""Benchmark the tenant-scoped notes list endpoint at scale.

Seeds two tenants with many notes each, then times repeated authenticated list
requests for one tenant. Reports the median and p95 latency in milliseconds and
writes the result as JSON so CI can compare against a stored baseline.

Run: python -m bench.bench_notes_list --notes 2000 --iterations 200
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
import time
from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.db import Base, get_db
from app.core.security import create_access_token, hash_password
from app.main import create_app
from app.models import Note, Tenant, User


def _seed(session, notes_per_tenant: int) -> str:
    tenants = []
    for name in ("Acme", "Globex"):
        tenant = Tenant(name=name)
        session.add(tenant)
        session.flush()
        session.add(
            User(
                tenant_id=tenant.id,
                email=f"owner@{name.lower()}.example",
                password_hash=hash_password("password123"),
            )
        )
        session.bulk_save_objects(
            [
                Note(tenant_id=tenant.id, title=f"{name} note {i}", body="x" * 64)
                for i in range(notes_per_tenant)
            ]
        )
        tenants.append(tenant)
    session.commit()
    primary = tenants[0]
    user = session.query(User).filter(User.tenant_id == primary.id).first()
    return create_access_token(str(user.id), primary.id)


def run(notes: int, iterations: int) -> dict:
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine, future=True)()

    token = _seed(session, notes)
    app = create_app()
    app.dependency_overrides[get_db] = lambda: session
    client = TestClient(app)
    headers = {"Authorization": f"Bearer {token}"}

    # Warm up.
    for _ in range(5):
        client.get("/notes", headers=headers)

    samples_ms = []
    for _ in range(iterations):
        start = time.perf_counter()
        resp = client.get("/notes", headers=headers)
        samples_ms.append((time.perf_counter() - start) * 1000)
        assert resp.status_code == 200
        assert len(resp.json()) == notes

    samples_ms.sort()
    return {
        "notes_per_tenant": notes,
        "iterations": iterations,
        "median_ms": round(statistics.median(samples_ms), 3),
        "p95_ms": round(samples_ms[int(len(samples_ms) * 0.95) - 1], 3),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--notes", type=int, default=2000)
    parser.add_argument("--iterations", type=int, default=200)
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args()

    result = run(args.notes, args.iterations)
    print(json.dumps(result, indent=2))
    if args.out:
        args.out.write_text(json.dumps(result, indent=2) + "\n")
    sys.exit(0)


if __name__ == "__main__":
    main()
