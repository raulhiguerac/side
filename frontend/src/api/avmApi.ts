import axios from "axios";
import { API } from "@/config";

const avmApi = axios.create({
  baseURL: API.AVM_BASE_URL,
  timeout: 8000,
});

export default avmApi;
