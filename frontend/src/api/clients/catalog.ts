import axios from "axios";
import { API } from "@/config";
import { applyAuthInterceptor } from "@/api/clients/interceptors";

const catalogClient = axios.create({
  baseURL: API.CATALOG_BASE_URL,
  timeout: 8000,
  withCredentials: true,
});

applyAuthInterceptor(catalogClient);

export default catalogClient;
