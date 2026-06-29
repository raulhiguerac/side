import axios from "axios";
import { API } from "@/config";
import { applyAuthInterceptor } from "@/api/interceptors";

const usersApi = axios.create({
  baseURL: API.USERS_BASE_URL,
  timeout: 8000,
  withCredentials: true,
});

applyAuthInterceptor(usersApi);

export default usersApi;
