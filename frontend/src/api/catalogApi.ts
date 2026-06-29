import axios from "axios";
import { API } from "@/config";

const catalogApi = axios.create({
  baseURL: API.CATALOG_BASE_URL,
  timeout: 8000,
});

export default catalogApi;
