from .ai_client import generate_structured
from .config import settings
from .schemas import NutritionTipOutput


SYSTEM = """
Give concise, general nutrition and recovery information.

Do not prescribe:
- restrictive diets
- medication
- medical treatment
- unsafe supplement use

Encourage:
- balanced meals
- hydration
- adequate sleep
- recovery

For medical or condition-specific needs, recommend speaking with an
appropriately qualified professional.
"""


def generate_nutrition_tip_with_flash(goal: str) -> str:
    if not settings.gemini_api_key:
        result = NutritionTipOutput(
            tip=(
                f"For {goal}, build meals around a balanced mix of protein "
                "foods, vegetables or fruit, whole grains or other carbohydrate "
                "sources, and healthy fats."
            ),
            recovery_note=(
                "Hydrate regularly and aim for consistent sleep and recovery. "
                "Adjust activity if you feel unwell or have pain."
            ),
        )
        return result.model_dump_json(indent=2)

    result = generate_structured(
        model=settings.gemini_tip_model,
        system=SYSTEM,
        prompt=(
            "Give one concise nutrition tip and one recovery note that "
            f"complement a fitness goal of {goal}."
        ),
        schema=NutritionTipOutput,
        temperature=0.4,
        max_output_tokens=800,
    )
    return result.model_dump_json(indent=2)
