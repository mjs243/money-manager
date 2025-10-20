# analyzers/wants_manager.py
# manage wants with cooling-off period

import json
from pathlib import Path
from datetime import datetime, timedelta
from models.want import Want, WantStatus

class WantsManager:
    """manage wants with cooling-off period"""

    def __init__(self, config_path: str = "data/wants.json"):
        self.config_path = Path(config_path)
        self.wants = []
        self._load_wants()

    def _load_wants(self):
        """load wants from file"""
        if not self.config_path.exists():
            self.wants = []
            return

        try:
            with open(self.config_path, 'r') as f:
                data = json.load(f)

            self.wants = [
                Want(
                    name=want['name'],
                    price=want['price'],
                    category=want['category'],
                    reason=want['reason'],
                    created=datetime.fromisoformat(want['created']),
                    status=WantStatus(want.get('status', WantStatus.PENDING.value)),
                    check_in_dates=[
                        datetime.fromisoformat(d)
                        for d in want.get('check_in_dates', [])
                    ],
                    purchased_date=(
                        datetime.fromisoformat(want['purchased_date'])
                        if want.get('purchased_date')
                        else None
                    ),
                    notes=want.get('notes', ''),
                )
                for want in data
            ]
            print(f"✅ loaded {len(self.wants)} wants")
        except Exception as e:
            print(f"⚠️  error loading wants: {e}")
            self.wants = []

    def _save_wants(self):
        """save wants to file"""
        data = [
            {
                "name": want.name,
                "price": want.price,
                "category": want.category,
                "reason": want.reason,
                "created": want.created.isoformat(),
                "status": want.status.value,
                "check_in_dates": [
                    d.isoformat() for d in want.check_in_dates
                ],
                "purchased_date": (
                    want.purchased_date.isoformat()
                    if want.purchased_date
                    else None
                ),
                "notes": want.notes,
            }
            for want in self.wants
        ]

        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_path, 'w') as f:
            json.dump(data, f, indent=2)

        print(f"✅ saved {len(self.wants)} wants")

    def add_want(
        self,
        name: str,
        price: float,
        category: str,
        reason: str,
        notes: str = ""
    ) -> Want:
        """add a new want"""
        want = Want(
            name=name,
            price=price,
            category=category,
            reason=reason,
            created=datetime.now(),
            notes=notes,
        )

        self.wants.append(want)
        self._save_wants()
        print(f"✅ added want: {name}")
        return want

    def cancel_want(self, name: str):
        """cancel a want"""
        for want in self.wants:
            if want.name.lower() == name.lower():
                want.cancel()
                self._save_wants()
                print(f"✅ cancelled: {name}")
                return

        print(f"❌ want not found: {name}")

    def purchase_want(self, name: str):
        """mark a want as purchased"""
        for want in self.wants:
            if want.name.lower() == name.lower():
                if want.is_ready_to_purchase:
                    want.purchase()
                    self._save_wants()
                    print(f"✅ purchased: {name}")
                else:
                    print(f"❌ {name} not ready for purchase "
                          f"({want.check_ins_completed}/3 check-ins)")
                return

        print(f"❌ want not found: {name}")

    def perform_check_ins(self):
        """check for wants that need check-ins today"""
        today = datetime.now()
        pending_wants = [
            w for w in self.wants if w.status == WantStatus.PENDING
        ]

        updated = False
        for want in pending_wants:
            # check if due for check-in
            if want.days_until_next_check_in == 0 or want.days_since_creation >= 30:
                want.add_check_in()
                updated = True
                print(f"✅ check-in: {want.name} "
                      f"({want.check_ins_completed}/3)")

        if updated:
            self._save_wants()

        return updated

    def get_pending_wants(self) -> list[Want]:
        """get all pending wants"""
        return [
            w for w in self.wants
            if w.status == WantStatus.PENDING
        ]

    def get_ready_wants(self) -> list[Want]:
        """get wants ready to purchase"""
        return [
            w for w in self.wants
            if w.is_ready_to_purchase
        ]

    def get_completed_wants(self) -> list[Want]:
        """get purchased wants"""
        return [
            w for w in self.wants
            if w.status == WantStatus.PURCHASED
        ]

    def get_cancelled_wants(self) -> list[Want]:
        """get cancelled wants"""
        return [
            w for w in self.wants
            if w.status == WantStatus.CANCELLED
        ]

    def wants_by_category(self) -> dict[str, list[Want]]:
        """organize wants by category"""
        result = {}
        for want in self.wants:
            if want.category not in result:
                result[want.category] = []
            result[want.category].append(want)
        return result

    def total_pending_cost(self) -> float:
        """total cost of all pending wants"""
        return sum(w.price for w in self.get_pending_wants())

    def total_completed_cost(self) -> float:
        """total cost of all purchased wants"""
        return sum(w.price for w in self.get_completed_wants())

    def savings_from_cancellations(self) -> float:
        """money saved by cancelling wants"""
        return sum(w.price for w in self.get_cancelled_wants())

    def cooling_off_stats(self) -> dict:
        """statistics on cooling-off effectiveness"""
        completed = len(self.get_completed_wants())
        cancelled = len(self.get_cancelled_wants())
        pending = len(self.get_pending_wants())

        total = completed + cancelled + pending
        if total == 0:
            return {
                "total_wants": 0,
                "completion_rate": 0,
                "cancellation_rate": 0,
                "savings_from_cooling": 0,
            }

        return {
            "total_wants": total,
            "completion_rate": (completed / total) * 100,
            "cancellation_rate": (cancelled / total) * 100,
            "savings_from_cooling": self.savings_from_cancellations(),
            "total_pending_cost": self.total_pending_cost(),
        }

    def want_report(self) -> str:
        """generate detailed wants report"""
        pending = self.get_pending_wants()
        ready = self.get_ready_wants()
        completed = self.get_completed_wants()
        cancelled = self.get_cancelled_wants()
        stats = self.cooling_off_stats()

        output = []
        output.append("=" * 70)
        output.append("WANTS TRACKING REPORT")
        output.append("=" * 70)

        # stats
        output.append(f"\n--- cooling-off stats ---")
        output.append(f"total wants: {stats['total_wants']}")
        output.append(f"completion rate: {stats['completion_rate']:.1f}%")
        output.append(f"cancellation rate: {stats['cancellation_rate']:.1f}%")
        output.append(f"savings from cooling: ${stats['savings_from_cooling']:,.2f}")
        output.append(f"total pending cost: ${stats['total_pending_cost']:,.2f}")

        # ready to purchase
        if ready:
            output.append(f"\n--- ✅ ready to purchase ({len(ready)}) ---")
            for want in ready:
                output.append(
                    f"  {want.name:.<35} "
                    f"${want.price:>8,.2f} "
                    f"(since {want.created.date()})"
                )
                output.append(f"    reason: {want.reason}")

        # pending with check-ins
        if pending:
            output.append(f"\n--- ⏳ pending wants ({len(pending)}) ---")
            for want in pending:
                check_status = f"({want.check_ins_completed}/3)"
                days_left = want.days_until_next_check_in

                output.append(
                    f"  {want.name:.<35} "
                    f"${want.price:>8,.2f} "
                    f"{check_status:<6} "
                    f"next in {days_left} days"
                )
                output.append(f"    reason: {want.reason}")

        # recently completed
        if completed:
            output.append(f"\n--- 🛒 recently purchased ({len(completed)}) ---")
            for want in sorted(completed, key=lambda x: x.purchased_date, reverse=True)[:5]:
                output.append(
                    f"  {want.name:.<35} "
                    f"${want.price:>8,.2f} "
                    f"({want.purchased_date.date()})"
                )

        # recently cancelled
        if cancelled:
            output.append(f"\n--- ❌ recently cancelled ({len(cancelled)}) ---")
            for want in sorted(cancelled, key=lambda x: x.check_in_dates[-1], reverse=True)[:5]:
                output.append(
                    f"  {want.name:.<35} "
                    f"${want.price:>8,.2f} "
                    f"(cancelled after {want.check_ins_completed} check-ins)"
                )

        output.append("\n" + "=" * 70)
        return "\n".join(output)