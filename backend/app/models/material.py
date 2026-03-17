from pydantic import Field

from app.models.common import AuditMetadata, BaseDomainModel


class MaterialBase(BaseDomainModel):
    name: str = Field(min_length=2, max_length=120)
    alloy_group: str = Field(min_length=2, max_length=120)
    density_kg_m3: float = Field(gt=0)
    electrochemical_potential_v: float = Field(
        description="Standard electrode potential used for galvanic comparison."
    )


class MaterialCreate(MaterialBase):
    pass


class MaterialUpdate(BaseDomainModel):
    name: str | None = Field(default=None, min_length=2, max_length=120)
    alloy_group: str | None = Field(default=None, min_length=2, max_length=120)
    density_kg_m3: float | None = Field(default=None, gt=0)
    electrochemical_potential_v: float | None = Field(default=None)


class MaterialRead(MaterialBase, AuditMetadata):
    pass
