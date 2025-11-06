"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { Product } from "@/types/product";
import { getProductById } from "@/lib/api";
import { formatPrice } from "@/lib/currency";
import { useCart } from "@/contexts/cart-context";
import { Loader2, ArrowLeft, ShoppingCart } from "lucide-react";
import Link from "next/link";

export default function ProductDetailPage() {
  const params = useParams();
  const productId = params.id as string;
  const [product, setProduct] = useState<Product | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const { addToCart, isInCart } = useCart();
  const [isAdding, setIsAdding] = useState(false);

  useEffect(() => {
    // Load product by ID using GET /product/:id endpoint
    const loadProduct = async () => {
      try {
        setLoading(true);
        setError(null);
        const found = await getProductById(productId);
        if (found) {
          setProduct(found);
        } else {
          setError("Product not found");
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load product");
      } finally {
        setLoading(false);
      }
    };

    if (productId) {
      loadProduct();
    }
  }, [productId]);

  if (loading) {
    return (
      <div className="flex min-h-[400px] items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (error || !product) {
    return (
      <div className="flex min-h-[400px] flex-col items-center justify-center space-y-4">
        <p className="text-destructive">{error || "Product not found"}</p>
        <Link
          href="/"
          className="flex items-center gap-2 text-primary hover:underline"
        >
          <ArrowLeft className="h-4 w-4" />
          Back to Explore
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <Link
        href="/"
        className="inline-flex items-center gap-2 text-muted-foreground hover:text-foreground"
      >
        <ArrowLeft className="h-4 w-4" />
        Back to Explore
      </Link>

      <div className="grid gap-8 md:grid-cols-2">
        {/* Product Image */}
        <div className="relative aspect-square w-full overflow-hidden rounded-lg border bg-muted">
          {product.image_url ? (
            <img
              src={product.image_url}
              alt={product.name}
              className="h-full w-full object-cover"
              loading="lazy"
            />
          ) : (
            <div className="flex h-full items-center justify-center text-muted-foreground">
              No Image Available
            </div>
          )}
        </div>

        {/* Product Details */}
        <div className="space-y-6">
          <div>
            <h1 className="text-3xl font-bold">{product.name}</h1>
            {product.category && (
              <span className="mt-2 inline-block rounded-full bg-secondary px-3 py-1 text-sm">
                {product.category}
              </span>
            )}
          </div>

          {product.price !== undefined && (
            <div>
              <p className="text-3xl font-bold">{formatPrice(product.price, product.currency)}</p>
            </div>
          )}

          {product.description && (
            <div>
              <h2 className="mb-2 text-lg font-semibold">Description</h2>
              <p className="text-muted-foreground">{product.description}</p>
            </div>
          )}

          {product.metadata && (
            <div className="space-y-4 rounded-lg border p-4">
              {product.metadata.similarity_score !== undefined && (
                <div>
                  <h3 className="text-sm font-medium text-muted-foreground">
                    Similarity Score
                  </h3>
                  <p className="text-2xl font-bold">
                    {(product.metadata.similarity_score * 100).toFixed(1)}%
                  </p>
                </div>
              )}
              {product.metadata.key_similarities &&
                product.metadata.key_similarities.length > 0 && (
                  <div>
                    <h3 className="mb-2 text-sm font-medium text-muted-foreground">
                      Key Similarities
                    </h3>
                    <div className="flex flex-wrap gap-2">
                      {product.metadata.key_similarities.map((similarity, idx) => (
                        <span
                          key={idx}
                          className="rounded-full bg-accent px-3 py-1 text-xs"
                        >
                          {similarity}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
            </div>
          )}

          <div className="pt-4">
            {product && (
              <button
                onClick={() => {
                  setIsAdding(true);
                  addToCart(product, 1);
                  setTimeout(() => setIsAdding(false), 500);
                }}
                className={`w-full flex items-center justify-center gap-2 rounded-lg px-6 py-3 font-medium transition-colors ${
                  isInCart(product.id)
                    ? "bg-secondary text-secondary-foreground"
                    : "bg-primary text-primary-foreground hover:bg-primary/90"
                }`}
              >
                <ShoppingCart className="h-5 w-5" />
                <span>
                  {isInCart(product.id)
                    ? "Already in Cart"
                    : isAdding
                      ? "Added!"
                      : "Add to Cart"}
                </span>
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

