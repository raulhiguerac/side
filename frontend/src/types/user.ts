export interface User {
  account_id: string;
  email: string;
  account_type: string;
  onboarding_step: string;
  is_active: boolean;
  is_admin: boolean;
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
  userInterests: UserInterests;
}

export type AccountIntent = "buyer" | "seller" | "renter" | "explorer";

export interface CurrentUserPerson {
  first_name: string;
  last_name: string;
  phone: string | null;
  photo_url: string | null;
  description: string | null;
  intent: AccountIntent | null;
  account_type: "person";
  created_at: string | null;
}

export interface CurrentUserOrganization {
  display_name: string;
  phone: string | null;
  photo_url: string | null;
  description: string | null;
  intent: AccountIntent | null;
  account_type: "organization";
  created_at: string | null;
}

export interface CurrentUserProfileOut {
  profile: CurrentUserPerson | CurrentUserOrganization;
}

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
