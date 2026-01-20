from fastapi import FastAPI, Depends, HTTPException, Query, status
from datetime import date, timedelta
from sqlalchemy.orm import Session
from typing import Optional, List

from db import engine, SessionLocal, Base
from models import User, Weight, DailyMacro, Target
from schemas import (
    WeightIn, MacroIn, TargetIn,
    UserIn, UserOut, UsersListOut,
    WeightUpsertOut, WeightsListOut,
    MacroUpsertOut, MacrosListOut,
    TargetUpsertOut, TargetGetOut,
    WeightBulkUpsertOut, MacroBulkUpsertOut
)
from logic import build_weekly_insight, build_rolling_insights, calorie_adjustment

# uvicorn main:app --reload
# or uvicorn main:app --host 0.0.0.0 --port 8000
app = FastAPI()

# Create tables on startup (simple approach for now)
Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_user_by_username(db: Session, username: str) -> User:
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/users", response_model=UserOut, status_code=201)
def create_user(user: UserIn, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.username == user.username).first()
    if existing:
        return existing
    new_user = User(username=user.username)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@app.get("/users", response_model=UsersListOut)
def list_users(db: Session = Depends(get_db)):
    users = db.query(User).order_by(User.id.asc()).all()
    return {"count": len(users),"users": users}

@app.post("/weights", response_model=WeightUpsertOut)
def upsert_weight(username:str, entry: WeightIn, db: Session = Depends(get_db)):
    user = get_user_by_username(db, username)
    user_id = user.id
    existing = db.query(Weight).filter(Weight.user_id == user_id, Weight.day == entry.day).first()

    if existing:
        existing.weight_lbs = entry.weight_lbs
        db.commit()
        db.refresh(existing)
        return {"action": "updated", "saved": existing}

    new_row = Weight(user_id=user_id, day=entry.day, weight_lbs=entry.weight_lbs)
    db.add(new_row)
    db.commit()
    db.refresh(new_row)
    return {"action": "created", "saved": new_row}

@app.post("/weights/bulk", response_model=WeightBulkUpsertOut)
def bulk_upsert_weights(username: str, entries: List[WeightIn], db: Session = Depends(get_db)):
    user = get_user_by_username(db, username)
    user_id = user.id

    created = 0
    updated = 0
    saved_rows = []

    for entry in entries:
        existing = (
            db.query(Weight)
            .filter(Weight.user_id == user_id, Weight.day == entry.day)
            .first()
        )

        if existing:
            existing.weight_lbs = entry.weight_lbs
            updated += 1
            saved_rows.append(existing)
        else:
            row = Weight(user_id=user_id, day=entry.day, weight_lbs=entry.weight_lbs)
            db.add(row)
            created += 1
            saved_rows.append(row)

    db.commit()
    for r in saved_rows:
        db.refresh(r)

    return {"created": created, "updated": updated, "saved": saved_rows}

@app.get("/weights", response_model=WeightsListOut)
def list_weights(username:str, start: Optional[date] = None, end: Optional[date] = None, limit: int = Query(100, ge=1, le=1000), offset: int = Query(0, ge=0), db: Session = Depends(get_db)):
    user = get_user_by_username(db, username)
    user_id = user.id
    q = db.query(Weight).filter(Weight.user_id == user_id)

    if start is not None:
        q = q.filter(Weight.day >= start)
    if end is not None:
        q = q.filter(Weight.day < end)

    total = q.count()
    rows = q.order_by(Weight.day.asc()).offset(offset).limit(limit).all()
    return {"count": total, "weights": rows}

@app.post("/macros", response_model=MacroUpsertOut)
def upsert_macros(username:str, entry: MacroIn, db: Session = Depends(get_db)):
    user = get_user_by_username(db, username)
    user_id = user.id
    existing = db.query(DailyMacro).filter(DailyMacro.user_id == user_id, DailyMacro.day == entry.day).first()

    if existing:
        existing.calories = entry.calories
        existing.protein_g = entry.protein_g
        existing.carbs_g = entry.carbs_g
        existing.fat_g = entry.fat_g
        db.commit()
        db.refresh(existing)
        return {"action": "updated", "saved": existing}

    new_row = DailyMacro(user_id=user_id, **entry.model_dump())
    db.add(new_row)
    db.commit()
    db.refresh(new_row)
    return {"action": "created", "saved": new_row}

@app.post("/macros/bulk", response_model=MacroBulkUpsertOut)
def bulk_upsert_macros(username: str, entries: List[MacroIn], db: Session = Depends(get_db)):
    user = get_user_by_username(db, username)
    user_id = user.id

    created = 0
    updated = 0
    saved_rows = []

    for entry in entries:
        existing = (
            db.query(DailyMacro)
            .filter(DailyMacro.user_id == user_id, DailyMacro.day == entry.day)
            .first()
        )

        if existing:
            existing.calories = entry.calories
            existing.protein_g = entry.protein_g
            existing.carbs_g = entry.carbs_g
            existing.fat_g = entry.fat_g
            updated += 1
            saved_rows.append(existing)
        else:
            row = DailyMacro(user_id=user_id, **entry.model_dump())
            db.add(row)
            created += 1
            saved_rows.append(row)

    db.commit()
    for r in saved_rows:
        db.refresh(r)

    return {"created": created, "updated": updated, "saved": saved_rows}

@app.get("/macros", response_model=MacrosListOut)
def list_macros(username:str, start: Optional[date] = None, end: Optional[date] = None, limit: int = Query(100, ge=1, le=1000), offset: int = Query(0, ge=0), db: Session = Depends(get_db)):
    user = get_user_by_username(db, username)
    user_id = user.id
    q = db.query(DailyMacro).filter(DailyMacro.user_id == user_id)

    if start is not None:
        q = q.filter(DailyMacro.day >= start)
    if end is not None:
        q = q.filter(DailyMacro.day < end)

    total = q.count()
    rows = q.order_by(DailyMacro.day.asc()).offset(offset).limit(limit).all()
    return {"count": total, "macros": rows}

@app.post("/targets", response_model=TargetUpsertOut)
def upsert_target(username:str, entry: TargetIn, db: Session = Depends(get_db)):
    user = get_user_by_username(db, username)
    user_id = user.id
    existing = db.query(Target).filter(Target.user_id == user_id).first()
    if existing:
        existing.calories_target = entry.calories_target
        existing.protein_target_g = entry.protein_target_g
        existing.carbs_target_g = entry.carbs_target_g
        existing.fat_target_g = entry.fat_target_g
        db.commit()
        db.refresh(existing)
        return {"action": "updated", "target": existing}

    new_row = Target(user_id=user_id, **entry.model_dump())
    db.add(new_row)
    db.commit()
    db.refresh(new_row)
    return {"action": "created", "target": new_row}

@app.get("/targets", response_model=TargetGetOut)
def get_target(username:str, db: Session = Depends(get_db)):
    user = get_user_by_username(db, username)
    user_id = user.id
    row = db.query(Target).filter(Target.user_id == user_id).first()
    return {"target": row}

@app.get("/insights/weekly")
def weekly_insight(username:str, start: date, db: Session = Depends(get_db)):
    user = get_user_by_username(db, username)
    user_id = user.id
    end = start + timedelta(days=7)

    macro_rows = db.query(DailyMacro).filter(DailyMacro.user_id == user_id, DailyMacro.day >= start, DailyMacro.day < end).order_by(DailyMacro.day.asc()).all()
    weight_rows = db.query(Weight).filter(Weight.user_id == user_id, Weight.day >= start, Weight.day < end).order_by(Weight.day.asc()).all()
    target = db.query(Target).filter(Target.user_id == user_id).first()
    
    return build_weekly_insight(
        start=start,
        macro_rows=macro_rows,
        weight_rows=weight_rows,
        target=target
    )

@app.get("/insights/rolling")
def rolling_insights(username:str, days: int = 7, db: Session = Depends(get_db)):
    user = get_user_by_username(db, username)
    user_id = user.id
    end = date.today()
    start = end - timedelta(days=days)

    macro_rows = db.query(DailyMacro).filter(DailyMacro.user_id == user_id, DailyMacro.day >= start, DailyMacro.day <= end).order_by(DailyMacro.day.asc()).all()
    weight_rows = db.query(Weight).filter(Weight.user_id == user_id, Weight.day >= start, Weight.day <= end).order_by(Weight.day.asc()).all()

    return build_rolling_insights(
        days=days,
        start=start,
        end=end,
        macro_rows=macro_rows,
        weight_rows=weight_rows
    )

@app.get("/adjustment/weight")
def weight_adjustments(username:str, desired_lbs_per_week: float, days: int = 35, db: Session = Depends(get_db)):
    user = get_user_by_username(db, username)
    user_id = user.id
    end = date.today()
    start = end - timedelta(days=days)

    macro_rows = db.query(DailyMacro).filter(DailyMacro.user_id == user_id, DailyMacro.day > start, DailyMacro.day <= end).order_by(DailyMacro.day.asc()).all()
    weight_rows = db.query(Weight).filter(Weight.user_id == user_id, Weight.day > start, Weight.day <= end).order_by(Weight.day.asc()).all()

    return calorie_adjustment(
        days=days,
        start=start,
        end=end,
        macro_rows=macro_rows,
        weight_rows=weight_rows,
        desired_lbs_per_week=desired_lbs_per_week
    )