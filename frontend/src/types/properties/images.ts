export interface PropertyImageCard {
  id: string;
  url: string;
  is_cover: boolean;
  display_order: number;
}

export interface PresignedUrlItem {
  upload_url: string;
  public_url: string;
  key: string;
}

export interface PresignedUrlsResponse {
  batch_id: string;
  items: PresignedUrlItem[];
}
