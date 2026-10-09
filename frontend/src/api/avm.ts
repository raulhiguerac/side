import avmClient from "@/api/clients/avm";
import { AVM_ENDPOINTS } from "@/constants/avmEndpoints";
import type {
  AvmPredictRequest,
  AvmPredictResponse,
} from "@/types/avm/predict";

export async function predict(
  payload: AvmPredictRequest
): Promise<AvmPredictResponse> {
  const { data } = await avmClient.post<AvmPredictResponse>(
    AVM_ENDPOINTS.predict,
    payload
  );
  return data;
}
