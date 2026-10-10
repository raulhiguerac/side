export interface UserLocation {
  country_name: string;
  latitude: number;
  longitude: number;
}

export interface UserInterests {
  localities: string[];
  neighborhoods: Record<string, string[]>;
  properties: Record<string, string[]>;
}

export interface UserState {
  userInterests: UserInterests;
}

export interface NeighborhoodSelection {
  locality_id: string;
  neighborhoods: Record<number, string>;
}
