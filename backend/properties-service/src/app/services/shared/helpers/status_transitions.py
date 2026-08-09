from app.models.listing import ListingStatus, VerificationStatus

# Única fuente de las máquinas de estado del listing: los use cases las aplican
# y el detalle admin las publica, así que la UI no puede ofrecer un destino que
# el backend vaya a rechazar. Verificación y estado son independientes entre sí:
# publicar no exige estar verificada.

# `verified` no es terminal — una property aprobada puede volver a la cola o
# perder el sello. Lo único prohibido es volver a `unverified`, que solo existe
# como estado inicial.
VERIFICATION_TRANSITIONS: dict[VerificationStatus, list[VerificationStatus]] = {
    VerificationStatus.unverified: [VerificationStatus.pending],
    VerificationStatus.pending: [VerificationStatus.verified, VerificationStatus.rejected],
    VerificationStatus.rejected: [VerificationStatus.pending],
    VerificationStatus.verified: [VerificationStatus.pending, VerificationStatus.rejected],
}

# El dueño solo puede `draft ↔ active`, así que `inactive` es el takedown de facto.
LISTING_STATUS_TRANSITIONS: dict[ListingStatus, list[ListingStatus]] = {
    ListingStatus.draft: [ListingStatus.active],
    ListingStatus.active: [ListingStatus.draft, ListingStatus.inactive, ListingStatus.sold, ListingStatus.rented],
    ListingStatus.inactive: [ListingStatus.active, ListingStatus.draft],
    ListingStatus.sold: [ListingStatus.inactive],
    ListingStatus.rented: [ListingStatus.inactive],
}

# La del dueño es un toggle, no una máquina abierta: un solo destino por estado
# y nada que hacer desde `inactive`, `sold` o `rented` — de ahí solo lo saca un
# admin con `LISTING_STATUS_TRANSITIONS`.
OWNER_VISIBILITY_TRANSITIONS: dict[ListingStatus, ListingStatus] = {
    ListingStatus.draft: ListingStatus.active,
    ListingStatus.active: ListingStatus.draft,
}
