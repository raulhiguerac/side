import axios from "axios";
import { API } from "@/config";
import { applyAuthInterceptor } from "@/api/clients/interceptors";

const propertiesClient = axios.create({
  baseURL: API.PROPERTIES_BASE_URL,
  timeout: 8000,
  withCredentials: true,
});

applyAuthInterceptor(propertiesClient);

export default propertiesClient;
