from app.models.listing import Property, VerificationStatus


def degrade_verification(*, prop: Property) -> None:
    """Cambiar las fotos invalida la verificación: lo que se aprobó visualmente
    deja de ser lo que se publica, así que la property vuelve a la cola.

    Muta el modelo en sitio y **no** commitea — el caller ya tiene su propia
    transacción abierta, y así el cambio de fotos y la pérdida del sello entran
    o fallan juntos.

    Solo degrada desde `verified`: en `unverified`, `pending` o `rejected` no hay
    sello que quitar, y el no-op hace que llamarlo de más sea inofensivo.
    """
    if prop.verification_status == VerificationStatus.verified:
        prop.verification_status = VerificationStatus.pending
