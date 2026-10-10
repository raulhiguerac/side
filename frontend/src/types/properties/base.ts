export type ListingStatus = "draft" | "active" | "inactive" | "sold" | "rented";
export type PropertyType = "house" | "apartment";
export type ListingType = "sale" | "rent";

export type VerificationStatus =
  | "unverified"
  | "pending"
  | "verified"
  | "rejected";

export type ListingStatusTab = "all" | ListingStatus;
