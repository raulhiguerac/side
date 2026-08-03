import type { ListingStatus } from "@/types/feed";
import type { VerificationStatus } from "@/types/properties";

/**
 * Espejo de las dos máquinas de estado del backend, con la traducción de cada
 * transición a la acción que el admin ve.
 *
 * Fuente de verdad:
 * - `moderation/verify.py` → `_ALLOWED_TRANSITIONS` (VerificationStatus)
 * - `moderation/set_status.py` → `_ALLOWED_TRANSITIONS` (ListingStatus)
 *
 * Si acá sobra una transición, el request sale y vuelve `409
 * INVALID_STATUS_TRANSITION`. Si falta, la acción simplemente no se ofrece.
 * Las dos tablas son **independientes**: publicar no exige estar verificada.
 */

/** Cómo se pinta el botón. La regla de negocio no depende de esto. */
export type ActionTone = "primary" | "danger" | "neutral";

export interface ModerationAction<TTarget extends string> {
  /** Valor que viaja en el body al backend. */
  target: TTarget;
  label: string;
  tone: ActionTone;
  /**
   * El backend exige `rejection_reason` al rechazar y lo prohíbe en el resto
   * (`VerifyPropertyRequest.validate_rejection_reason`), así que estas son las
   * únicas acciones que abren el modal del motivo.
   */
  requiresReason?: boolean;
}

/**
 * `verified` dejó de ser terminal: una property aprobada que después viola las
 * normas vuelve a la cola o pierde el sello. Lo único prohibido es volver a
 * `unverified`, que solo existe como estado inicial.
 */
export const VERIFICATION_TRANSITIONS: Record<
  VerificationStatus,
  ModerationAction<VerificationStatus>[]
> = {
  unverified: [
    { target: "pending", label: "Enviar a revisión", tone: "primary" },
  ],
  pending: [
    { target: "verified", label: "Aprobar", tone: "primary" },
    {
      target: "rejected",
      label: "Rechazar",
      tone: "danger",
      requiresReason: true,
    },
  ],
  rejected: [{ target: "pending", label: "Reencolar", tone: "primary" }],
  verified: [
    { target: "pending", label: "Reencolar", tone: "neutral" },
    {
      target: "rejected",
      label: "Revocar",
      tone: "danger",
      requiresReason: true,
    },
  ],
};

/**
 * Ojo con `inactive`: el dueño solo puede hacer `draft ↔ active`, así que una
 * property que un admin desactiva no la puede republicar nadie más que un
 * admin. Es el takedown de facto.
 */
export const LISTING_STATUS_TRANSITIONS: Record<
  ListingStatus,
  ModerationAction<ListingStatus>[]
> = {
  draft: [{ target: "active", label: "Publicar", tone: "primary" }],
  active: [
    { target: "draft", label: "Pasar a borrador", tone: "neutral" },
    { target: "inactive", label: "Desactivar", tone: "danger" },
    { target: "sold", label: "Marcar como vendida", tone: "neutral" },
    { target: "rented", label: "Marcar como arrendada", tone: "neutral" },
  ],
  inactive: [
    { target: "active", label: "Reactivar", tone: "primary" },
    { target: "draft", label: "Pasar a borrador", tone: "neutral" },
  ],
  sold: [{ target: "inactive", label: "Desactivar", tone: "neutral" }],
  rented: [{ target: "inactive", label: "Desactivar", tone: "neutral" }],
};
