import { Product, TextSearchRequest, ImageSearchResponse, DetectedItem } from "@/types/product";

// Type declaration for process.env
declare const process: {
  env: {
    [key: string]: string | undefined;
  };
};

// Helper to safely access environment variables
function getEnv(key: string, defaultValue: string): string {
  if (typeof window === "undefined") {
    // Server-side
    return process.env[key] || defaultValue;
  }
  // Client-side - Next.js injects NEXT_PUBLIC_ vars at build time
  return process.env[key] || defaultValue;
}

const API_URL = getEnv("NEXT_PUBLIC_API_URL", "http://localhost:8000");
const API_BASE_PATH = getEnv("NEXT_PUBLIC_API_BASE_PATH", "/api/v1");

const BASE_URL = `${API_URL}${API_BASE_PATH}`;

// Transform API response to Product format
function transformProduct(item: any): Product {
  // Handle both nested (product_info) and direct structure
  const productInfo = item.product_info || item;
  
  return {
    id: item.product_id || item.id || "",
    name: productInfo.name || item.name || "",
    description: productInfo.description || item.description,
    image_url: productInfo.image_url || item.image_url,
    price: productInfo.price !== undefined ? productInfo.price : (item.price !== undefined ? item.price : undefined),
    currency: productInfo.currency || item.currency || "USD",
    category: productInfo.category || item.category,
    brand: productInfo.brand || item.brand,
    colors: productInfo.colors || item.colors || [],
    style_tags: productInfo.style_tags || item.style_tags || [],
    metadata: {
      similarity_score: item.similarity_score,
      key_similarities: item.key_similarities || productInfo.key_similarities,
    },
  };
}

// Health check
export async function checkHealth(): Promise<{ status: string; timestamp: string }> {
  const response = await fetch(`${BASE_URL}/health`);
  if (!response.ok) {
    throw new Error("Health check failed");
  }
  return response.json();
}

// Get all products
export async function getProducts(limit?: number, offset?: number): Promise<Product[]> {
  const params = new URLSearchParams();
  if (limit) params.append("limit", limit.toString());
  if (offset) params.append("offset", offset.toString());
  
  const queryString = params.toString();
  const url = `${BASE_URL}/products${queryString ? `?${queryString}` : ""}`;
  
  const response = await fetch(url, {
    method: "GET",
  });

  if (!response.ok) {
    // If /products doesn't exist, try /product
    if (response.status === 404) {
      const altUrl = `${BASE_URL}/product${queryString ? `?${queryString}` : ""}`;
      const altResponse = await fetch(altUrl, { method: "GET" });
      if (altResponse.ok) {
        const data = await altResponse.json();
        if (Array.isArray(data)) {
          return data.map(transformProduct);
        }
        if (data.results && Array.isArray(data.results)) {
          return data.results.map(transformProduct);
        }
        return [];
      }
    }
    const error = await response.text();
    throw new Error(`Failed to get products: ${error}`);
  }

  const data = await response.json();
  
  // Handle response with products array
  if (data.products && Array.isArray(data.products)) {
    return data.products.map(transformProduct);
  }
  
  // Handle direct array response
  if (Array.isArray(data)) {
    return data.map(transformProduct);
  }
  
  // Handle results array
  if (data.results && Array.isArray(data.results)) {
    return data.results.map(transformProduct);
  }

  return [];
}

// Get product by ID
export async function getProductById(id: string): Promise<Product | null> {
  const response = await fetch(`${BASE_URL}/product/${id}`, {
    method: "GET",
  });

  if (!response.ok) {
    if (response.status === 404) {
      return null;
    }
    const error = await response.text();
    throw new Error(`Failed to get product: ${error}`);
  }

  const data = await response.json();
  return transformProduct(data);
}

// Text search
export async function searchText(request: TextSearchRequest): Promise<Product[]> {
  const response = await fetch(`${BASE_URL}/search/text`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      query: request.query,
      limit: request.limit || 20,
    }),
  });

  if (!response.ok) {
    const error = await response.text();
    throw new Error(`Text search failed: ${error}`);
  }

  const data = await response.json();
  
  // Transform nested response structure
  if (data.results && Array.isArray(data.results)) {
    return data.results.map(transformProduct);
  }
  
  // Fallback if response is already an array
  if (Array.isArray(data)) {
    return data.map(transformProduct);
  }

  return [];
}

// Image similarity search
export async function searchSimilarImage(
  file: File,
  limit: number = 10
): Promise<Product[]> {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(`${BASE_URL}/search/similar?limit=${limit}`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    const error = await response.text();
    throw new Error(`Image search failed: ${error}`);
  }

  const data = await response.json();
  
  // Handle nested structure: data.results[].similar_products[]
  if (data.results && Array.isArray(data.results)) {
    const allProducts: Product[] = [];
    for (const result of data.results) {
      if (result.similar_products && Array.isArray(result.similar_products)) {
        allProducts.push(...result.similar_products.map(transformProduct));
      }
    }
    return allProducts;
  }
  
  // Fallback: direct similar_products array
  if (data.similar_products && Array.isArray(data.similar_products)) {
    return data.similar_products.map(transformProduct);
  }

  return [];
}

// Detect items in image
export async function detectItems(file: File): Promise<DetectedItem[]> {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(`${BASE_URL}/detect`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    const error = await response.text();
    throw new Error(`Detection failed: ${error}`);
  }

  return response.json();
}

// Get outfit recommendations
export async function getOutfitRecommendations(
  occasion: string = "casual"
): Promise<any> {
  const response = await fetch(`${BASE_URL}/outfit/recommend?occasion=${occasion}`, {
    method: "POST",
  });

  if (!response.ok) {
    const error = await response.text();
    throw new Error(`Outfit recommendation failed: ${error}`);
  }

  return response.json();
}

// Compatibility analysis
export async function analyzeCompatibility(items: Product[]): Promise<any> {
  const response = await fetch(`${BASE_URL}/compatibility/analyze`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(items),
  });

  if (!response.ok) {
    const error = await response.text();
    throw new Error(`Compatibility analysis failed: ${error}`);
  }

  return response.json();
}

// Color harmony
export async function checkColorHarmony(colors: string[]): Promise<any> {
  const response = await fetch(`${BASE_URL}/color/harmony`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ colors }),
  });

  if (!response.ok) {
    const error = await response.text();
    throw new Error(`Color harmony check failed: ${error}`);
  }

  return response.json();
}

// Instagram/Pinterest scraping types
export interface ScrapeRequest {
  url: string;
  post_limit?: number;
  use_api?: boolean;
}

export interface BatchScrapeRequest {
  urls: string[];
  post_limit?: number;
  use_api?: boolean;
}

export interface ScrapedPost {
  source: string;
  structured_data?: any;
  raw_data?: any;
  scraped_date: string;
  extraction_method: string;
}

export interface ScrapeResponse {
  success: boolean;
  message: string;
  total_posts: number;
  posts: ScrapedPost[];
  url: string;
  platform: string;
  scraped_at: string;
  estimated_cost?: number;
}

export interface BatchScrapeResponse {
  success: boolean;
  message: string;
  total_posts: number;
  posts: ScrapedPost[];
  urls_processed: number;
  urls_failed: number;
  errors: Array<{ url: string; error: string }>;
  scraped_at: string;
  total_cost?: number;
}

// Scrape single URL (Instagram or Pinterest)
export async function scrapeSocialMedia(
  request: ScrapeRequest,
  saveToDb: boolean = false
): Promise<ScrapeResponse> {
  const response = await fetch(`${BASE_URL}/scrape?save_to_db=${saveToDb}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      url: request.url,
      post_limit: request.post_limit || 50,
      use_api: request.use_api !== false,
    }),
  });

  if (!response.ok) {
    const error = await response.text();
    throw new Error(`Scraping failed: ${error}`);
  }

  return response.json();
}

// Batch scrape multiple URLs
export async function batchScrapeSocialMedia(
  request: BatchScrapeRequest,
  saveToDb: boolean = false
): Promise<BatchScrapeResponse> {
  const response = await fetch(`${BASE_URL}/scrape/batch?save_to_db=${saveToDb}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      urls: request.urls,
      post_limit: request.post_limit || 50,
      use_api: request.use_api !== false,
    }),
  });

  if (!response.ok) {
    const error = await response.text();
    throw new Error(`Batch scraping failed: ${error}`);
  }

  return response.json();
}

// Proxy image URL through backend to bypass CORS
// Uses the same endpoint as PostsGallery for consistency
export function getProxiedImageUrl(imageUrl: string): string {
  if (!imageUrl) return imageUrl;
  // If it's already a relative URL or data URL, return as-is
  if (imageUrl.startsWith('/') || imageUrl.startsWith('data:')) {
    return imageUrl;
  }
  // Use the same endpoint pattern as PostsGallery: /products/image-proxy
  // BASE_URL is already /api/v1, so this becomes /api/v1/products/image-proxy
  return `${BASE_URL}/products/image-proxy?url=${encodeURIComponent(imageUrl)}`;
}

// Get saved scraped posts
// Backend can return either flat structure (from DB) or nested structure (from file storage)
export interface SavedPost {
  id: string;
  platform?: string;
  source_url?: string;
  scraped_at?: string;
  scraped_date?: string;
  post_data?: ScrapedPost;
  // Flat structure fields (from database)
  display_url?: string;
  images?: string[];
  caption?: string;
  owner_username?: string;
  owner_full_name?: string;
  likes_count?: number;
  comments_count?: number;
  url?: string;
  short_code?: string;
  hashtags?: string[];
  raw_data?: any;
}

export interface SavedPostsResponse {
  success: boolean;
  posts: SavedPost[];
  total: number;
  limit: number;
  offset: number;
}

export async function getSavedPosts(
  limit: number = 20,
  offset: number = 0,
  platform?: string
): Promise<SavedPostsResponse> {
  const params = new URLSearchParams({
    limit: limit.toString(),
    offset: offset.toString(),
  });
  
  if (platform) {
    params.append('platform', platform);
  }

  const response = await fetch(`${BASE_URL}/scraped-posts?${params.toString()}`);

  if (!response.ok) {
    const error = await response.text();
    throw new Error(`Failed to fetch saved posts: ${error}`);
  }

  return response.json();
}

// Extracted Items Types
export interface ExtractedItem {
  id: string;
  instagram_post_id: string;
  category: string;
  subcategory?: string;
  colors?: string[];
  style_tags?: string[];
  pattern?: string;
  material?: string;
  brand?: string;
  item_name?: string;
  keywords?: string[];
  detection_confidence?: number;
  extraction_confidence?: number;
  best_match_product_id?: string;
  best_match_score?: number;
  extraction_method?: string;
  extraction_date: string;
}

export interface ProductInfo {
  product_id: string;
  name: string;
  brand?: string;
  price: number;
  currency: string;
  image_url?: string;
  in_stock: boolean;
}

export interface SimilarProduct {
  product_id: string;
  similarity_score: number;
  product_info: ProductInfo;
  match_reasoning: string;
  key_similarities: string[];
}

export interface ExtractedItemsResponse {
  success: boolean;
  message: string;
  post_id: string;
  items: ExtractedItem[];
  total: number;
}

export interface ExtractedItemWithMatchesResponse {
  success: boolean;
  message: string;
  item: ExtractedItem;
  matched_products?: SimilarProduct[];
}

// Get extracted items for a post
export async function getExtractedItemsForPost(postId: string): Promise<ExtractedItemsResponse> {
  const response = await fetch(`${BASE_URL}/extracted-items/post/${postId}`);

  if (!response.ok) {
    const error = await response.text();
    throw new Error(`Failed to fetch extracted items: ${error}`);
  }

  return response.json();
}

// Get extracted item with similar products
export async function getExtractedItemWithMatches(itemId: string): Promise<ExtractedItemWithMatchesResponse> {
  const response = await fetch(`${BASE_URL}/extracted-items/${itemId}?include_matches=true`);

  if (!response.ok) {
    const error = await response.text();
    throw new Error(`Failed to fetch extracted item: ${error}`);
  }

  return response.json();
}

// Delete Instagram post
export async function deletePost(postId: string, deleteExtractedItems: boolean = true): Promise<{ success: boolean; message: string }> {
  const response = await fetch(`${BASE_URL}/posts/${postId}?delete_extracted_items=${deleteExtractedItems}`, {
    method: 'DELETE',
  });

  if (!response.ok) {
    const error = await response.text();
    throw new Error(`Failed to delete post: ${error}`);
  }

  return response.json();
}

