import propertiesClient from "@/api/clients/properties";
import { PROPERTIES_ENDPOINTS } from "@/constants/propertiesEndpoints";
import type { PropertyCard } from "@/types/feed/cards";
import type { FeedMapQuery, FeedPage, FeedQuery } from "@/types/feed/search";
import type { PropertyDetail } from "@/types/properties/detail";
import type {
  CreatePropertyForm,
  PropertyEditForm,
} from "@/types/properties/forms";
import type { PresignedUrlsResponse } from "@/types/properties/images";
import type { PublicUserPropertiesResponse } from "@/types/users/profile";

export async function getFeed(query: FeedQuery): Promise<FeedPage> {
  const { data } = await propertiesClient.get<FeedPage>(
    PROPERTIES_ENDPOINTS.feed,
    { params: query, paramsSerializer: { indexes: null } }
  );
  return data;
}

export async function getFeedMap(query: FeedMapQuery): Promise<PropertyCard[]> {
  const { data } = await propertiesClient.get<PropertyCard[]>(
    PROPERTIES_ENDPOINTS.feedMap,
    { params: query }
  );
  return data;
}

export async function getMyProperties(): Promise<PropertyCard[]> {
  const { data } = await propertiesClient.get<PropertyCard[]>(
    PROPERTIES_ENDPOINTS.me
  );
  return data;
}

export async function getUserListings(
  accountId: string,
  offset: number
): Promise<PublicUserPropertiesResponse> {
  const { data } = await propertiesClient.get<PublicUserPropertiesResponse>(
    PROPERTIES_ENDPOINTS.byUser(accountId),
    { params: { offset }, paramsSerializer: { indexes: null } }
  );
  return data;
}

export async function getProperty(id: string): Promise<PropertyDetail> {
  const { data } = await propertiesClient.get<PropertyDetail>(
    PROPERTIES_ENDPOINTS.byId(id)
  );
  return data;
}

export async function createProperty(
  form: CreatePropertyForm
): Promise<string> {
  const { data } = await propertiesClient.post<string>(
    PROPERTIES_ENDPOINTS.create,
    form
  );
  return data;
}

export async function updateProperty(
  id: string,
  form: PropertyEditForm
): Promise<void> {
  await propertiesClient.patch(PROPERTIES_ENDPOINTS.byId(id), form);
}

export async function deleteProperty(id: string): Promise<void> {
  await propertiesClient.delete(PROPERTIES_ENDPOINTS.byId(id));
}

export async function toggleVisibility(id: string): Promise<void> {
  await propertiesClient.post(PROPERTIES_ENDPOINTS.visibility(id));
}

export async function requestImageUploadUrls(
  propertyId: string,
  count: number
): Promise<PresignedUrlsResponse> {
  const { data } = await propertiesClient.post<PresignedUrlsResponse>(
    PROPERTIES_ENDPOINTS.imagesPresignedUrls,
    { property_id: propertyId, create_count: count }
  );
  return data;
}

export async function confirmImageUploads(
  propertyId: string,
  batchId: string,
  confirmedKeys: string[]
): Promise<void> {
  await propertiesClient.post(PROPERTIES_ENDPOINTS.imagesConfirm(propertyId), {
    batch_id: batchId,
    confirmed_keys: confirmedKeys,
  });
}

export async function deleteImages(
  propertyId: string,
  imageIds: string[]
): Promise<void> {
  await propertiesClient.delete(PROPERTIES_ENDPOINTS.images(propertyId), {
    data: { image_ids: imageIds },
  });
}
