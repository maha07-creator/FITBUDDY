from __future__ import annotations

import json
import logging
from pathlib import Path
from urllib.parse import quote

from fastapi import (
    APIRouter,
    Depends,
    Form,
    Header,
    HTTPException,
    Request,
    status,
)
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import ValidationError
from sqlalchemy.orm import Session

from .ai_client import AIGenerationError
from .config import settings
from .database import (
    delete_user,
    get_all_users,
    get_db,
    get_original_plan,
    get_user,
    save_plan,
    save_user,
    update_plan,
)
from .gemini_flash_generator import generate_nutrition_tip_with_flash
from .gemini_generator import generate_workout_gemini
from .schemas import FeedbackRequest, UserInput
from .updated_plan import update_workout_plan

logger = logging.getLogger("fitbuddy")

BASE_DIR = Path(__file__).resolve().parent.parent

router = APIRouter()
templates = Jinja2Templates(directory=BASE_DIR / "templates")


# ------------------------------------------------
# HELPERS
# ------------------------------------------------

def _parse_json(value: str | None) -> dict | None:
    if not value:
        return None
    try:
        return json.loads(value)
    except Exception:
        return None


def _pretty_json(value: str | None) -> str:
    data = _parse_json(value)
    if data is None:
        return value or ""
    return json.dumps(data, indent=2, ensure_ascii=False)


def _friendly_error(exc: Exception) -> str:
    """Turn exceptions into short, readable messages for the web page."""
    if isinstance(exc, ValidationError):
        parts = []
        for err in exc.errors():
            field = ".".join(str(p) for p in err["loc"]) or "input"
            parts.append(f"{field.replace('_', ' ')}: {err['msg']}")
        return "Please check your details — " + "; ".join(parts)

    if isinstance(exc, (ValueError, AIGenerationError)):
        return str(exc)

    logger.exception("Unexpected error")
    return "Something went wrong while generating your plan. Please try again."


def _admin_ok(x_admin_key: str | None, form_key: str | None = None) -> bool:
    # If no admin key is configured, local development is allowed.
    if not settings.admin_key:
        return True
    return (x_admin_key or form_key or "") == settings.admin_key


def _result_context(request: Request, user, plan, updated: bool) -> dict:
    current = (plan.updated_plan or plan.original_plan) if updated else plan.original_plan
    return {
        "request": request,
        "user": user,
        "plan": plan,
        "plan_data": _parse_json(current),
        "tip_data": _parse_json(plan.nutrition_tip),
        "workout_plan": _pretty_json(current),
        "nutrition_tip": _pretty_json(plan.nutrition_tip),
        "error": None,
        "updated": updated,
    }


# ------------------------------------------------
# HOME
# ------------------------------------------------

@router.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"request": request, "error": None, "form": {}},
    )


# ------------------------------------------------
# HTML WORKOUT GENERATION
# ------------------------------------------------

@router.post("/generate-workout", response_class=HTMLResponse)
def generate_workout(
    request: Request,
    username: str = Form(...),
    user_id: str = Form(...),
    age: int = Form(...),
    weight: float = Form(...),
    goal: str = Form(...),
    intensity: str = Form(...),
    db: Session = Depends(get_db),
):
    form = {
        "username": username,
        "user_id": user_id,
        "age": age,
        "weight": weight,
        "goal": goal,
        "intensity": intensity,
    }

    try:
        data = UserInput(**form)

        workout = generate_workout_gemini(data)
        tip = generate_nutrition_tip_with_flash(data.goal)

        user = save_user(db, **data.model_dump())
        plan = save_plan(db, user.id, workout, tip)

        return templates.TemplateResponse(
            request=request,
            name="result.html",
            context=_result_context(request, user, plan, updated=False),
        )

    except Exception as exc:
        return templates.TemplateResponse(
            request=request,
            name="index.html",
            context={
                "request": request,
                "error": _friendly_error(exc),
                "form": form,
            },
            status_code=400,
        )


# ------------------------------------------------
# HTML FEEDBACK
# ------------------------------------------------

@router.post("/submit-feedback", response_class=HTMLResponse)
def submit_feedback(
    request: Request,
    user_id: str = Form(...),
    feedback: str = Form(...),
    db: Session = Depends(get_db),
):
    user = None
    plan = None

    try:
        payload = FeedbackRequest(user_id=user_id, feedback=feedback)

        user = get_user(db, payload.user_id)
        plan = get_original_plan(db, payload.user_id)

        if not plan or not user:
            raise ValueError("User ID was not found. Generate a plan first.")

        revised = update_workout_plan(plan.original_plan, payload.feedback)
        update_plan(db, plan, revised, payload.feedback)

        return templates.TemplateResponse(
            request=request,
            name="result.html",
            context=_result_context(request, user, plan, updated=True),
        )

    except Exception as exc:
        if user and plan:
            # Keep showing the existing plan, with the error on top.
            context = _result_context(
                request, user, plan, updated=bool(plan.updated_plan)
            )
        else:
            context = {
                "request": request,
                "user": None,
                "plan": None,
                "plan_data": None,
                "tip_data": None,
                "workout_plan": "",
                "nutrition_tip": "",
                "updated": False,
            }
        context["error"] = _friendly_error(exc)

        return templates.TemplateResponse(
            request=request,
            name="result.html",
            context=context,
            status_code=400,
        )


# ------------------------------------------------
# ADMIN DASHBOARD
# ------------------------------------------------

@router.get("/view-all-users", response_class=HTMLResponse)
def view_all_users(
    request: Request,
    admin_key: str | None = None,
    x_admin_key: str | None = Header(default=None),
    db: Session = Depends(get_db),
):
    if not _admin_ok(x_admin_key, admin_key):
        return templates.TemplateResponse(
            request=request,
            name="admin_login.html",
            context={
                "request": request,
                "error": "Invalid admin key." if admin_key else None,
            },
            status_code=403 if admin_key else 200,
        )

    rows = [{"user": user, "plans": user.plans} for user in get_all_users(db)]

    return templates.TemplateResponse(
        request=request,
        name="all_users.html",
        context={
            "request": request,
            "rows": rows,
            "admin_key": admin_key,
            "admin_protected": bool(settings.admin_key),
        },
    )


# ------------------------------------------------
# ADMIN DELETE
# ------------------------------------------------

@router.post("/admin/delete/{user_id}")
def admin_delete(
    user_id: str,
    admin_key: str = Form(""),
    db: Session = Depends(get_db),
):
    if not _admin_ok(None, admin_key):
        raise HTTPException(status_code=403, detail="Invalid admin key")

    delete_user(db, user_id)

    url = "/view-all-users"
    if admin_key:
        url += f"?admin_key={quote(admin_key)}"

    return RedirectResponse(url=url, status_code=status.HTTP_303_SEE_OTHER)


# ------------------------------------------------
# API HEALTH
# ------------------------------------------------

@router.get("/api/health")
def health():
    return {
        "status": "ok",
        "service": settings.app_name,
        "mode": "gemini" if settings.gemini_api_key else "demo",
    }


# ------------------------------------------------
# API WORKOUT
# ------------------------------------------------

@router.post("/api/workout")
def api_workout(payload: UserInput, db: Session = Depends(get_db)):
    try:
        workout = generate_workout_gemini(payload)
        tip = generate_nutrition_tip_with_flash(payload.goal)
    except AIGenerationError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    user = save_user(db, **payload.model_dump())
    plan = save_plan(db, user.id, workout, tip)

    return {
        "user_id": user.user_id,
        "plan_id": plan.id,
        "workout_plan": json.loads(workout),
        "nutrition_tip": json.loads(tip),
    }


# ------------------------------------------------
# API FEEDBACK
# ------------------------------------------------

@router.post("/api/feedback")
def api_feedback(payload: FeedbackRequest, db: Session = Depends(get_db)):
    plan = get_original_plan(db, payload.user_id)

    if not plan:
        raise HTTPException(status_code=404, detail="User ID was not found")

    try:
        revised = update_workout_plan(plan.original_plan, payload.feedback)
    except AIGenerationError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    update_plan(db, plan, revised, payload.feedback)

    return {
        "user_id": payload.user_id,
        "plan_id": plan.id,
        "updated_plan": json.loads(revised),
    }


# ------------------------------------------------
# API USERS
# ------------------------------------------------

@router.get("/api/users")
def api_users(
    x_admin_key: str | None = Header(default=None),
    db: Session = Depends(get_db),
):
    if not _admin_ok(x_admin_key):
        raise HTTPException(status_code=403, detail="Admin key required")

    return [
        {
            "user_id": user.user_id,
            "username": user.username,
            "age": user.age,
            "weight": user.weight,
            "goal": user.goal,
            "intensity": user.intensity,
            "created_at": user.created_at.isoformat(),
        }
        for user in get_all_users(db)
    ]
