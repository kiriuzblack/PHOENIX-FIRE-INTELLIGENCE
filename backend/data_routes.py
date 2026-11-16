
import csv
from collections import Counter
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query

router = APIRouter(
    prefix="/api/data",
    tags=["Scientific Data"]
)

DATA_DIR = Path(__file__).resolve().parent / "data"


def read_csv(filename: str) -> list[dict]:
    path = DATA_DIR / filename

    if not path.is_file():
        raise HTTPException(
            status_code=503,
            detail=f"Archivo de datos no disponible: {filename}"
        )

    with path.open(
        "r",
        encoding="utf-8-sig",
        newline=""
    ) as file:
        return list(csv.DictReader(file))


def filter_experiment(rows, experiment):
    if not experiment:
        return rows

    search = experiment.strip().upper()

    return [
        row for row in rows
        if (row.get("experiment") or "")
        .upper()
        .startswith(search)
    ]


@router.get("/summary")
def get_summary():
    experiments = read_csv("integrated_experiments.csv")
    evidence = read_csv("evidence_matrix.csv")
    flags = read_csv("quality_flags.csv")
    saffire = read_csv("saffire_classification.csv")

    counts = Counter(
        row.get("experiment", "Unknown")
        for row in experiments
    )

    return {
        "total_experiment_records": len(experiments),
        "evidence_records": len(evidence),
        "quality_flags": len(flags),
        "saffire_records": len(saffire),
        "by_experiment": dict(sorted(counts.items())),
        "source": "PHOENIX Data Analytics",
        "validation_notice": (
            "Son registros procesados; no todos los valores "
            "o clasificaciones están validados."
        )
    }


@router.get("/experiments")
def get_experiments(
    experiment: str | None = None,
    limit: int = Query(default=50, ge=1, le=500)
):
    rows = read_csv("integrated_experiments.csv")
    rows = filter_experiment(rows, experiment)

    return {
        "total": len(rows),
        "items": rows[:limit]
    }


@router.get("/evidence")
def get_evidence(
    experiment: str | None = None,
    limit: int = Query(default=50, ge=1, le=500)
):
    rows = read_csv("evidence_matrix.csv")
    rows = filter_experiment(rows, experiment)

    return {
        "total": len(rows),
        "items": rows[:limit]
    }


@router.get("/quality-flags")
def get_quality_flags():
    return {
        "items": read_csv("quality_flags.csv")
    }


@router.get("/saffire")
def get_saffire(
    limit: int = Query(default=50, ge=1, le=500)
):
    rows = read_csv("saffire_classification.csv")

    return {
        "total": len(rows),
        "items": rows[:limit]
    }
