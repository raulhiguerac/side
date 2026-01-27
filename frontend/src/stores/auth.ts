/**
 * 🏪 AUTH STORE - La "memoria" de autenticación de tu app
 *
 * Imagina que tu app es una tienda:
 * - La COOKIE es tu tarjeta de membresía (el backend la verifica)
 * - El STORE es la memoria del cajero (recuerda quién eres mientras compras)
 *
 * Cuando recargas la página, el cajero "olvida" quién eres,
 * pero tu tarjeta (cookie) sigue válida, así que le preguntas
 * al backend "¿quién soy?" y el cajero vuelve a recordarte.
 */

import { defineStore } from "pinia";
import axios from "axios";
import router from "@/router";

// ---------------------------------------------------------
// 📦 TIPOS - Definen la "forma" de los datos
// ---------------------------------------------------------

/**
 * ¿Cómo se ve un Usuario?
 * Es como una ficha con sus datos básicos
 */
interface UserProfile {
  first_name: string;
  last_name: string;
  phone: string;
  photo_url?: string;
  description?: string;
  intent?: "buyer" | "seller" | "renter" | "explorer";
  account_type: "person" | "organization";
}

interface User extends UserProfile {
  id?: string;
  email?: string; // El email no viene en /profile, viene de otro endpoint
}

// Respuesta del endpoint /users/me/profile
interface ProfileResponse {
  profile: UserProfile;
}

/**
 * ¿Qué guarda el Store?
 * Es el "estado" - lo que la app recuerda
 */
interface AuthState {
  user: User | null; // Puede ser un User o null (no logueado)
  isAuthenticated: boolean; // true = logueado, false = no logueado
  isLoading: boolean; // true = estamos verificando, false = ya sabemos
  _authChecked: boolean; // true = ya verificamos una vez (evita llamadas duplicadas)
}

// ---------------------------------------------------------
// 🏪 EL STORE - Donde guardamos todo
// ---------------------------------------------------------

export const useAuthStore = defineStore("auth", {
  /**
   * STATE = Los datos que guardamos
   * Es como las variables de la tienda
   */
  state: (): AuthState => ({
    user: null, // Al inicio no sabemos quién es
    isAuthenticated: false, // Al inicio asumimos que no está logueado
    isLoading: true, // Al inicio estamos verificando
    _authChecked: false, // Aún no hemos verificado
  }),

  /**
   * GETTERS = Datos calculados (como fórmulas de Excel)
   * Se actualizan automáticamente cuando cambia el state
   */
  getters: {
    /**
     * Nombre completo del usuario
     * Si no hay usuario, devuelve string vacío
     */
    fullName(): string {
      if (!this.user) return "";
      return `${this.user.first_name} ${this.user.last_name}`;
    },

    /**
     * ¿Es una organización/inmobiliaria?
     */
    isOrganization(): boolean {
      return this.user?.account_type === "organization";
    },

    /**
     * photo_url del usuario (o un placeholder si no tiene)
     */
    userAvatar(): string {
      if (this.user?.photo_url) return this.user.photo_url;
      // Si no tiene photo_url, generamos uno con sus iniciales
      const name = this.fullName || "User";
      return `https://ui-avatars.com/api/?name=${encodeURIComponent(
        name
      )}&background=22C55E&color=fff`;
    },
  },

  /**
   * ACTIONS = Funciones que hacen cosas (como empleados de la tienda)
   * Pueden ser async (esperar respuestas del servidor)
   */
  actions: {
    /**
     * 🔍 VERIFICAR AUTENTICACIÓN
     *
     * Pregunta al backend: "¿Quién soy?"
     * El backend revisa la cookie y responde con los datos del usuario
     *
     * Cuándo usar: Al cargar la app (App.vue o router)
     */
    async checkAuth(force = false): Promise<void> {
      // Si ya verificamos y no es forzado, no hacemos nada
      if (this._authChecked && !force) {
        return;
      }

      // Si ya estamos cargando, no hacemos otra llamada
      if (this.isLoading && this._authChecked) {
        return;
      }

      this.isLoading = true;

      try {
        // Preguntamos al backend (la cookie se envía automáticamente)
        const response = await axios.get<ProfileResponse>(
          "http://localhost:8000/v1/users/me/profile",
          { withCredentials: true }
        );

        // Si llegamos aquí, el usuario está autenticado
        this.user = response.data.profile;
        this.isAuthenticated = true;
      } catch (error) {
        // Si hay error, el usuario NO está autenticado
        this.user = null;
        this.isAuthenticated = false;
      } finally {
        this.isLoading = false;
        this._authChecked = true; // Ya verificamos
      }
    },

    /**
     * 🔑 LOGIN
     *
     * Envía email y password al backend
     * Si es correcto, el backend pone una cookie
     * Luego llamamos checkAuth() para obtener los datos del usuario
     *
     * @param email - El correo del usuario
     * @param password - La contraseña
     * @returns true si el login fue exitoso, false si falló
     */
    async login(email: string, password: string): Promise<boolean> {
      try {
        // 1. Hacemos login (el backend pone la cookie)
        await axios.post(
          "http://localhost:8000/v1/auth/login",
          { email, password },
          { withCredentials: true }
        );

        // 2. Obtenemos los datos del usuario con la cookie (forzamos la llamada)
        await this.checkAuth(true);

        return this.isAuthenticated;
      } catch (error) {
        // Login fallido
        this.user = null;
        this.isAuthenticated = false;
        return false;
      }
    },

    /**
     * 📝 REGISTRO
     *
     * Crea una nueva cuenta
     * Luego llama checkAuth() para obtener los datos del usuario
     *
     * @param userData - Los datos del nuevo usuario
     * @returns true si el registro fue exitoso
     */
    async register(userData: {
      email: string;
      password: string;
      first_name: string;
      last_name: string;
      phone: string;
      account_type: "person" | "organization";
    }): Promise<boolean> {
      try {
        // 1. Hacemos el registro (el backend pone la cookie)
        await axios.post(
          "http://localhost:8000/v1/auth/register",
          {
            email: userData.email,
            password: userData.password,
            first_name: userData.first_name,
            last_name: userData.last_name,
            phone: userData.phone,
            account_type: userData.account_type,
          },
          { withCredentials: true }
        );

        // 2. Obtenemos los datos del usuario con la cookie (forzamos la llamada)
        await this.checkAuth(true);

        return this.isAuthenticated;
      } catch (error) {
        return false;
      }
    },

    /**
     * 🚪 LOGOUT
     *
     * Cierra la sesión:
     * 1. Le dice al backend que borre la cookie
     * 2. Limpia el store
     * 3. Redirige al inicio
     */
    async logout(): Promise<void> {
      try {
        // Le pedimos al backend que invalide la cookie
        await axios.post(
          "http://localhost:8000/v1/auth/logout",
          {},
          { withCredentials: true }
        );
      } catch (error) {
        // Aunque falle, limpiamos el estado local
        console.error("Error en logout:", error);
      } finally {
        // Limpiamos todo
        this.user = null;
        this.isAuthenticated = false;
        this._authChecked = false; // Reseteamos para la próxima sesión

        // Redirigimos al inicio
        router.push("/");
      }
    },

    /**
     * 🔄 ACTUALIZAR USUARIO
     *
     * Si el usuario cambia su perfil, actualizamos el store
     *
     * @param userData - Los nuevos datos (parciales)
     */
    updateUser(userData: Partial<User>): void {
      if (this.user) {
        // Partial<User> significa "algunos campos de User"
        // ...this.user = copia los datos actuales
        // ...userData = sobrescribe con los nuevos
        this.user = { ...this.user, ...userData };
      }
    },
  },
});
