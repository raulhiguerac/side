import type { AccountIntent } from "@/types/users/base";

export interface AuthProfile {
  first_name: string;
  last_name: string;
  phone: string;
  photo_url?: string;
  description?: string;
  intent?: AccountIntent;
  account_type: "person" | "organization";
}

export interface AuthUser extends AuthProfile {
  id?: string;
  email?: string;
}

export interface AuthProfileResponse {
  profile: AuthProfile;
}

export interface AuthState {
  user: AuthUser | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  _authChecked: boolean;
  onboardingStep: string;
  isAdmin: boolean;
  accountId: string | null;
}

export interface RegisterPayload {
  email: string;
  password: string;
  first_name: string;
  last_name: string;
  phone: string;
  account_type: "person" | "organization";
}

export interface LoginPayload {
  email: string;
  password: string;
}

export interface ChangePasswordPayload {
  current_password: string;
  new_password: string;
}
