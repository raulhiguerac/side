import axios from "axios";
import { useUserStore } from "@/stores/user";

export async function getCitiesByCountry(id: string) {
  try {
    const raw = localStorage.getItem(`cities:${id}`);
    if (raw) return JSON.parse(raw);
    const { data } = await axios.get(
      "http://localhost:8001/v1/localities/by-country",
      {
        params: { country_id: id },
      }
    );
    localStorage.setItem(`cities:${id}`, JSON.stringify(data));
    return data;
  } catch (error) {
    console.error("Error al obtener las ciudades soportadas:", error);
  }
}

export async function locations() {
  const userStore = useUserStore();
  const countryDetected = await userStore.detectLocation();

  const countries = async () => {
    try {
      const raw = localStorage.getItem("countries");
      if (raw) return JSON.parse(raw);
      const { data } = await axios.get("http://localhost:8001/v1/countries");
      localStorage.setItem("countries", JSON.stringify(data));
      return data;
    } catch (error) {
      console.error("Error al obtener los paises soportados:", error);
    }
  };

  const data = await countries();
  const match = data?.find(
    (country: any) => country.name === countryDetected.country_name
  );
  const countryUser: string | undefined = match?.id;

  return { countryDetected, countryUser };
}
