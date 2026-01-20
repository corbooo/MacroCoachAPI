from sqlalchemy import Column, Integer, Date, Float, String, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from db import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False, index=True)

    weights = relationship("Weight", back_populates="user")
    macros = relationship("DailyMacro", back_populates="user")
    target = relationship("Target", back_populates="user", uselist=False)

class Weight(Base):
    __tablename__ = "weights"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    day = Column(Date, nullable=False)
    weight_lbs = Column(Float, nullable=False)

    user = relationship("User", back_populates="weights")

    __table_args__ = (UniqueConstraint("user_id", "day", name="uq_weights_day"),)

class DailyMacro(Base):
    __tablename__ = "daily_macros"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    day = Column(Date, nullable=False)

    user = relationship("User", back_populates="macros")

    calories = Column(Integer, nullable=False)
    protein_g = Column(Float, nullable=False)
    carbs_g = Column(Float, nullable=False)
    fat_g = Column(Float, nullable=False)

    __table_args__ = (UniqueConstraint("user_id", "day", name="uq_daily_macros_day"),)

class Target(Base):
    __tablename__ = "targets"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True, index=True)

    calories_target = Column(Integer, nullable=False)
    protein_target_g = Column(Float, nullable=False)
    carbs_target_g = Column(Float, nullable=False)
    fat_target_g = Column(Float, nullable=False)

    user = relationship("User", back_populates="target")