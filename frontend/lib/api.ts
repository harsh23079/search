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

