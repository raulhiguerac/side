export interface PageRange {
  from: number;
  to: number;
}

export interface FetchPageResult<T> {
  items: T[];
  hasMore: boolean;
}
