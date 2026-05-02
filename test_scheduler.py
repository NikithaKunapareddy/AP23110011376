"""
Test Script for Vehicle Maintenance Scheduler
Demonstrates the knapsack algorithm with sample data
"""

import asyncio
from vehicle_maintenance_scheduler import (
    VehicleMaintenanceScheduler,
    Vehicle,
    Depot
)
from logging_middleware import LoggerService


async def main():
    """Test the scheduler with sample data"""
    
    # Initialize logger
    logger = LoggerService(log_dir="logs", app_name="scheduler-test")
    
    # Create scheduler
    scheduler = VehicleMaintenanceScheduler(logger)
    
    # Sample vehicles
    vehicles = [
        Vehicle(task_id="264e638f-1c7a-4d67-9f9c-53f3d1766d37", duration=1, impact=5),
        Vehicle(task_id="73ce9dca-1536-4a7a-9f1e-c67083afad61", duration=6, impact=2),
        Vehicle(task_id="4b6e22ee-b4ed-45a4-a6af-5294b0d69f37", duration=1, impact=3),
        Vehicle(task_id="d6372f32-852b-46a9-8e8c-e730fecc3c22", duration=5, impact=5),
        Vehicle(task_id="ec40b581-bdfc-43e0-a047-871fdafe8167", duration=7, impact=3),
        Vehicle(task_id="fb1e3165-67c9-4e96-a5c3-2d20085d293b", duration=6, impact=3),
        Vehicle(task_id="330065c0-3815-4e10-a18a-b93b117e30a8", duration=5, impact=1),
        Vehicle(task_id="72a91abc-4ed7-492c-9e99-348e7437953b", duration=5, impact=9),
        Vehicle(task_id="8a7ff5b1-335c-4a2f-96d8-09c4a362e781", duration=6, impact=10),
        Vehicle(task_id="08d00114-9506-463d-ba2e-3343ec4e2e89", duration=6, impact=6),
    ]
    
    # Sample depots
    depots = [
        Depot(id=1, mechanic_hours=60),
        Depot(id=2, mechanic_hours=135),
        Depot(id=3, mechanic_hours=188),
    ]
    
    print("\n" + "="*70)
    print("VEHICLE MAINTENANCE SCHEDULER - KNAPSACK SOLUTION")
    print("="*70)
    
    print(f"\nTotal Vehicles Available: {len(vehicles)}")
    print(f"Total Depots: {len(depots)}")
    
    # Run scheduling
    results = scheduler.schedule_all_depots(vehicles, depots)
    
    # Display results
    for depot_id, result in results.items():
        print(f"\n{'─'*70}")
        print(f"DEPOT {depot_id}")
        print(f"{'─'*70}")
        print(f"Budget: {result['mechanic_hours_budget']} hours")
        print(f"Used: {result['total_hours_used']} hours")
        print(f"Remaining: {result['hours_remaining']} hours")
        print(f"Total Impact Score: {result['total_impact']}")
        print(f"Utilization Rate: {100 - (result['hours_remaining']/result['mechanic_hours_budget']*100):.1f}%")
        print(f"Efficiency: {result['efficiency']:.2f}")
        
        print(f"\nSelected Vehicles ({len(result['selected_vehicles'])}):")
        for i, vehicle in enumerate(result['selected_vehicles'], 1):
            print(f"  {i}. TaskID: {vehicle['task_id']}")
            print(f"     Duration: {vehicle['duration']}h | Impact: {vehicle['impact']}")
    
    print(f"\n{'='*70}")
    print("Scheduling Complete!")
    print(f"{'='*70}\n")


if __name__ == "__main__":
    asyncio.run(main())
