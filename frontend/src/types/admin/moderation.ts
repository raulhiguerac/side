import type { ListingStatus } from "@/types/feed";
import type { VerificationStatus } from "@/types/properties";

/** Solo los campos que cambiaron; cada uno es su propio endpoint, así que son uno o dos requests. */
export interface ModerationPayload {
  verificationStatus?: VerificationStatus;
  /** Obligatorio si `verificationStatus` es `rejected`; prohibido si no. */
  rejectionReason?: string;
  status?: ListingStatus;
}
