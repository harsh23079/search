"use client";

import { useState, useEffect, useRef, useCallback, useMemo } from "react";
import { Product } from "@/types/product";
import { ProductCard } from "./product-card";
import { ProductFilters, FilterState } from "./product-filters";
import { getProducts } from "@/lib/api";
import { Loader2 } from "lucide-react";

const ITEMS_PER_PAGE = 20;

export function ExploreFeed() {
  const [allProducts, setAllProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [offset, setOffset] = useState(0);
  const [hasMore, setHasMore] = useState(true);
  const [filters, setFilters] = useState<FilterState>({
    categories: [],
    brands: [],
    colors: [],
    styleTags: [],
    minPrice: null,
    maxPrice: null,
  });
  const observerTarget = useRef<HTMLDivElement>(null);

  const loadProducts = useCallback(async (currentOffset: number, append: boolean = false) => {
    try {
      if (append) {
        setLoadingMore(true);
      } else {
        setLoading(true);
      }
      setError(null);
      
      const results = await getProducts(ITEMS_PER_PAGE, currentOffset);
      
      if (append) {
        setAllProducts((prev) => [...prev, ...results]);
      } else {
        setAllProducts(results);
      }
      
      // If we got fewer items than requested, we've reached the end
      if (results.length < ITEMS_PER_PAGE) {
        setHasMore(false);
      } else {
        setHasMore(true);
      }
      
      setOffset(currentOffset + results.length);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load products");
    } finally {
      setLoading(false);
      setLoadingMore(false);
    }
  }, []);

  // Initial load
  useEffect(() => {
    loadProducts(0, false);
  }, [loadProducts]);

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

  // Intersection Observer for infinite scroll
  useEffect(() => {
    // Don't enable infinite scroll if filters are active
    if (hasActiveFilters) {
      return;
    }

    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting && hasMore && !loadingMore && !loading) {
          loadProducts(offset, true);
        }
      },
      { threshold: 0.1 }
    );

    const currentTarget = observerTarget.current;
    if (currentTarget) {
      observer.observe(currentTarget);
    }

    return () => {
      if (currentTarget) {
        observer.unobserve(currentTarget);
      }
    };
  }, [offset, hasMore, loadingMore, loading, loadProducts, hasActiveFilters]);

  // Get unique values from all products
  const availableCategories = useMemo(() => {
    const categories = new Set<string>();
    allProducts.forEach((product) => {
      if (product.category) {
        categories.add(product.category);
      }
    });
    return Array.from(categories).sort();
  }, [allProducts]);

  const availableBrands = useMemo(() => {
    const brands = new Set<string>();
    allProducts.forEach((product) => {
      if (product.brand) {
        brands.add(product.brand);
      }
    });
    return Array.from(brands).sort();
  }, [allProducts]);

  const availableColors = useMemo(() => {
    const colors = new Set<string>();
    allProducts.forEach((product) => {
      if (product.colors && Array.isArray(product.colors)) {
        product.colors.forEach((color) => colors.add(color));
      }
    });
    return Array.from(colors).sort();
  }, [allProducts]);

  const availableStyleTags = useMemo(() => {
    const tags = new Set<string>();
    allProducts.forEach((product) => {
      if (product.style_tags && Array.isArray(product.style_tags)) {
        product.style_tags.forEach((tag) => tags.add(tag));
      }
    });
    return Array.from(tags).sort();
  }, [allProducts]);

  // Get max price from all products
  const maxPriceValue = useMemo(() => {
    return Math.max(...allProducts.map((p) => p.price || 0), 0);
  }, [allProducts]);

  // Filter products based on active filters
  const filteredProducts = useMemo(() => {
    return allProducts.filter((product) => {
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
  }, [allProducts, filters]);

  if (loading) {
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
    <div className="flex gap-6">
      {/* Filter Sidebar */}
      <aside className="hidden lg:block w-64 shrink-0 self-start">
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
      <div className="flex-1 space-y-4">
        {/* Mobile Filters */}
        <div className="lg:hidden">
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
        <div className="rounded-lg border border-destructive/50 bg-destructive/10 p-3 text-sm text-destructive">
          Error loading more products: {error}
        </div>
      )}

        {/* Results count */}
        {filteredProducts.length > 0 && (
          <div className="flex items-center justify-between">
            <p className="text-sm text-muted-foreground">
              {hasActiveFilters ? (
                <>
                  Showing <span className="font-semibold text-foreground">{filteredProducts.length}</span> of{" "}
                  <span className="font-semibold text-foreground">{allProducts.length}</span> loaded products
                  <span className="ml-2 text-xs">(filtered from {allProducts.length} total)</span>
                </>
              ) : (
                <>
                  Showing <span className="font-semibold text-foreground">{filteredProducts.length}</span> products
                </>
              )}
            </p>
            {hasActiveFilters && (
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

        {filteredProducts.length === 0 && !loading ? (
          <div className="flex min-h-[400px] items-center justify-center">
            <p className="text-muted-foreground">
              {allProducts.length === 0
                ? "No products found"
                : "No products match your filters"}
            </p>
          </div>
        ) : (
          <>
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
              {filteredProducts.map((product) => (
                <ProductCard key={product.id} product={product} />
              ))}
            </div>

            {/* Loading indicator and sentinel for infinite scroll */}
            <div ref={observerTarget} className="flex justify-center py-8">
              {loadingMore && (
                <div className="flex items-center gap-2">
                  <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
                  <span className="text-sm text-muted-foreground">Loading more products...</span>
                </div>
              )}
              {!hasMore && allProducts.length > 0 && !hasActiveFilters && (
                <p className="text-sm text-muted-foreground">
                  You've reached the end! No more products to load.
                </p>
              )}
              {hasActiveFilters && (
                <p className="text-sm text-muted-foreground">
                  Clear filters to load more products
                </p>
              )}
            </div>
          </>
        )}
      </div>
    </div>
  );
}

