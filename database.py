from __future__ import annotations

from datetime import datetime, timezone
from typing import Generator

from sqlalchemy import (
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    create_engine,
    select,
)
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    Session,
    mapped_column,
    relationship,
    sessionmaker,
)

from .config import settings


def utcnow() -> datetime:
    """Naive UTC timestamp (replaces the deprecated datetime.utcnow)."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


# SQLite needs this option when used with FastAPI.
connect_args = (
    {"check_same_thread": False}
    if settings.database_url.startswith("sqlite")
    else {}
)

engine = create_engine(settings.database_url, connect_args=connect_args)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    username: Mapped[str] = mapped_column(String(120))
    age: Mapped[int] = mapped_column(Integer)
    weight: Mapped[float] = mapped_column(Float)
    goal: Mapped[str] = mapped_column(String(40))
    intensity: Mapped[str] = mapped_column(String(20))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    plans: Mapped[list["WorkoutPlan"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        order_by="WorkoutPlan.id.desc()",
    )


class WorkoutPlan(Base):
    __tablename__ = "workout_plans"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_pk: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    original_plan: Mapped[str] = mapped_column(Text)
    updated_plan: Mapped[str | None] = mapped_column(Text, nullable=True)
    nutrition_tip: Mapped[str] = mapped_column(Text)
    feedback: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    user: Mapped[User] = relationship(back_populates="plans")


def init_db() -> None:
    """Create all database tables."""
    Base.metadata.create_all(bind=engine)


def get_db() -> Generator[Session, None, None]:
    """FastAPI database dependency."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def save_user(
    db: Session,
    user_id: str,
    username: str,
    age: int,
    weight: float,
    goal: str,
    intensity: str,
) -> User:
    user = db.scalar(select(User).where(User.user_id == user_id))

    if user:
        user.username = username
        user.age = age
        user.weight = weight
        user.goal = goal
        user.intensity = intensity
    else:
        user = User(
            user_id=user_id,
            username=username,
            age=age,
            weight=weight,
            goal=goal,
            intensity=intensity,
        )
        db.add(user)

    db.commit()
    db.refresh(user)
    return user


def save_plan(
    db: Session,
    user_pk: int,
    original_plan: str,
    nutrition_tip: str,
) -> WorkoutPlan:
    plan = WorkoutPlan(
        user_pk=user_pk,
        original_plan=original_plan,
        nutrition_tip=nutrition_tip,
    )
    db.add(plan)
    db.commit()
    db.refresh(plan)
    return plan


def get_user(db: Session, user_id: str) -> User | None:
    return db.scalar(select(User).where(User.user_id == user_id))


def get_original_plan(db: Session, user_id: str) -> WorkoutPlan | None:
    """Return the user's most recent plan (which holds the original version)."""
    user = get_user(db, user_id)
    if not user:
        return None

    return db.scalar(
        select(WorkoutPlan)
        .where(WorkoutPlan.user_pk == user.id)
        .order_by(WorkoutPlan.id.desc())
    )


def update_plan(
    db: Session,
    plan: WorkoutPlan,
    updated_plan: str,
    feedback: str,
) -> WorkoutPlan:
    plan.updated_plan = updated_plan
    plan.feedback = feedback
    plan.updated_at = utcnow()
    db.commit()
    db.refresh(plan)
    return plan


def get_all_users(db: Session) -> list[User]:
    return list(db.scalars(select(User).order_by(User.created_at.desc())).all())


def delete_user(db: Session, user_id: str) -> bool:
    user = get_user(db, user_id)
    if not user:
        return False
    db.delete(user)
    db.commit()
    return True
