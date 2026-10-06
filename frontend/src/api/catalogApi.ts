import axios from "axios";
import { API } from "@/config";
import { applyAuthInterceptor } from "@/api/interceptors";

const catalogApi = axios.create({
  baseURL: API.CATALOG_BASE_URL,
  timeout: 8000,
  withCredentials: true,
});

applyAuthInterceptor(catalogApi);

export default catalogApi;
