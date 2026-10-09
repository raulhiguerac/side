import propertiesClient from "@/api/clients/properties";
import { PROPERTIES_ENDPOINTS } from "@/constants/propertiesEndpoints";
import type {
  BulkJobAccepted,
  BulkJobsFilters,
  BulkJobsPage,
  BulkJobStatusDetail,
  BulkUploadUrl,
} from "@/types/admin/bulk";
import type {
  AdminPromotionsPage,
  PromotionPayload,
} from "@/types/admin/promotions";
import type {
  AdminPropertiesFilters,
  AdminPropertiesPage,
  AdminPropertyDetail,
} from "@/types/admin/properties";
import type {
  ListingStatus,
  VerificationStatus,
} from "@/types/properties/base";
import type { PageParams } from "@/types/shared/pagination";

export async function getProperties(
  params: PageParams & AdminPropertiesFilters
): Promise<AdminPropertiesPage> {
  const { data } = await propertiesClient.get<AdminPropertiesPage>(
    PROPERTIES_ENDPOINTS.adminList,
    { params }
  );
  return data;
}

export async function getProperty(id: string): Promise<AdminPropertyDetail> {
  const { data } = await propertiesClient.get<AdminPropertyDetail>(
    PROPERTIES_ENDPOINTS.adminDetail(id)
  );
  return data;
}

export async function setVerification(
  id: string,
  verificationStatus: VerificationStatus,
  rejectionReason?: string
): Promise<void> {
  await propertiesClient.patch(PROPERTIES_ENDPOINTS.adminVerification(id), {
    verification_status: verificationStatus,
    // Omitido y no `null`: el backend lo prohíbe si no se está rechazando.
    ...(rejectionReason ? { rejection_reason: rejectionReason } : {}),
  });
}

export async function setStatus(
  id: string,
  status: ListingStatus
): Promise<void> {
  await propertiesClient.patch(PROPERTIES_ENDPOINTS.adminStatus(id), {
    status,
  });
}

export async function getPromotions(
  params: PageParams
): Promise<AdminPromotionsPage> {
  const { data } = await propertiesClient.get<AdminPromotionsPage>(
    PROPERTIES_ENDPOINTS.adminPromotions,
    { params }
  );
  return data;
}

export async function createPromotion(
  propertyId: string,
  payload: PromotionPayload
): Promise<void> {
  await propertiesClient.post(PROPERTIES_ENDPOINTS.adminPromotions, {
    property_id: propertyId,
    promoted_days: payload.promotedDays,
    priority: payload.priority,
  });
}

export async function removePromotion(propertyId: string): Promise<void> {
  await propertiesClient.delete(
    PROPERTIES_ENDPOINTS.adminPropertyPromotions(propertyId)
  );
}

export async function getBulkJobs(
  params: PageParams & BulkJobsFilters
): Promise<BulkJobsPage> {
  const { data } = await propertiesClient.get<BulkJobsPage>(
    PROPERTIES_ENDPOINTS.adminBulkJobs,
    { params }
  );
  return data;
}

export async function getBulkJobStatus(
  id: string
): Promise<BulkJobStatusDetail> {
  const { data } = await propertiesClient.get<BulkJobStatusDetail>(
    PROPERTIES_ENDPOINTS.adminBulkJobStatus(id)
  );
  return data;
}

export async function requestBulkUploadUrl(
  filename: string
): Promise<BulkUploadUrl> {
  const { data } = await propertiesClient.post<BulkUploadUrl>(
    PROPERTIES_ENDPOINTS.adminBulkUploadUrl,
    { filename }
  );
  return data;
}

export async function startBulkJob(
  storageKey: string
): Promise<BulkJobAccepted> {
  const { data } = await propertiesClient.post<BulkJobAccepted>(
    PROPERTIES_ENDPOINTS.adminBulkJobs,
    { storage_key: storageKey }
  );
  return data;
}
