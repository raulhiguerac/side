import { computed, onBeforeUnmount, ref } from "vue";
import axios from "axios";
import * as usersApi from "@/api/users";
import { LIMITS } from "@/config";
import { useAuthStore } from "@/stores/auth";
import type { ProfileForm } from "@/types/users/profile";
import { logger } from "@/utils/logger";

const MAX_PHOTO_MB = LIMITS.MAX_PROFILE_PHOTO_BYTES / 1024 / 1024;

function photoErrorMessage(error: unknown): string {
  if (!axios.isAxiosError(error)) return "No se pudo subir la foto";
  if (error.response?.status === 413)
    return `La foto supera los ${MAX_PHOTO_MB} MB`;
  if (error.response?.status === 415)
    return "Formato no soportado (usa JPG, PNG o WEBP)";
  return "No se pudo subir la foto";
}

function emptyForm(): ProfileForm {
  return {
    first_name: "",
    last_name: "",
    phone: "",
    description: "",
    account_type: "person",
  };
}

export function useProfileSettings() {
  const authStore = useAuthStore();

  const form = ref<ProfileForm>(emptyForm());
  const original = ref<ProfileForm>(emptyForm());
  const avatarFile = ref<File | null>(null);
  const avatarPreview = ref<string | null>(null);
  const saving = ref(false);
  const error = ref<string | null>(null);
  const success = ref<string | null>(null);

  const fieldsChanged = computed(
    () => JSON.stringify(form.value) !== JSON.stringify(original.value)
  );
  const hasChanges = computed(
    () => fieldsChanged.value || avatarFile.value !== null
  );
  const avatarUrl = computed(() => avatarPreview.value ?? authStore.userAvatar);

  function load() {
    const user = authStore.user;
    if (!user) return;
    form.value = {
      first_name: user.first_name || "",
      last_name: user.last_name || "",
      phone: user.phone || "",
      description: user.description || "",
      account_type: user.account_type || "person",
    };
    original.value = { ...form.value };
  }

  function clearAvatar() {
    if (avatarPreview.value) URL.revokeObjectURL(avatarPreview.value);
    avatarPreview.value = null;
    avatarFile.value = null;
  }

  function selectAvatar(file: File) {
    error.value = null;
    success.value = null;
    if (!LIMITS.PROFILE_PHOTO_TYPES.includes(file.type)) {
      error.value = "Formato no soportado (usa JPG, PNG o WEBP)";
      return;
    }
    if (file.size > LIMITS.MAX_PROFILE_PHOTO_BYTES) {
      error.value = `La foto supera los ${MAX_PHOTO_MB} MB`;
      return;
    }
    clearAvatar();
    avatarFile.value = file;
    avatarPreview.value = URL.createObjectURL(file);
  }

  async function save() {
    saving.value = true;
    error.value = null;
    success.value = null;
    let fieldsSaved = false;

    try {
      if (fieldsChanged.value) {
        const { first_name, last_name, phone, description } = form.value;
        await usersApi.updateProfile({
          first_name,
          last_name,
          phone,
          description,
        });
        authStore.updateUser(form.value);
        original.value = { ...form.value };
        fieldsSaved = true;
      }

      if (avatarFile.value) {
        try {
          const { photo_url } = await usersApi.uploadProfilePhoto(
            avatarFile.value
          );
          authStore.updateUser({ photo_url });
          clearAvatar();
        } catch (e) {
          logger.error("Error al subir la foto de perfil:", e);
          // Si los datos ya quedaron, decirlo evita reintentar algo guardado.
          error.value = fieldsSaved
            ? `Se guardaron tus datos, pero no la foto: ${photoErrorMessage(e)}`
            : photoErrorMessage(e);
          return;
        }
      }

      success.value = "Perfil actualizado";
    } catch (e) {
      logger.error("Error al guardar el perfil:", e);
      error.value = "No se pudieron guardar tus datos";
    } finally {
      saving.value = false;
    }
  }

  function reset() {
    form.value = { ...original.value };
    clearAvatar();
    error.value = null;
    success.value = null;
  }

  onBeforeUnmount(clearAvatar);

  return {
    form,
    avatarUrl,
    hasChanges,
    saving,
    error,
    success,
    load,
    selectAvatar,
    save,
    reset,
  };
}
