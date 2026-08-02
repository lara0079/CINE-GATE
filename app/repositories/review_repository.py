from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from threading import RLock
from uuid import UUID

from app.domain.models import AuditEvent, ClearanceOutcome, ClearanceReview, DashboardSummary


class ReviewNotFoundError(KeyError):
    pass


class SQLiteReviewRepository:
    def __init__(self, database_path: str) -> None:
        self.database_path = database_path
        if database_path != ":memory:":
            Path(database_path).parent.mkdir(parents=True, exist_ok=True)
        self._lock = RLock()
        self._connection = sqlite3.connect(database_path, check_same_thread=False, timeout=10)
        self._connection.row_factory = sqlite3.Row
        self._connection.execute("PRAGMA foreign_keys = ON")
        self._connection.execute("PRAGMA busy_timeout = 5000")
        if database_path != ":memory:":
            self._connection.execute("PRAGMA journal_mode = WAL")
            self._connection.execute("PRAGMA synchronous = NORMAL")
        self._initialize()

    def _initialize(self) -> None:
        with self._connection:
            self._connection.execute(
                """
                CREATE TABLE IF NOT EXISTS reviews (
                    review_id TEXT PRIMARY KEY,
                    case_id TEXT NOT NULL DEFAULT '',
                    revision_number INTEGER NOT NULL DEFAULT 1,
                    supersedes_review_id TEXT,
                    input_sha256 TEXT NOT NULL DEFAULT '',
                    created_at TEXT NOT NULL,
                    project_name TEXT NOT NULL DEFAULT '',
                    action_type TEXT NOT NULL DEFAULT '',
                    outcome TEXT NOT NULL,
                    human_decision TEXT NOT NULL,
                    review_json TEXT NOT NULL
                )
                """
            )
            columns = {
                row["name"]
                for row in self._connection.execute("PRAGMA table_info(reviews)").fetchall()
            }
            migrations = {
                "project_name": "ALTER TABLE reviews ADD COLUMN project_name TEXT NOT NULL DEFAULT ''",
                "action_type": "ALTER TABLE reviews ADD COLUMN action_type TEXT NOT NULL DEFAULT ''",
                "case_id": "ALTER TABLE reviews ADD COLUMN case_id TEXT NOT NULL DEFAULT ''",
                "revision_number": "ALTER TABLE reviews ADD COLUMN revision_number INTEGER NOT NULL DEFAULT 1",
                "supersedes_review_id": "ALTER TABLE reviews ADD COLUMN supersedes_review_id TEXT",
                "input_sha256": "ALTER TABLE reviews ADD COLUMN input_sha256 TEXT NOT NULL DEFAULT ''",
            }
            for column, statement in migrations.items():
                if column not in columns:
                    self._connection.execute(statement)

            self._connection.execute(
                """
                CREATE TABLE IF NOT EXISTS audit_events (
                    event_id TEXT PRIMARY KEY,
                    review_id TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    actor TEXT NOT NULL,
                    details_json TEXT NOT NULL,
                    FOREIGN KEY(review_id) REFERENCES reviews(review_id) ON DELETE CASCADE
                )
                """
            )
            self._connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_events_review ON audit_events(review_id, created_at)"
            )
            self._connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_reviews_outcome ON reviews(outcome, created_at)"
            )
            self._connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_reviews_project ON reviews(project_name, created_at)"
            )
            self._connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_reviews_case ON reviews(case_id, revision_number)"
            )

    def save(self, review: ClearanceReview) -> None:
        payload = review.model_dump_json()
        with self._lock, self._connection:
            self._connection.execute(
                """
                INSERT INTO reviews(
                    review_id, case_id, revision_number, supersedes_review_id, input_sha256,
                    created_at, project_name, action_type, outcome, human_decision, review_json
                ) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(review_id) DO UPDATE SET
                    case_id=excluded.case_id,
                    revision_number=excluded.revision_number,
                    supersedes_review_id=excluded.supersedes_review_id,
                    input_sha256=excluded.input_sha256,
                    project_name=excluded.project_name,
                    action_type=excluded.action_type,
                    outcome=excluded.outcome,
                    human_decision=excluded.human_decision,
                    review_json=excluded.review_json
                """,
                (
                    str(review.review_id),
                    str(review.case_id),
                    review.revision_number,
                    str(review.supersedes_review_id) if review.supersedes_review_id else None,
                    review.input_sha256,
                    review.created_at.isoformat(),
                    review.action.project_name,
                    review.action.action_type.value,
                    review.outcome.value,
                    review.human_decision,
                    payload,
                ),
            )

    def get(self, review_id: UUID) -> ClearanceReview:
        with self._lock:
            row = self._connection.execute(
                "SELECT review_json FROM reviews WHERE review_id = ?", (str(review_id),)
            ).fetchone()
        if not row:
            raise ReviewNotFoundError(str(review_id))
        return ClearanceReview.model_validate_json(row["review_json"])

    def list(
        self,
        limit: int = 100,
        outcome: ClearanceOutcome | None = None,
        query: str | None = None,
    ) -> list[ClearanceReview]:
        clauses: list[str] = []
        params: list[object] = []
        if outcome:
            clauses.append("outcome = ?")
            params.append(outcome.value)
        if query and query.strip():
            clauses.append("(LOWER(project_name) LIKE ? OR LOWER(action_type) LIKE ?)")
            pattern = f"%{query.strip().lower()}%"
            params.extend([pattern, pattern])
        where = f" WHERE {' AND '.join(clauses)}" if clauses else ""
        params.append(limit)
        sql = f"SELECT review_json FROM reviews{where} ORDER BY created_at DESC LIMIT ?"
        with self._lock:
            rows = self._connection.execute(sql, params).fetchall()
        return [ClearanceReview.model_validate_json(row["review_json"]) for row in rows]

    def list_case(self, case_id: UUID) -> list[ClearanceReview]:
        with self._lock:
            rows = self._connection.execute(
                "SELECT review_json FROM reviews WHERE case_id = ? ORDER BY revision_number ASC",
                (str(case_id),),
            ).fetchall()
        return [ClearanceReview.model_validate_json(row["review_json"]) for row in rows]

    def latest_for_case(self, case_id: UUID) -> ClearanceReview:
        with self._lock:
            row = self._connection.execute(
                """
                SELECT review_json FROM reviews
                WHERE case_id = ? ORDER BY revision_number DESC, created_at DESC LIMIT 1
                """,
                (str(case_id),),
            ).fetchone()
        if not row:
            raise ReviewNotFoundError(str(case_id))
        return ClearanceReview.model_validate_json(row["review_json"])

    def add_event(self, event: AuditEvent) -> None:
        with self._lock, self._connection:
            self._connection.execute(
                """
                INSERT INTO audit_events(event_id, review_id, created_at, event_type, actor, details_json)
                VALUES(?, ?, ?, ?, ?, ?)
                """,
                (
                    str(event.event_id),
                    str(event.review_id),
                    event.created_at.isoformat(),
                    event.event_type,
                    event.actor,
                    json.dumps(event.details, ensure_ascii=False, default=str, sort_keys=True),
                ),
            )

    def list_events(self, review_id: UUID) -> list[AuditEvent]:
        with self._lock:
            rows = self._connection.execute(
                """
                SELECT event_id, review_id, created_at, event_type, actor, details_json
                FROM audit_events WHERE review_id = ? ORDER BY created_at ASC, event_id ASC
                """,
                (str(review_id),),
            ).fetchall()
        return [
            AuditEvent.model_validate(
                {
                    "event_id": row["event_id"],
                    "review_id": row["review_id"],
                    "created_at": row["created_at"],
                    "event_type": row["event_type"],
                    "actor": row["actor"],
                    "details": json.loads(row["details_json"]),
                }
            )
            for row in rows
        ]

    def summary(self) -> DashboardSummary:
        with self._lock:
            total = self._connection.execute("SELECT COUNT(*) AS n FROM reviews").fetchone()["n"]
            cases = self._connection.execute(
                "SELECT COUNT(DISTINCT case_id) AS n FROM reviews WHERE case_id != ''"
            ).fetchone()["n"]
            revisions = self._connection.execute(
                "SELECT COUNT(*) AS n FROM reviews WHERE revision_number > 1"
            ).fetchone()["n"]
            outcomes = {
                row["outcome"]: row["n"]
                for row in self._connection.execute(
                    "SELECT outcome, COUNT(*) AS n FROM reviews GROUP BY outcome"
                ).fetchall()
            }
            decisions = {
                row["human_decision"]: row["n"]
                for row in self._connection.execute(
                    "SELECT human_decision, COUNT(*) AS n FROM reviews GROUP BY human_decision"
                ).fetchall()
            }
        return DashboardSummary(
            total_reviews=total,
            total_cases=cases,
            revision_reviews=revisions,
            cleared=outcomes.get("CLEARED", 0),
            review_required=outcomes.get("REVIEW_REQUIRED", 0),
            blocked=outcomes.get("BLOCKED", 0),
            human_approved=decisions.get("approved", 0),
            human_rejected=decisions.get("rejected", 0),
        )

    def quick_check(self) -> str:
        with self._lock:
            row = self._connection.execute("PRAGMA quick_check").fetchone()
        return str(row[0]) if row else "unknown"
