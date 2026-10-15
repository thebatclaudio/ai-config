"""
csv_ledger.py

Append and query expense entries in a CSV-based ledger.
Simple interface for budget-coach agent.
"""

import csv
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Optional


@dataclass
class ExpenseEntry:
    """Represents a single expense transaction."""
    date: datetime
    amount: float
    category: str
    description: str
    tags: Optional[List[str]] = None
    currency: str = "USD"

    def to_csv_row(self) -> List[str]:
        """Convert to CSV row."""
        return [
            self.date.isoformat(),
            str(self.amount),
            self.category,
            self.description,
            ",".join(self.tags or []),
            self.currency,
        ]

    @classmethod
    def from_csv_row(cls, row: List[str]) -> "ExpenseEntry":
        """Parse CSV row."""
        date, amount, category, description, tags_str, currency = row
        return cls(
            date=datetime.fromisoformat(date),
            amount=float(amount),
            category=category,
            description=description,
            tags=tags_str.split(",") if tags_str else None,
            currency=currency or "USD",
        )


class ExpenseLedger:
    """Simple CSV-based expense ledger."""

    def __init__(self, path: Path):
        self.path = Path(path)
        self._ensure_file()

    def _ensure_file(self):
        """Create ledger file with headers if it doesn't exist."""
        if not self.path.exists():
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.path, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["date", "amount", "category", "description", "tags", "currency"])

    def add_entry(self, entry: ExpenseEntry) -> None:
        """Append an expense entry to the ledger."""
        with open(self.path, "a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(entry.to_csv_row())

    def read_all(self) -> List[ExpenseEntry]:
        """Read all entries from the ledger."""
        entries = []
        with open(self.path, "r", newline="") as f:
            reader = csv.reader(f)
            next(reader)  # skip header
            for row in reader:
                if row:  # skip empty rows
                    entries.append(ExpenseEntry.from_csv_row(row))
        return entries

    def entries_by_month(self, year: int, month: int) -> List[ExpenseEntry]:
        """Get all entries for a specific month."""
        all_entries = self.read_all()
        return [
            e for e in all_entries
            if e.date.year == year and e.date.month == month
        ]

    def entries_by_category(self, category: str) -> List[ExpenseEntry]:
        """Get all entries in a specific category."""
        all_entries = self.read_all()
        return [e for e in all_entries if e.category.lower() == category.lower()]

    def total_by_category(self, year: int, month: int) -> dict:
        """Get total spending per category for a month."""
        entries = self.entries_by_month(year, month)
        totals = {}
        for entry in entries:
            totals[entry.category] = totals.get(entry.category, 0) + entry.amount
        return totals

    def monthly_total(self, year: int, month: int) -> float:
        """Get total spending for a month."""
        entries = self.entries_by_month(year, month)
        return sum(e.amount for e in entries)
