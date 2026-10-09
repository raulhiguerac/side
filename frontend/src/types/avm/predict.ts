import type { AvmFormPayload } from "@/types/avm/form";

export interface AvmPredictRequest extends AvmFormPayload {
  lat: number;
  lon: number;
  barrio_ideca: string;
}

export interface AvmPredictResponse {
  predicted_price: number;
}
