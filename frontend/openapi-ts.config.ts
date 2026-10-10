import { defineConfig } from "@hey-api/openapi-ts";

export default defineConfig({
  input: "http://localhost:8001/openapi.json",
  output: "src/types/generated/catalog",
  plugins: ["@hey-api/typescript"],
});