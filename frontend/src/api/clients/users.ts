import axios from "axios";
import { API } from "@/config";
import { applyAuthInterceptor } from "@/api/clients/interceptors";

const usersClient = axios.create({
  baseURL: API.USERS_BASE_URL,
  timeout: 8000,
  withCredentials: true,
});

applyAuthInterceptor(usersClient);

export default usersClient;
