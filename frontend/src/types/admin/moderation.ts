import type {
  ListingStatus,
  VerificationStatus,
} from "@/types/properties/base";

/** Solo los campos que cambiaron; cada uno es su propio endpoint, así que son uno o dos requests. */
export interface ModerationPayload {
  verificationStatus?: VerificationStatus;
  /** Obligatorio si `verificationStatus` es `rejected`; prohibido si no. */
  rejectionReason?: string;
  status?: ListingStatus;
}
