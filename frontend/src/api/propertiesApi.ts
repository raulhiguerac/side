import axios from "axios";
import { API } from "@/config";

const propertiesApi = axios.create({
  baseURL: API.PROPERTIES_BASE_URL,
});

export default propertiesApi;
