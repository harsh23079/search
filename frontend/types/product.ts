export interface Product {
  id: string;
  name: string;
  description?: string;
  image_url?: string;
  price?: number;
  currency?: string;
  category?: string;
  brand?: string;
  colors?: string[];
  style_tags?: string[];
  metadata?: {
    similarity_score?: number;
    key_similarities?: string[];
  };
}

export type ProductCategory = "clothing" | "shoes" | "bags" | "accessories";

export interface TextSearchRequest {
  query: string;
  limit?: number;
}

export interface ImageSearchResponse {
  similar_products: Product[];
}

export interface DetectedItem {
  category: string;
  colors: string[];
  style_tags: string[];
}

