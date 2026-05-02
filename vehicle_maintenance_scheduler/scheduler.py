"""
Vehicle Maintenance Scheduler
Solves the 0/1 knapsack problem for optimal vehicle maintenance scheduling
"""

from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from logging_middleware import LoggerService


@dataclass
class Vehicle:
    """Vehicle maintenance task"""
    task_id: str
    duration: int  # in hours
    impact: int    # operational importance score


@dataclass
class Depot:
    """Service depot with mechanic budget"""
    id: int
    mechanic_hours: int


class VehicleMaintenanceScheduler:
    """
    Optimal vehicle maintenance scheduler using dynamic programming.
    Solves the weighted 0/1 knapsack problem to maximize operational impact
    within available mechanic hours.
    """

    def __init__(self, logger_service: Optional[LoggerService] = None):
        self.logger_service = logger_service

    def _log(self, level: str, message: str, context: Optional[Dict] = None):
        """Log using the logging middleware"""
        if self.logger_service:
            method = getattr(self.logger_service, level, self.logger_service.info)
            method(
                stack="backend",
                package="service",
                message=message,
                context=context or {}
            )

    def schedule_maintenance(
        self,
        vehicles: List[Vehicle],
        mechanic_hours: int
    ) -> Tuple[List[Vehicle], int, int]:
        """
        Find optimal subset of vehicles to maintain within budget.

        Args:
            vehicles: List of vehicles requiring maintenance
            mechanic_hours: Available mechanic hours budget

        Returns:
            Tuple of (selected_vehicles, total_impact, total_hours)
        """
        self._log(
            "info",
            f"Starting maintenance scheduling for {len(vehicles)} vehicles with {mechanic_hours} hours budget"
        )

        if not vehicles or mechanic_hours <= 0:
            self._log("warning", "Invalid input: no vehicles or budget")
            return [], 0, 0

        n = len(vehicles)
        
        # DP table: dp[i][w] = max impact using first i vehicles with w hours
        dp = [[0 for _ in range(mechanic_hours + 1)] for _ in range(n + 1)]

        # Fill DP table
        for i in range(1, n + 1):
            vehicle = vehicles[i - 1]
            for w in range(mechanic_hours + 1):
                # Option 1: Don't include this vehicle
                dp[i][w] = dp[i - 1][w]

                # Option 2: Include this vehicle (if it fits)
                if vehicle.duration <= w:
                    include_value = dp[i - 1][w - vehicle.duration] + vehicle.impact
                    dp[i][w] = max(dp[i][w], include_value)

        # Backtrack to find selected vehicles
        selected = []
        w = mechanic_hours
        for i in range(n, 0, -1):
            if dp[i][w] != dp[i - 1][w]:
                selected.append(vehicles[i - 1])
                w -= vehicles[i - 1].duration

        selected.reverse()

        total_impact = dp[n][mechanic_hours]
        total_hours = sum(v.duration for v in selected)

        self._log(
            "info",
            f"Scheduling complete: {len(selected)} vehicles selected, impact={total_impact}, hours={total_hours}",
            context={
                "selected_count": len(selected),
                "total_impact": total_impact,
                "total_hours": total_hours,
                "remaining_hours": mechanic_hours - total_hours
            }
        )

        return selected, total_impact, total_hours

    def schedule_all_depots(
        self,
        vehicles: List[Vehicle],
        depots: List[Depot]
    ) -> Dict[int, Dict]:
        """
        Schedule maintenance for all depots.

        Args:
            vehicles: List of all vehicles
            depots: List of all depots with their budgets

        Returns:
            Dict mapping depot_id to scheduling results
        """
        self._log(
            "info",
            f"Starting multi-depot scheduling: {len(depots)} depots, {len(vehicles)} vehicles"
        )

        results = {}
        for depot in depots:
            selected, impact, hours = self.schedule_maintenance(vehicles, depot.mechanic_hours)
            results[depot.id] = {
                "depot_id": depot.id,
                "mechanic_hours_budget": depot.mechanic_hours,
                "selected_vehicles": [
                    {
                        "task_id": v.task_id,
                        "duration": v.duration,
                        "impact": v.impact
                    }
                    for v in selected
                ],
                "total_impact": impact,
                "total_hours_used": hours,
                "hours_remaining": depot.mechanic_hours - hours,
                "efficiency": round((impact / depot.mechanic_hours * 100), 2) if depot.mechanic_hours > 0 else 0
            }

        self._log(
            "info",
            f"Multi-depot scheduling complete",
            context={
                "depots_processed": len(results),
                "total_vehicles_scheduled": sum(
                    len(r["selected_vehicles"]) for r in results.values()
                )
            }
        )

        return results

    def get_efficiency_report(self, scheduling_result: Dict) -> Dict:
        """Generate efficiency report for scheduling results"""
        total_budget = scheduling_result["mechanic_hours_budget"]
        total_used = scheduling_result["total_hours_used"]
        total_impact = scheduling_result["total_impact"]

        return {
            "depot_id": scheduling_result["depot_id"],
            "utilization_rate": round((total_used / total_budget * 100), 2),
            "impact_per_hour": round((total_impact / total_used), 2) if total_used > 0 else 0,
            "vehicles_count": len(scheduling_result["selected_vehicles"]),
            "efficiency_score": scheduling_result["efficiency"]
        }
