import usersClient from "@/api/clients/users";
import { USERS_ENDPOINTS } from "@/constants/usersEndpoints";
import type {
  AuthProfileResponse,
  ChangePasswordPayload,
  LoginPayload,
  RegisterPayload,
  ResetPasswordPayload,
} from "@/types/users/auth";
import type { AccountIntent, User } from "@/types/users/base";
import type {
  NeighborhoodSelection,
  UserInterests,
} from "@/types/users/interests";
import type {
  CurrentUserProfileOut,
  PhotoUploadOut,
  ProfileUpdatePayload,
} from "@/types/users/profile";

export async function login(payload: LoginPayload): Promise<void> {
  await usersClient.post(USERS_ENDPOINTS.login, payload);
}

export async function register(payload: RegisterPayload): Promise<void> {
  await usersClient.post(USERS_ENDPOINTS.register, payload);
}

export async function logout(): Promise<void> {
  await usersClient.post(USERS_ENDPOINTS.logout, {});
}

export async function changePassword(
  payload: ChangePasswordPayload
): Promise<void> {
  await usersClient.post(USERS_ENDPOINTS.changePassword, payload);
}

export async function requestPasswordReset(email: string): Promise<void> {
  await usersClient.post(USERS_ENDPOINTS.resetPasswordRequest, { email });
}

export async function confirmPasswordReset(
  token: string,
  payload: ResetPasswordPayload
): Promise<void> {
  await usersClient.post(USERS_ENDPOINTS.resetPasswordConfirm, payload, {
    headers: { Authorization: `Bearer ${token}` },
  });
}

export async function getAccount(): Promise<User> {
  const { data } = await usersClient.get<User>(USERS_ENDPOINTS.me);
  return data;
}

// Sin uso: el backend aún no tiene DELETE /v1/users/me.
export async function deleteAccount(): Promise<void> {
  await usersClient.delete(USERS_ENDPOINTS.me);
}

export async function deactivateAccount(): Promise<void> {
  await usersClient.post(USERS_ENDPOINTS.deactivate, {});
}

export async function getAuthProfile(): Promise<AuthProfileResponse> {
  const { data } = await usersClient.get<AuthProfileResponse>(
    USERS_ENDPOINTS.profile
  );
  return data;
}

export async function updateProfile(
  payload: ProfileUpdatePayload
): Promise<void> {
  await usersClient.patch(USERS_ENDPOINTS.profile, payload);
}

export async function uploadProfilePhoto(file: File): Promise<PhotoUploadOut> {
  const body = new FormData();
  body.append("file", file);
  const { data } = await usersClient.post<PhotoUploadOut>(
    USERS_ENDPOINTS.profilePhoto,
    body
  );
  return data;
}

export async function getPublicProfile(
  accountId: string
): Promise<CurrentUserProfileOut> {
  const { data } = await usersClient.get<CurrentUserProfileOut>(
    USERS_ENDPOINTS.publicProfile(accountId)
  );
  return data;
}

export async function getInterests(): Promise<UserInterests> {
  const { data } = await usersClient.get<UserInterests>(
    USERS_ENDPOINTS.interests
  );
  return data;
}

export async function saveIntent(intent: AccountIntent): Promise<void> {
  await usersClient.post(USERS_ENDPOINTS.onboardingIntent, { intent });
}

export async function saveCities(localityIds: string[]): Promise<void> {
  await usersClient.post(USERS_ENDPOINTS.onboardingCity, {
    locality_ids: localityIds,
  });
}

export async function saveNeighborhoods(
  localities: NeighborhoodSelection[]
): Promise<void> {
  await usersClient.post(USERS_ENDPOINTS.onboardingNeighborhood, {
    localities,
  });
}

export async function savePropertyTypes(
  localityId: string,
  propertyTypes: string[]
): Promise<void> {
  await usersClient.post(USERS_ENDPOINTS.onboardingPropertyType, {
    locality_id: localityId,
    property_type: propertyTypes,
  });
}
