import type { PropertyCard } from "@/types/feed/cards";
import type { AccountIntent } from "@/types/users/base";

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

export interface PublicUserPropertiesResponse {
  items: PropertyCard[];
  has_more: boolean;
}

export interface ProfileUpdatePayload {
  first_name: string;
  last_name: string;
  phone: string;
  description: string;
}
