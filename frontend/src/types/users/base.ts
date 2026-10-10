export type AccountIntent = "buyer" | "seller" | "renter" | "explorer";

export type OnboardingStep =
  | "intent"
  | "city"
  | "neighborhood"
  | "property_type"
  | "done";

export interface User {
  account_id: string;
  email: string;
  account_type: string;
  onboarding_step: OnboardingStep;
  is_active: boolean;
  is_admin: boolean;
}
