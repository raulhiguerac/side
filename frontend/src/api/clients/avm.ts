import axios from "axios";
import { API } from "@/config";

const avmClient = axios.create({
  baseURL: API.AVM_BASE_URL,
  timeout: 8000,
});

export default avmClient;
