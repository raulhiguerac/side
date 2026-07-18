import axios from "axios";
import { API } from "@/config";
import { applyAuthInterceptor } from "@/api/interceptors";

const propertiesApi = axios.create({
  baseURL: API.PROPERTIES_BASE_URL,
  timeout: 8000,
  withCredentials: true,
});

applyAuthInterceptor(propertiesApi);

export default propertiesApi;
