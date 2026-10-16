<template>
  <div class="lg:h-full flex flex-col">
    <!-- Header -->
    <div class="mb-8">
      <h1 class="text-brand-text text-2xl font-bold">Cuenta</h1>
      <p class="text-brand-muted text-sm mt-1">
        Gestiona tu cuenta y datos personales
      </p>
    </div>

    <!-- Danger Zone -->
    <div class="bg-white rounded-2xl border border-red-200 p-6 md:p-8">
      <div class="flex items-start gap-4 mb-6">
        <div
          class="w-12 h-12 bg-red-50 rounded-xl flex items-center justify-center flex-shrink-0"
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            width="24"
            height="24"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
            stroke-linecap="round"
            stroke-linejoin="round"
            class="text-red-500"
          >
            <path
              d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"
            />
            <line x1="12" x2="12" y1="9" y2="13" />
            <line x1="12" x2="12.01" y1="17" y2="17" />
          </svg>
        </div>
        <div>
          <h3 class="text-red-600 font-semibold">Zona de peligro</h3>
          <p class="text-brand-muted text-sm">
            Estas acciones son irreversibles. Procede con cuidado.
          </p>
        </div>
      </div>

      <!-- Deactivate Account -->
      <div class="border border-brand-divider rounded-xl p-5 mb-4">
        <div
          class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4"
        >
          <div>
            <h4 class="text-brand-text font-semibold">Desactivar cuenta</h4>
            <p class="text-brand-muted text-sm">
              Tu cuenta será desactivada temporalmente. Podrás reactivarla
              iniciando sesión.
            </p>
          </div>
          <BaseButton
            variant="danger-soft"
            @click="showDeactivateModal = true"
            class="shrink-0"
          >
            Desactivar
          </BaseButton>
        </div>
      </div>

      <!-- Delete Account: deshabilitado, el backend no implementa el borrado de cuentas.
      <div class="border border-red-200 rounded-xl p-5 bg-red-50/50">
        <div
          class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4"
        >
          <div>
            <h4 class="text-red-600 font-semibold">
              Eliminar cuenta permanentemente
            </h4>
            <p class="text-brand-muted text-sm">
              Todos tus datos serán eliminados. Esta acción no se puede
              deshacer.
            </p>
          </div>
          <BaseButton
  variant="danger"
  @click="showDeleteModal = true"
  class="shrink-0"
>
            Eliminar cuenta
          </BaseButton>
        </div>
      </div>
      -->
    </div>

    <!-- Deactivate Modal -->
    <div
      v-if="showDeactivateModal"
      class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4"
      @click.self="closeDeactivateModal"
    >
      <div class="bg-white rounded-2xl max-w-md w-full p-6">
        <div class="flex items-center gap-4 mb-4">
          <div
            class="w-12 h-12 bg-yellow-100 rounded-xl flex items-center justify-center"
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              width="24"
              height="24"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
              class="text-yellow-600"
            >
              <circle cx="12" cy="12" r="10" />
              <line x1="12" x2="12" y1="8" y2="12" />
              <line x1="12" x2="12.01" y1="16" y2="16" />
            </svg>
          </div>
          <div>
            <h3 class="text-brand-text font-bold text-lg">Desactivar cuenta</h3>
          </div>
        </div>

        <p class="text-brand-muted text-sm mb-6">
          Tu cuenta será desactivada y no podrás acceder hasta que la reactives.
          Tus propiedades no serán visibles en el marketplace.
        </p>

        <div class="flex flex-col gap-1.5 mb-6">
          <label class="text-brand-text text-sm font-semibold">
            Escribe "DESACTIVAR" para confirmar
          </label>
          <input
            v-model="deactivateConfirm"
            type="text"
            placeholder="DESACTIVAR"
            class="w-full h-12 px-4 bg-white border-[1.5px] border-brand-border rounded-xl text-sm text-brand-text placeholder:text-brand-placeholder focus:outline-none focus:border-yellow-500 transition-colors"
          />
        </div>

        <FormMessage v-if="error" variant="error" class="mb-4">
          {{ error }}
        </FormMessage>

        <div class="flex gap-3">
          <BaseButton
            variant="ghost"
            size="lg"
            @click="closeDeactivateModal"
            class="flex-1"
          >
            Cancelar
          </BaseButton>
          <BaseButton
            variant="danger"
            size="lg"
            @click="deactivate"
            :disabled="deactivateConfirm !== 'DESACTIVAR' || deactivating"
            class="flex-1"
          >
            {{ deactivating ? "Procesando..." : "Desactivar" }}
          </BaseButton>
        </div>
      </div>
    </div>

    <!-- Delete Modal: deshabilitado junto con el botón de arriba.
    <div
      v-if="showDeleteModal"
      class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4"
      @click.self="showDeleteModal = false"
    >
      <div class="bg-white rounded-2xl max-w-md w-full p-6">
        <div class="flex items-center gap-4 mb-4">
          <div
            class="w-12 h-12 bg-red-100 rounded-xl flex items-center justify-center"
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              width="24"
              height="24"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
              class="text-red-600"
            >
              <path d="M3 6h18" />
              <path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6" />
              <path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2" />
              <line x1="10" x2="10" y1="11" y2="17" />
              <line x1="14" x2="14" y1="11" y2="17" />
            </svg>
          </div>
          <div>
            <h3 class="text-red-600 font-bold text-lg">Eliminar cuenta</h3>
          </div>
        </div>

        <p class="text-brand-muted text-sm mb-4">
          Esta acción es
          <strong class="text-red-600">permanente e irreversible</strong>. Se
          eliminarán:
        </p>

        <ul class="text-brand-muted text-sm mb-6 space-y-1">
          <li class="flex items-center gap-2">
            <span class="text-red-500">•</span> Tu perfil y datos personales
          </li>
          <li class="flex items-center gap-2">
            <span class="text-red-500">•</span> Todas tus propiedades publicadas
          </li>
          <li class="flex items-center gap-2">
            <span class="text-red-500">•</span> Tu historial de actividad
          </li>
        </ul>

        <div class="flex flex-col gap-1.5 mb-6">
          <label class="text-brand-text text-sm font-semibold">
            Escribe "ELIMINAR MI CUENTA" para confirmar
          </label>
          <input
            v-model="deleteConfirm"
            type="text"
            placeholder="ELIMINAR MI CUENTA"
            class="w-full h-12 px-4 bg-white border-[1.5px] border-red-300 rounded-xl text-sm text-brand-text placeholder:text-brand-placeholder focus:outline-none focus:border-red-500 transition-colors"
          />
        </div>

        <div class="flex gap-3">
          <BaseButton
  variant="ghost"
  size="lg"
  @click="showDeleteModal = false"
  class="flex-1"
>
            Cancelar
          </BaseButton>
          <BaseButton
  variant="danger"
  size="lg"
  @click="deleteAccount"
  :disabled="deleteConfirm !== 'ELIMINAR MI CUENTA' || isLoading"
  class="flex-1"
>
            {{ isLoading ? "Eliminando..." : "Eliminar cuenta" }}
          </BaseButton>
        </div>
      </div>
    </div>
    -->
  </div>
</template>

<script lang="ts" setup>
import BaseButton from "@/components/shared/BaseButton.vue";
import { ref } from "vue";
import FormMessage from "@/components/shared/FormMessage.vue";
import { useAccountSettings } from "@/composables/users/useAccountSettings";

const { deactivating, error, deactivate, reset } = useAccountSettings();

const showDeactivateModal = ref(false);
const deactivateConfirm = ref("");

function closeDeactivateModal() {
  showDeactivateModal.value = false;
  deactivateConfirm.value = "";
  reset();
}

// Deshabilitado: el backend no implementa el borrado de cuentas (ver el template).
// const showDeleteModal = ref(false);
// const deleteConfirm = ref("");
// const deleteAccount = async () => {
//   isLoading.value = true;
//   try {
//     await usersApi.deleteAccount();
//     authStore.user = null;
//     authStore.isAuthenticated = false;
//     authStore._authChecked = false;
//     router.push("/");
//   } catch (error) {
//     logger.error("Error al eliminar cuenta:", error);
//     alert("Error al eliminar la cuenta");
//   } finally {
//     isLoading.value = false;
//     showDeleteModal.value = false;
//   }
// };
</script>
