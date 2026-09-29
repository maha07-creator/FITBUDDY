from typing import Literal

from pydantic import BaseModel, Field, field_validator


Goal = Literal[
    "weight loss",
    "muscle gain",
    "general wellness",
    "flexibility",
    "endurance",
]

Intensity = Literal["low", "medium", "high"]


class UserInput(BaseModel):
    username: str = Field(min_length=2, max_length=120)
    user_id: str = Field(min_length=2, max_length=80, pattern=r"^[A-Za-z0-9_-]+$")
    age: int = Field(ge=13, le=100)
    weight: float = Field(gt=20, le=400)
    goal: Goal
    intensity: Intensity

    @field_validator("username")
    @classmethod
    def clean_username(cls, value: str) -> str:
        return " ".join(value.strip().split())


class FeedbackRequest(BaseModel):
    user_id: str = Field(min_length=2, max_length=80)
    feedback: str = Field(min_length=3, max_length=1000)


# ---------------------------------------------------------------
# AI output schemas.
# These are sent to Gemini as response_schema, so they deliberately
# have NO default values (the Gemini API can reject schema defaults).
# ---------------------------------------------------------------

class Exercise(BaseModel):
    name: str
    sets_reps: str
    rest: str
    notes: str


class DayPlan(BaseModel):
    day: str
    focus: str
    warm_up: str
    exercises: list[Exercise]
    cool_down: str


class WorkoutPlanOutput(BaseModel):
    overview: str
    safety_note: str
    days: list[DayPlan]


class NutritionTipOutput(BaseModel):
    tip: str
    recovery_note: str
