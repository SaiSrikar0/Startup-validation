from __future__ import annotations

import csv
import hashlib
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from threading import RLock
from typing import Any

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
from ..supabase_client import get_supabase_client


def _project_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _seed_path() -> Path:
    return _project_root() / "database" / "data" / "cleaned" / "Startups_cleaned.csv"


def _split_values(value: str | None) -> list[str]:
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


def _list_from_db(value: str | list[str] | None) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if item is not None]
    return [item.strip() for item in str(value).split(",") if item.strip()]


def _to_db_list(value: list[str]) -> str:
    return ", ".join(value)


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
        self._supabase = get_supabase_client()
        self._table = self._supabase.table("startups") if self._supabase else None
        self._prediction_table = self._supabase.table("predictions") if self._supabase else None
        self._load_data()

    def _load_data(self) -> None:
        if self._table is not None:
            try:
                response = self._table.select("*").execute()
                if not response.error and response.data:
                    self._load_rows(response.data)
                    return
            except Exception:
                pass

        self._load_seed_data()

    def _load_seed_data(self) -> None:
        self._items = {}
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
                    categories=_list_from_db(row.get("Categories")),
                    founders=_list_from_db(row.get("Founders")),
                    investors=_list_from_db(row.get("Investors")),
                    funding_rounds=_list_from_db(row.get("Amounts raised in different funding rounds")),
                    city=(row.get("Headquarters (City)") or None),
                    state=(row.get("Headquarters (US State)") or None),
                    country=(row.get("Headquarters (Country)") or None),
                )

    def _to_db_record(self, record: StartupRecord) -> dict[str, Any]:
        return {
            "startup_id": record.startup_id,
            "company": record.company,
            "status": record.status,
            "year_founded": record.year_founded,
            "description": record.description,
            "categories": _to_db_list(record.categories),
            "founders": _to_db_list(record.founders),
            "investors": _to_db_list(record.investors),
            "funding_rounds": _to_db_list(record.funding_rounds),
            "city": record.city,
            "state": record.state,
            "country": record.country,
        }

    def _insert_to_db(self, record: StartupRecord) -> None:
        if self._table is None:
            return
        try:
            self._table.insert(self._to_db_record(record)).execute()
        except Exception:
            pass

    def _update_db(self, record: StartupRecord) -> None:
        if self._table is None:
            return
        try:
            self._table.update(self._to_db_record(record)).eq("startup_id", record.startup_id).execute()
        except Exception:
            pass

    def _delete_from_db(self, startup_id: str) -> None:
        if self._table is None:
            return
        try:
            self._table.delete().eq("startup_id", startup_id).execute()
        except Exception:
            pass

    def _to_prediction_record(self, payload: PredictionRequest, response: PredictionResponse) -> dict[str, Any]:
        return {
            "prediction_id": _stable_id(payload.company, datetime.utcnow().isoformat()),
            "company": payload.company,
            "status": payload.status,
            "year_founded": payload.year_founded,
            "description": payload.description,
            "categories": _to_db_list(payload.categories),
            "founders": _to_db_list(payload.founders),
            "investors": _to_db_list(payload.investors),
            "funding_rounds": _to_db_list(payload.funding_rounds),
            "city": payload.city,
            "state": payload.state,
            "country": payload.country,
            "predicted_success": response.predicted_success,
            "probability": response.probability,
            "confidence": response.confidence,
            "model_name": response.model_name,
            "created_at": datetime.utcnow().isoformat(),
        }

    def _persist_prediction(self, payload: PredictionRequest, response: PredictionResponse) -> None:
        if self._prediction_table is None:
            return
        try:
            self._prediction_table.insert(self._to_prediction_record(payload, response)).execute()
        except Exception:
            pass

    def _load_rows(self, rows: list[dict[str, Any]]) -> None:
        self._items = {}
        for row in rows:
            company = (row.get("company") or row.get("Company") or "").strip()
            if not company:
                continue

            startup_id = row.get("startup_id") or _stable_id(company, company)
            self._items[startup_id] = StartupRecord(
                startup_id=startup_id,
                company=company,
                status=(row.get("status") or row.get("Satus") or "Unknown").strip(),
                year_founded=int(float(row.get("year_founded") or row.get("Year Founded") or 0)),
                description=(row.get("description") or row.get("Description") or "").strip(),
                categories=_list_from_db(row.get("categories") or row.get("Categories")),
                founders=_list_from_db(row.get("founders") or row.get("Founders")),
                investors=_list_from_db(row.get("investors") or row.get("Investors")),
                funding_rounds=_list_from_db(row.get("funding_rounds") or row.get("Amounts raised in different funding rounds")),
                city=(row.get("city") or row.get("Headquarters (City)") or None),
                state=(row.get("state") or row.get("Headquarters (US State)") or None),
                country=(row.get("country") or row.get("Headquarters (Country)") or None),
            )
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
            self._insert_to_db(record)
            return record

    def update(self, startup_id: str, payload: StartupUpdate) -> StartupRecord | None:
        with self._lock:
            record = self._items.get(startup_id)
            if record is None:
                return None

            updates = payload.model_dump(exclude_unset=True)
            original_id = record.startup_id
            for key, value in updates.items():
                if value is not None:
                    setattr(record, key, value)

            if "company" in updates and updates["company"]:
                record.startup_id = _stable_id(record.company, f"{record.company}-{startup_id}")
                self._items.pop(original_id, None)

            self._items[record.startup_id] = record
            if record.startup_id != original_id:
                self._insert_to_db(record)
                self._delete_from_db(original_id)
            else:
                self._update_db(record)
            return record

    def delete(self, startup_id: str) -> bool:
        with self._lock:
            exists = self._items.pop(startup_id, None) is not None
            if exists:
                self._delete_from_db(startup_id)
            return exists

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

        print("\n" + "=" * 60)
        print("PREDICTION REQUEST")
        print(payload.model_dump())
        print("=" * 60)

        try:
            print("Loading ANN predictor...")

            from ..models.ANN_Model.predictor import (
                predict_with_ann,
                is_available,
            )

            print("Checking ANN availability...")

            if is_available():
                print("ANN AVAILABLE")

                response = predict_with_ann(payload)

                print("ANN PREDICTION SUCCESS")
                print("Probability:", response.probability)
                print("Model:", response.model_name)

                self._persist_prediction(payload, response)

                return response

            print("ANN NOT AVAILABLE")

        except Exception as e:

            print("\nANN ERROR OCCURRED")
            print(type(e).__name__)
            print(str(e))

            import traceback
            traceback.print_exc()

        print("\nUSING HEURISTIC FALLBACK MODEL")

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
            factors.append(
                f"Category coverage contributes {category_score:.2f} to the score"
            )

        if payload.founders:
            founder_score = min(len(payload.founders), 5) * 0.02
            score += founder_score
            factors.append(
                f"Founder team size contributes {founder_score:.2f} to the score"
            )

        if payload.investors:
            investor_score = min(len(payload.investors), 5) * 0.03
            score += investor_score
            factors.append(
                f"Investor backing contributes {investor_score:.2f} to the score"
            )

        if (payload.country or "").lower() == "usa":
            score += 0.05
            factors.append(
                "US headquarters adds a small location advantage"
            )

        if payload.description:
            score += 0.03
            factors.append(
                "A filled description improves feature completeness"
            )

        score = max(0.0, min(score, 0.99))

        predicted_success = score >= 0.50

        confidence = (
            "high"
            if score >= 0.75
            else "medium"
            if score >= 0.55
            else "low"
        )

        response = PredictionResponse(
            company=payload.company,
            predicted_success=predicted_success,
            probability=round(score, 3),
            confidence=confidence,
            factors=factors or [
                "No strong signals found, using baseline score"
            ],
            model_name="heuristic-fallback",
        )

        self._persist_prediction(payload, response)

        return response

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
