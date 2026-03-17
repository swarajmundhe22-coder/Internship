from fastapi import APIRouter

from app.models.material import MaterialCreate, MaterialRead
from app.services.material_service import MaterialService

router = APIRouter()
service = MaterialService()


@router.post("", response_model=MaterialRead, summary="Create material profile")
def create_material(payload: MaterialCreate) -> MaterialRead:
    return service.create_material(payload)
