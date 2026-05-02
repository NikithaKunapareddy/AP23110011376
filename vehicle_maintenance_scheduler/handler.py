"""
Vehicle Maintenance Scheduler API Handler
Fetches depot and vehicle data from APIs and runs scheduling algorithm
"""

import httpx
from typing import List, Dict, Optional
from logging_middleware import LoggerService
from .scheduler import VehicleMaintenanceScheduler, Vehicle, Depot


class SchedulerHandler:
    """Handles API calls and scheduling orchestration"""

    BASE_URL = "http://20.207.122.201/evaluation-service"
    AUTH_URL = "http://20.207.122.201/evaluation-service/auth"

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        logger_service: Optional[LoggerService] = None
    ):
        self.client_id = client_id
        self.client_secret = client_secret
        self.logger_service = logger_service
        self.scheduler = VehicleMaintenanceScheduler(logger_service)
        self.access_token: Optional[str] = None

    async def _get_access_token(self) -> str:
        """Authenticate and get JWT token"""
        if self.access_token:
            return self.access_token
            
        self._log("info", "Authenticating with Afford API")
        
        try:
            async with httpx.AsyncClient() as client:
                auth_body = {
                    "email": "anikitha_kunapareddy@srmap.edu.in",
                    "name": "Kunapareddy Nikitha",
                    "rollNo": "AP23110011376",
                    "accessCode": "QkbpxH",
                    "clientID": self.client_id,
                    "clientSecret": self.client_secret
                }
                
                response = await client.post(
                    self.AUTH_URL,
                    json=auth_body,
                    timeout=10
                )
                response.raise_for_status()
                data = response.json()
                self.access_token = data.get("access_token")
                
                if not self.access_token:
                    raise ValueError("No access token in auth response")
                    
                self._log("info", "Successfully authenticated with Afford API")
                return self.access_token
                
        except Exception as e:
            self._log("error", f"Authentication failed: {str(e)}")
            raise

    def _get_headers(self) -> Dict[str, str]:
        """Get headers with authentication token"""
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }

    def _log(self, level: str, message: str, context: Optional[Dict] = None):
        """Log using middleware"""
        if self.logger_service:
            method = getattr(self.logger_service, level, self.logger_service.info)
            method(
                stack="backend",
                package="handler",
                message=message,
                context=context or {}
            )

    async def fetch_depots(self) -> List[Depot]:
        """Fetch depot data from API"""
        self._log("info", "Fetching depot information from API")
        
        try:
            token = await self._get_access_token()
            headers = self._get_headers()
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.BASE_URL}/depots",
                    headers=headers,
                    timeout=10
                )
                response.raise_for_status()
                data = response.json()

                depots = [
                    Depot(id=d["ID"], mechanic_hours=d["MechanicHours"])
                    for d in data.get("depots", [])
                ]

                self._log(
                    "info",
                    f"Fetched {len(depots)} depots",
                    context={"depot_count": len(depots)}
                )
                return depots

        except Exception as e:
            self._log("error", f"Failed to fetch depots: {str(e)}")
            raise

    async def fetch_vehicles(self) -> List[Vehicle]:
        """Fetch vehicle maintenance tasks from API"""
        self._log("info", "Fetching vehicle maintenance tasks from API")
        
        try:
            token = await self._get_access_token()
            headers = self._get_headers()
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.BASE_URL}/vehicles",
                    headers=headers,
                    timeout=10
                )
                response.raise_for_status()
                data = response.json()

                vehicles = [
                    Vehicle(
                        task_id=v["TaskID"],
                        duration=v["Duration"],
                        impact=v["Impact"]
                    )
                    for v in data.get("vehicles", [])
                ]

                self._log(
                    "info",
                    f"Fetched {len(vehicles)} vehicle maintenance tasks",
                    context={"vehicle_count": len(vehicles)}
                )
                return vehicles

        except Exception as e:
            self._log("error", f"Failed to fetch vehicles: {str(e)}")
            raise

    async def run_scheduling(self) -> Dict:
        """Fetch data and run complete scheduling"""
        self._log("info", "Starting complete maintenance scheduling workflow")
        
        try:
            depots = await self.fetch_depots()
            vehicles = await self.fetch_vehicles()

            results = self.scheduler.schedule_all_depots(vehicles, depots)

            self._log(
                "info",
                "Maintenance scheduling workflow completed successfully",
                context={"depots": len(depots), "vehicles": len(vehicles)}
            )

            return {
                "status": "success",
                "depots_processed": len(depots),
                "vehicles_available": len(vehicles),
                "results": results
            }

        except Exception as e:
            self._log("error", f"Scheduling workflow failed: {str(e)}")
            raise
