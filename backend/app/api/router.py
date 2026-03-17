from fastapi import APIRouter

from app.api import (
    analytics_routes,
	audit_logs_routes,
	auth_routes,
	billing_routes,
	demo_routes,
	copilot_routes,
	integration_routes,
	intelligence_routes,
	comparison_sets_routes,
	compare_routes,
	consortium_routes,
	deck_routes,
	dossier_routes,
	environment_routes,
	materials_routes,
	projects_routes,
	report_routes,
	simulation_routes,
	tenant_routes,
	visualization_routes,
)
from app.api.v1.routes import health

api_router = APIRouter()
api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(materials_routes.router)
api_router.include_router(environment_routes.router)
api_router.include_router(simulation_routes.router)
api_router.include_router(report_routes.router)
api_router.include_router(copilot_routes.router)
api_router.include_router(billing_routes.router)
api_router.include_router(analytics_routes.router)
api_router.include_router(audit_logs_routes.router)
api_router.include_router(dossier_routes.router)
api_router.include_router(deck_routes.router)
api_router.include_router(consortium_routes.router)
api_router.include_router(compare_routes.router)
api_router.include_router(comparison_sets_routes.router)
api_router.include_router(auth_routes.router)
api_router.include_router(demo_routes.router)
api_router.include_router(integration_routes.router)
api_router.include_router(intelligence_routes.router)
api_router.include_router(tenant_routes.router)
api_router.include_router(projects_routes.router)
api_router.include_router(visualization_routes.router)
