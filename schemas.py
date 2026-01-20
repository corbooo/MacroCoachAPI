from datetime import date
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional

class UserIn(BaseModel):
    username: str = Field(min_length=3, max_length=20)

class WeightIn(BaseModel):
    day: date
    weight_lbs: float = Field(gt=0, lt=1000)

class MacroIn(BaseModel):
    day: date
    calories: int = Field(gt=0, lt=20000)
    protein_g: float = Field(gt=0, lt=1000)
    carbs_g: float = Field(gt=0, lt=2000)
    fat_g: float = Field(gt=0, lt=1000)

class TargetIn(BaseModel):
    calories_target: int = Field(gt=0, lt=20000)
    protein_target_g: float = Field(ge=0, lt=1000)
    carbs_target_g: float = Field(ge=0, lt=2000)
    fat_target_g: float = Field(ge=0, lt=1000)


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    username: str

class WeightOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    user_id: int
    day: date
    weight_lbs: float

class MacroOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    user_id: int
    day: date
    calories: int
    protein_g: float
    carbs_g: float
    fat_g: float

class WeightBulkUpsertOut(BaseModel):
    created: int
    updated: int
    saved: List[WeightOut]

class MacroBulkUpsertOut(BaseModel):
    created: int
    updated: int
    saved: List[MacroOut]

class TargetOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    user_id: int
    calories_target: int
    protein_target_g: float
    carbs_target_g: float
    fat_target_g: float

# --- wrappers for list endpoints ---

class UsersListOut(BaseModel):
    count: int
    users: List[UserOut]

class WeightsListOut(BaseModel):
    count: int
    weights: List[WeightOut]

class MacrosListOut(BaseModel):
    count: int
    macros: List[MacroOut]

class TargetGetOut(BaseModel):
    target: Optional[TargetOut]

# upsert responses
class WeightUpsertOut(BaseModel):
    action: str
    saved: WeightOut

class MacroUpsertOut(BaseModel):
    action: str
    saved: MacroOut

class TargetUpsertOut(BaseModel):
    action: str
    target: TargetOut
