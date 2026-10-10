export type AccountIntent = "buyer" | "seller" | "renter" | "explorer";

export interface User {
  account_id: string;
  email: string;
  account_type: string;
  onboarding_step: string;
  is_active: boolean;
  is_admin: boolean;
}
