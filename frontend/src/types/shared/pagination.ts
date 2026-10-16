export interface PageRange {
  from: number;
  to: number;
}

export interface FetchPageResult<T> {
  items: T[];
  hasMore: boolean;
}

export interface PageParams {
  page: number;
  page_size: number;
}

/** Página de los listados admin de catalog (`Page[T]` del back). */
export interface AdminPage<T> {
  items: T[];
  total_items: number;
  total_pages: number;
  current_page: number;
  items_per_page: number;
}
