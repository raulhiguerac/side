from app.schemas.base import StrictBase 
from app.models.onboarding import OnboardingStep

class OnboardingIntent(StrictBase):
    intent: OnboardingStep