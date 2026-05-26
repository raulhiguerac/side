export interface User {
  account_id: string;
  email: string;
  account_type: string;
  onboarding_step: string;
  is_active: boolean;
}

export interface UserLocation {
  country_name: string;
  latitude: number;
  longitude: number;
}

export interface UserInterests {
  localities: string[];
  neighborhoods: Record<string, string[]>;
  properties: Record<string, string[]>;
}

export interface UserState {
  onboardingStep: string;
  hasCheckedOnboarding: boolean;
  userDismissedModal: boolean;
  userInterests: UserInterests;
}
