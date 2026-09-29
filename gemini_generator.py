from __future__ import annotations

from .ai_client import generate_structured
from .config import settings
from .schemas import UserInput, WorkoutPlanOutput


SYSTEM = """
You are FitBuddy, a cautious wellness planning assistant.

Generate general fitness information, not medical diagnosis or treatment.

Do not prescribe:
- extreme dieting
- unsafe exercise challenges
- dangerous exercise
- medication
- medical treatment

Prefer:
- gradual progression
- appropriate rest
- hydration
- warm-ups
- cooldowns
- recovery

If the request implies:
- an injury
- medical condition
- severe pain
- eating disorder
- serious health concern

do not provide condition-specific instructions.
Instead recommend consulting an appropriately qualified professional.

Never guarantee weight loss, muscle gain, or other outcomes.
"""


def _demo_plan(data: UserInput) -> str:
    plan = WorkoutPlanOutput(
        overview=(
            f"A balanced 7-day {data.goal} plan at {data.intensity} intensity."
        ),
        safety_note=(
            "Start gently, use controlled technique, take rest as needed, "
            "and stop if exercise causes pain."
        ),
        days=[
            {
                "day": "Day 1",
                "focus": "Full body foundation",
                "warm_up": "5–8 min easy movement",
                "exercises": [
                    {"name": "Bodyweight squat", "sets_reps": "2 x 8–12",
                     "rest": "60 sec", "notes": "Controlled tempo"},
                    {"name": "Incline push-up", "sets_reps": "2 x 6–12",
                     "rest": "60 sec", "notes": "Use a stable surface"},
                ],
                "cool_down": "5 min easy walking and gentle mobility",
            },
            {
                "day": "Day 2",
                "focus": "Light cardio + mobility",
                "warm_up": "5 min easy walking",
                "exercises": [
                    {"name": "Brisk walk", "sets_reps": "20–30 min",
                     "rest": "As needed", "notes": "Conversational pace"},
                ],
                "cool_down": "5 min slow walk + gentle stretches",
            },
            {
                "day": "Day 3",
                "focus": "Lower body + core",
                "warm_up": "5–8 min mobility",
                "exercises": [
                    {"name": "Glute bridge", "sets_reps": "2 x 10–15",
                     "rest": "60 sec", "notes": "Squeeze gently at top"},
                    {"name": "Dead bug", "sets_reps": "2 x 6–10/side",
                     "rest": "45 sec", "notes": "Move slowly"},
                ],
                "cool_down": "5 min gentle mobility",
            },
            {
                "day": "Day 4",
                "focus": "Recovery",
                "warm_up": "None required",
                "exercises": [
                    {"name": "Easy walk", "sets_reps": "10–20 min optional",
                     "rest": "As needed", "notes": "Keep it comfortable"},
                ],
                "cool_down": "Gentle breathing and mobility",
            },
            {
                "day": "Day 5",
                "focus": "Upper body + core",
                "warm_up": "5–8 min easy movement",
                "exercises": [
                    {"name": "Wall/incline push-up", "sets_reps": "2 x 6–12",
                     "rest": "60 sec", "notes": "Keep shoulders comfortable"},
                    {"name": "Bird dog", "sets_reps": "2 x 6–10/side",
                     "rest": "45 sec", "notes": "Stable trunk"},
                ],
                "cool_down": "5 min easy mobility",
            },
            {
                "day": "Day 6",
                "focus": "Cardio + flexibility",
                "warm_up": "5 min easy walk",
                "exercises": [
                    {"name": "Brisk walk or easy cycle", "sets_reps": "20–30 min",
                     "rest": "As needed", "notes": "Adjust pace to comfort"},
                ],
                "cool_down": "5–8 min gentle stretching",
            },
            {
                "day": "Day 7",
                "focus": "Rest and reflection",
                "warm_up": "None",
                "exercises": [
                    {"name": "Rest / easy movement",
                     "sets_reps": "Optional gentle activity",
                     "rest": "—", "notes": "Review how the week felt"},
                ],
                "cool_down": "Relaxation and hydration",
            },
        ],
    )
    return plan.model_dump_json(indent=2)


def generate_workout_gemini(data: UserInput) -> str:
    # Demo mode if no API key exists.
    if not settings.gemini_api_key:
        return _demo_plan(data)

    prompt = f"""
Create a personalized 7-day general fitness plan.

User:
Name: {data.username}
Age: {data.age}
Weight: {data.weight} kg
Goal: {data.goal}
Intensity: {data.intensity}

Requirements:
1. Return exactly 7 days.
2. Every day needs: day, focus, warm-up, exercises, cooldown/recovery.
3. Warm-up should generally be 5–10 minutes.
4. Each exercise must contain: name, sets/reps or duration, rest, notes
   (use an empty string for notes if there is nothing to add).
5. Include variety.
6. Include at least one recovery/rest day.
7. Avoid unsafe extremes.
8. Do not diagnose medical conditions.
9. Do not guarantee results.
10. Keep the plan practical for a normal user.
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
