import json

from .ai_client import generate_structured
from .config import settings
from .schemas import WorkoutPlanOutput


SYSTEM = """
You revise general wellness workout plans.

Preserve a safe structure. Include recovery.

Never provide:
- medical diagnosis
- medical treatment
- dangerous exercise instructions
- extreme dieting

Apply the user's feedback when it is safe and reasonable.

If feedback requests something unsafe, replace it with a safer alternative
and mention that adjustment in the safety note.
"""


def update_workout_plan(original_plan: str, feedback: str) -> str:
    if not settings.gemini_api_key:
        return _demo_update(original_plan, feedback)

    prompt = f"""
Original plan JSON:

{original_plan}

User feedback:

{feedback}

Create a revised 7-day plan.

Requirements:
1. Keep the same JSON schema.
2. Preserve useful parts of the original plan.
3. Apply reasonable user feedback.
4. Keep at least one recovery/rest day.
5. Do not introduce unsafe extremes.
6. Do not provide medical treatment.
"""

    result = generate_structured(
        model=settings.gemini_workout_model,
        system=SYSTEM,
        prompt=prompt,
        schema=WorkoutPlanOutput,
        temperature=0.6,
        max_output_tokens=6000,
    )
    return result.model_dump_json(indent=2)


def _demo_update(original_plan: str, feedback: str) -> str:
    data = json.loads(original_plan)

    data["overview"] += f" Updated based on feedback: {feedback}"
    data["safety_note"] += (
        " Keep changes gradual and stop if an exercise causes pain."
    )

    feedback_lower = feedback.lower()

    if "cardio" in feedback_lower:
        data["days"][1]["focus"] = "Cardio emphasis"
        data["days"][1]["exercises"] = [
            {
                "name": "Brisk walk or easy cycle",
                "sets_reps": "25–35 min",
                "rest": "As needed",
                "notes": "Comfortable, controlled pace",
            }
        ]

    if "rest" in feedback_lower:
        data["days"][3]["focus"] = "Extra recovery day"

    return WorkoutPlanOutput.model_validate(data).model_dump_json(indent=2)
