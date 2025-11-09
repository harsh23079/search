"use client";

import { useState, useEffect, useCallback, useMemo } from "react";
import { Product } from "@/types/product";
import { ProductCard } from "./product-card";
import { ProductFilters, FilterState } from "./product-filters";
import { getAllProducts, searchText } from "@/lib/api";
import { Loader2 } from "lucide-react";


interface ExploreFeedProps {
  searchQuery?: string;
}

export function ExploreFeed({ searchQuery = "" }: ExploreFeedProps) {
  const [allProducts, setAllProducts] = useState<Product[]>([]);
  const [searchResults, setSearchResults] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);
  const [searching, setSearching] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [filters, setFilters] = useState<FilterState>({
    categories: [],
    brands: [],
    colors: [],
    styleTags: [],
    minPrice: null,
    maxPrice: null,
  });

  const loadProducts = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      
      const results = await getAllProducts();
      
      setAllProducts(results);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load products");
    } finally {
      setLoading(false);
    }
  }, []);

  // Initial load
  useEffect(() => {
    loadProducts();
  }, [loadProducts]);

  // Text search when searchQuery changes
  useEffect(() => {
    const performSearch = async () => {
      const query = searchQuery.trim();
      
      if (!query) {
        setSearchResults([]);
        setSearching(false);
        return;
      }

      setSearching(true);
      setError(null);
      
      try {
        const results = await searchText({ query, limit: 100 });
        setSearchResults(results);
      } catch (err) {
        console.error("Search error:", err);
        setError(err instanceof Error ? err.message : "Search failed");
        setSearchResults([]);
      } finally {
        setSearching(false);
      }
    };

    // Debounce search
    const timeoutId = setTimeout(performSearch, 300);
    return () => clearTimeout(timeoutId);
  }, [searchQuery]);

  // Check if any filters are active
  const hasActiveFilters = useMemo(() => {
    return (
      filters.categories.length > 0 ||
      filters.brands.length > 0 ||
      filters.colors.length > 0 ||
      filters.styleTags.length > 0 ||
      filters.minPrice !== null ||
      filters.maxPrice !== null
    );
  }, [filters]);

  // No infinite scroll needed since we load all products at once

  // Get unique values from products (use search results if searching, otherwise all products)
  const productsForFilters = useMemo(() => {
    return searchQuery.trim() ? searchResults : allProducts;
  }, [searchQuery, searchResults, allProducts]);

  const availableCategories = useMemo(() => {
    const categories = new Set<string>();
    productsForFilters.forEach((product) => {
      if (product.category) {
        categories.add(product.category);
      }
    });
    return Array.from(categories).sort();
  }, [productsForFilters]);

  const availableBrands = useMemo(() => {
    const brands = new Set<string>();
    productsForFilters.forEach((product) => {
      if (product.brand) {
        brands.add(product.brand);
      }
    });
    return Array.from(brands).sort();
  }, [productsForFilters]);

  const availableColors = useMemo(() => {
    const colors = new Set<string>();
    productsForFilters.forEach((product) => {
      if (product.colors && Array.isArray(product.colors)) {
        product.colors.forEach((color) => colors.add(color));
      }
    });
    return Array.from(colors).sort();
  }, [productsForFilters]);

  const availableStyleTags = useMemo(() => {
    const tags = new Set<string>();
    productsForFilters.forEach((product) => {
      if (product.style_tags && Array.isArray(product.style_tags)) {
        product.style_tags.forEach((tag) => tags.add(tag));
      }
    });
    return Array.from(tags).sort();
  }, [productsForFilters]);

  // Get max price from products
  const maxPriceValue = useMemo(() => {
    return Math.max(...productsForFilters.map((p) => p.price || 0), 0);
  }, [productsForFilters]);

  // Filter products based on active filters
  // Use search results if searchQuery exists, otherwise use allProducts
  const filteredProducts = useMemo(() => {
    const productsToFilter = searchQuery.trim() ? searchResults : allProducts;
    
    return productsToFilter.filter((product) => {
      // Category filter
      if (
        filters.categories.length > 0 &&
        !filters.categories.includes(product.category || "")
      ) {
        return false;
      }

      // Brand filter
      if (filters.brands.length > 0 && !filters.brands.includes(product.brand || "")) {
        return false;
      }

      // Color filter
      if (filters.colors.length > 0) {
        const productColors = product.colors || [];
        const hasMatchingColor = filters.colors.some((color) =>
          productColors.some((pc) => pc.toLowerCase() === color.toLowerCase())
        );
        if (!hasMatchingColor) {
          return false;
        }
      }

      // Style tag filter
      if (filters.styleTags.length > 0) {
        const productTags = product.style_tags || [];
        const hasMatchingTag = filters.styleTags.some((tag) =>
          productTags.some((pt) => pt.toLowerCase() === tag.toLowerCase())
        );
        if (!hasMatchingTag) {
          return false;
        }
      }

      // Price filter
      if (product.price !== undefined) {
        if (filters.minPrice !== null && product.price < filters.minPrice) {
          return false;
        }
        if (filters.maxPrice !== null && product.price > filters.maxPrice) {
          return false;
        }
      }

      return true;
    });
  }, [allProducts, searchResults, filters, searchQuery]);

  if (loading && !searchQuery.trim()) {
    return (
      <div className="flex min-h-[400px] items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (error && allProducts.length === 0) {
    return (
      <div className="flex min-h-[400px] items-center justify-center">
        <div className="text-center">
          <p className="text-destructive">Error: {error}</p>
          <p className="mt-2 text-sm text-muted-foreground">
            Make sure your backend is running on http://localhost:8000
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-full gap-6">
      {/* Filter Sidebar */}
      <aside className="hidden lg:block w-64 shrink-0 h-full overflow-y-auto">
        <ProductFilters
          filters={filters}
          onFiltersChange={setFilters}
          availableCategories={availableCategories}
          availableBrands={availableBrands}
          availableColors={availableColors}
          availableStyleTags={availableStyleTags}
          maxPriceValue={maxPriceValue}
        />
      </aside>

      {/* Main Content */}
      <div className="flex-1 flex flex-col min-w-0 h-full">
        {/* Mobile Filters */}
        <div className="lg:hidden shrink-0 mb-4">
          <ProductFilters
            filters={filters}
            onFiltersChange={setFilters}
            availableCategories={availableCategories}
            availableBrands={availableBrands}
            availableColors={availableColors}
            availableStyleTags={availableStyleTags}
            maxPriceValue={maxPriceValue}
          />
        </div>

        {error && allProducts.length > 0 && (
          <div className="rounded-lg border border-destructive/50 bg-destructive/10 p-3 text-sm text-destructive shrink-0 mb-4">
            Error loading more products: {error}
          </div>
        )}

        {/* Results count */}
        {(filteredProducts.length > 0 || searchQuery.trim() || hasActiveFilters || searching) && (
          <div className="flex items-center justify-between shrink-0 mb-4">
            <p className="text-sm text-muted-foreground">
              {searching ? (
                <span className="flex items-center gap-2">
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Searching...
                </span>
              ) : searchQuery.trim() || hasActiveFilters ? (
                <>
                  Showing <span className="font-semibold text-foreground">{filteredProducts.length}</span>{" "}
                  {searchQuery.trim() ? (
                    <>search result{filteredProducts.length !== 1 ? 's' : ''} for "{searchQuery}"</>
                  ) : (
                    <>of <span className="font-semibold text-foreground">{allProducts.length}</span> products</>
                  )}
                </>
              ) : (
                <>
                  Showing <span className="font-semibold text-foreground">{filteredProducts.length}</span> products
                </>
              )}
            </p>
            {(hasActiveFilters || searchQuery.trim()) && !searching && (
              <button
                onClick={() => {
                  setFilters({
                    categories: [],
                    brands: [],
                    colors: [],
                    styleTags: [],
                    minPrice: null,
                    maxPrice: null,
                  });
                }}
                className="text-xs text-primary hover:underline"
              >
                Clear filters
              </button>
            )}
          </div>
        )}

        {/* Scrollable Product Grid Container */}
        <div className="flex-1 overflow-y-auto min-h-0">
          {searching ? (
            <div className="flex min-h-[400px] items-center justify-center">
              <div className="text-center">
                <Loader2 className="h-8 w-8 animate-spin text-muted-foreground mx-auto mb-4" />
                <p className="text-muted-foreground">Searching products...</p>
              </div>
            </div>
          ) : filteredProducts.length === 0 && !loading ? (
            <div className="flex min-h-[400px] items-center justify-center">
              <p className="text-muted-foreground">
                {allProducts.length === 0
                  ? "No products found"
                  : searchQuery.trim()
                  ? `No products found matching "${searchQuery}"`
                  : "No products match your filters"}
              </p>
            </div>
          ) : (
            <>
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 pb-4">
                {filteredProducts.map((product) => (
                  <ProductCard key={product.id} product={product} />
                ))}
              </div>

              {/* All products loaded */}
              {hasActiveFilters && (
                <div className="flex justify-center py-4">
                  <p className="text-sm text-muted-foreground">
                    Showing filtered results from {allProducts.length} total products
                  </p>
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}

