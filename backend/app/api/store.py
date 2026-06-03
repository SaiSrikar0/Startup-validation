from __future__ import annotations

import csv
import hashlib
from dataclasses import dataclass, field
from pathlib import Path
from threading import RLock

from .schemas import (
    CompetitionAnalysisRequest,
    CompetitionAnalysisResponse,
    CompetitionMatch,
    PredictionRequest,
    PredictionResponse,
    StartupCreate,
    StartupRead,
    StartupUpdate,
)


def _project_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _seed_path() -> Path:
    return _project_root() / "database" / "data" / "cleaned" / "Startups_cleaned.csv"


def _split_values(value: str | None) -> list[str]:
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


def _slugify(value: str) -> str:
    cleaned = "".join(character.lower() if character.isalnum() else "-" for character in value)
    while "--" in cleaned:
        cleaned = cleaned.replace("--", "-")
    return cleaned.strip("-") or "startup"


def _stable_id(company: str, seed: str) -> str:
    digest = hashlib.sha1(seed.encode("utf-8")).hexdigest()[:8]
    return f"{_slugify(company)}-{digest}"


@dataclass
class StartupRecord:
    startup_id: str
    company: str
    status: str
    year_founded: int
    description: str
    categories: list[str] = field(default_factory=list)
    founders: list[str] = field(default_factory=list)
    investors: list[str] = field(default_factory=list)
    funding_rounds: list[str] = field(default_factory=list)
    city: str | None = None
    state: str | None = None
    country: str | None = None

    def to_read_model(self) -> StartupRead:
        return StartupRead(**self.__dict__)


class StartupStore:
    def __init__(self) -> None:
        self._lock = RLock()
        self._items: dict[str, StartupRecord] = {}
        self._load_seed_data()

    def _load_seed_data(self) -> None:
        seed_file = _seed_path()
        if not seed_file.exists():
            return

        with seed_file.open(newline="", encoding="utf-8-sig") as file_handle:
            reader = csv.DictReader(file_handle)
            for index, row in enumerate(reader, start=1):
                company = (row.get("Company") or "").strip()
                if not company:
                    continue

                startup_id = _stable_id(company, f"{company}-{index}")
                self._items[startup_id] = StartupRecord(
                    startup_id=startup_id,
                    company=company,
                    status=(row.get("Satus") or row.get("Status") or "Unknown").strip(),
                    year_founded=int(float(row.get("Year Founded") or 0)),
                    description=(row.get("Description") or "").strip(),
                    categories=_split_values(row.get("Categories")),
                    founders=_split_values(row.get("Founders")),
                    investors=_split_values(row.get("Investors")),
                    funding_rounds=_split_values(row.get("Amounts raised in different funding rounds")),
                    city=(row.get("Headquarters (City)") or None),
                    state=(row.get("Headquarters (US State)") or None),
                    country=(row.get("Headquarters (Country)") or None),
                )

    def list(self) -> list[StartupRecord]:
        with self._lock:
            return list(self._items.values())

    def find_by_company(self, company: str) -> StartupRecord | None:
        name = company.strip().lower()
        for record in self.list():
            if record.company.strip().lower() == name:
                return record
        return None

    def stable_id_for_company(self, company: str) -> str:
        return _stable_id(company, company)

    def get(self, startup_id: str) -> StartupRecord | None:
        with self._lock:
            return self._items.get(startup_id)

    def add(self, payload: StartupCreate) -> StartupRecord:
        with self._lock:
            startup_id = _stable_id(payload.company, f"{payload.company}-{len(self._items) + 1}")
            record = StartupRecord(startup_id=startup_id, **payload.model_dump())
            self._items[startup_id] = record
            return record

    def update(self, startup_id: str, payload: StartupUpdate) -> StartupRecord | None:
        with self._lock:
            record = self._items.get(startup_id)
            if record is None:
                return None

            updates = payload.model_dump(exclude_unset=True)
            for key, value in updates.items():
                if value is not None:
                    setattr(record, key, value)

            if "company" in updates and updates["company"]:
                record.startup_id = _stable_id(record.company, f"{record.company}-{startup_id}")

            self._items[startup_id] = record
            return record

    def delete(self, startup_id: str) -> bool:
        with self._lock:
            return self._items.pop(startup_id, None) is not None

    def search(
        self,
        *,
        status: str | None = None,
        category: str | None = None,
        country: str | None = None,
        limit: int = 25,
        offset: int = 0,
    ) -> tuple[list[StartupRecord], int]:
        def matches(record: StartupRecord) -> bool:
            if status and record.status.lower() != status.lower():
                return False
            if country and (record.country or "").lower() != country.lower():
                return False
            if category and not any(category.lower() in item.lower() for item in record.categories):
                return False
            return True

        with self._lock:
            filtered = [record for record in self._items.values() if matches(record)]
            total = len(filtered)
            return filtered[offset : offset + limit], total

    def predict(self, payload: PredictionRequest) -> PredictionResponse:
        try:
            from ..models.ANN_Model.predictor import predict_with_ann

            return predict_with_ann(payload)
        except Exception:
            pass

        score = 0.28
        factors: list[str] = []

        status = (payload.status or "").lower()
        if status == "operating":
            score += 0.18
            factors.append("Operating status is a positive signal")
        elif status in {"exited", "dead"}:
            score -= 0.20
            factors.append("Non-operating status lowers the likelihood of success")

        if payload.year_founded is not None:
            if payload.year_founded >= 2011:
                score += 0.08
                factors.append("Recent founding year supports momentum")
            else:
                score -= 0.03

        if payload.categories:
            category_score = min(len(payload.categories), 4) * 0.04
            score += category_score
            factors.append(f"Category coverage contributes {category_score:.2f} to the score")

        if payload.founders:
            founder_score = min(len(payload.founders), 5) * 0.02
            score += founder_score
            factors.append(f"Founder team size contributes {founder_score:.2f} to the score")

        if payload.investors:
            investor_score = min(len(payload.investors), 5) * 0.03
            score += investor_score
            factors.append(f"Investor backing contributes {investor_score:.2f} to the score")

        if (payload.country or "").lower() == "usa":
            score += 0.05
            factors.append("US headquarters adds a small location advantage")

        if payload.description:
            score += 0.03
            factors.append("A filled description improves feature completeness")

        score = max(0.0, min(score, 0.99))
        predicted_success = score >= 0.50
        confidence = "high" if score >= 0.75 else "medium" if score >= 0.55 else "low"

        return PredictionResponse(
            company=payload.company,
            predicted_success=predicted_success,
            probability=round(score, 3),
            confidence=confidence,
            factors=factors or ["No strong signals found, using baseline score"],
            model_name="heuristic-fallback",
        )

    def analyze_competition(self, payload: CompetitionAnalysisRequest) -> CompetitionAnalysisResponse:
        try:
            from ..competitor_analysis.competition_service import analyze_with_ml

            return analyze_with_ml(payload, self)
        except Exception:
            pass

        target_categories = {item.lower() for item in payload.categories}
        candidates: list[CompetitionMatch] = []

        for record in self.list():
            if record.company.lower() == payload.company.lower():
                continue

            shared_categories = sorted(
                {
                    category
                    for category in record.categories
                    if category.lower() in target_categories
                }
            )

            score = len(shared_categories) * 0.28
            reasoning: list[str] = []

            if shared_categories:
                reasoning.append(f"Shares categories: {', '.join(shared_categories)}")
            if payload.country and record.country and record.country.lower() == payload.country.lower():
                score += 0.12
                reasoning.append("Same country")
            if payload.state and record.state and record.state.lower() == payload.state.lower():
                score += 0.10
                reasoning.append("Same state")
            if payload.city and record.city and record.city.lower() == payload.city.lower():
                score += 0.08
                reasoning.append("Same city")

            if score > 0:
                candidates.append(
                    CompetitionMatch(
                        startup_id=record.startup_id,
                        company=record.company,
                        score=round(min(score, 1.0), 3),
                        shared_categories=shared_categories,
                        reasoning=reasoning or ["General market overlap"],
                    )
                )

        candidates.sort(key=lambda item: item.score, reverse=True)
        return CompetitionAnalysisResponse(
            company=payload.company,
            top_matches=candidates[: payload.top_n],
            total_candidates=len(candidates),
        )


store = StartupStore()
