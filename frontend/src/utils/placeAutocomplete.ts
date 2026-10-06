import type { SelectedPlace } from "@/types/maps";

// Monta el autocompletado de Google Places en `container` y avisa el lugar elegido.
export async function mountPlaceAutocomplete(
  container: HTMLElement,
  onSelect: (place: SelectedPlace) => void
): Promise<void> {
  await google.maps.importLibrary("places");
  const el = new google.maps.places.PlaceAutocompleteElement({});
  container.appendChild(el);

  el.addEventListener("gmp-select", async (event) => {
    const place = event.placePrediction.toPlace();
    await place.fetchFields({
      fields: ["displayName", "formattedAddress", "location"],
    });
    if (!place.location) return;
    onSelect({
      latitude: place.location.lat(),
      longitude: place.location.lng(),
      address: place.formattedAddress ?? "",
    });
  });
}
