from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.security import require_roles
from app.models.auth import AuthPrincipal, UserRole
from app.database.session import get_db_session
from app.models.comparison import SimulationComparisonRequest, SimulationComparisonResponse
from app.services.comparison_service import ComparisonService

router = APIRouter(prefix="/compare", tags=["compare"])


@router.post("/simulations", response_model=SimulationComparisonResponse)
async def compare_simulations(
    payload: SimulationComparisonRequest,
    _principal: AuthPrincipal = Depends(require_roles(UserRole.admin, UserRole.engineer, UserRole.viewer)),
    session: AsyncSession = Depends(get_db_session),
) -> SimulationComparisonResponse:
    service = ComparisonService(session=session)
    try:
        return await service.compare_simulations(
            left_id=payload.left_simulation_id,
            right_id=payload.right_simulation_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
