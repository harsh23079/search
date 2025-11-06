"use client";

import Link from "next/link";
import { Product } from "@/types/product";
import { formatPrice } from "@/lib/currency";
import { useCart } from "@/contexts/cart-context";
import { ShoppingCart, Plus, Minus } from "lucide-react";
import { useState } from "react";

interface ProductCardProps {
  product: Product;
}

export function ProductCard({ product }: ProductCardProps) {
  const { addToCart, isInCart, getItemQuantity, updateCartItemQuantity } = useCart();
  const [isAdding, setIsAdding] = useState(false);
  const inCart = isInCart(product.id);
  const quantity = getItemQuantity(product.id);

  const handleAddToCart = (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsAdding(true);
    addToCart(product, 1);
    setTimeout(() => setIsAdding(false), 500);
  };

  const handleIncrease = (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    updateCartItemQuantity(product.id, quantity + 1);
  };

  const handleDecrease = (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (quantity > 1) {
      updateCartItemQuantity(product.id, quantity - 1);
    } else {
      // Remove from cart if quantity becomes 0
      updateCartItemQuantity(product.id, 0);
    }
  };

  return (
    <Link href={`/product/${product.id}`}>
      <div className="group relative overflow-hidden rounded-lg border bg-card transition-all hover:shadow-lg">
        <div className="aspect-square w-full overflow-hidden bg-muted">
          {product.image_url ? (
            <img
              src={product.image_url}
              alt={product.name}
              className="h-full w-full object-cover transition-transform group-hover:scale-105"
              loading="lazy"
            />
          ) : (
            <div className="flex h-full items-center justify-center text-muted-foreground">
              No Image
            </div>
          )}
        </div>
        <div className="p-4">
          <h3 className="font-semibold line-clamp-2">{product.name}</h3>
          {product.description && (
            <p className="mt-1 text-sm text-muted-foreground line-clamp-2">
              {product.description}
            </p>
          )}
          <div className="mt-2 flex items-center justify-between">
            {product.price !== undefined && (
              <span className="font-bold">{formatPrice(product.price, product.currency)}</span>
            )}
            {product.metadata?.similarity_score !== undefined && (
              <span className="text-xs text-muted-foreground">
                {(product.metadata.similarity_score * 100).toFixed(0)}% match
              </span>
            )}
          </div>
          <div className="mt-3 flex items-center justify-between gap-2">
            {product.category && (
              <span className="inline-block rounded-full bg-secondary px-2 py-1 text-xs">
                {product.category}
              </span>
            )}
            {inCart ? (
              <div className="ml-auto flex items-center gap-2 rounded-lg border bg-background px-2 py-1">
                <button
                  onClick={handleDecrease}
                  className="flex h-6 w-6 items-center justify-center rounded hover:bg-accent"
                  title="Decrease quantity"
                >
                  <Minus className="h-3 w-3" />
                </button>
                <span className="min-w-[1.5rem] text-center text-xs font-semibold">
                  {quantity}
                </span>
                <button
                  onClick={handleIncrease}
                  className="flex h-6 w-6 items-center justify-center rounded hover:bg-accent"
                  title="Increase quantity"
                >
                  <Plus className="h-3 w-3" />
                </button>
              </div>
            ) : (
              <button
                onClick={handleAddToCart}
                className="ml-auto flex items-center gap-1 rounded-lg bg-primary px-3 py-1.5 text-xs font-medium text-primary-foreground transition-colors hover:bg-primary/90"
                title="Add to cart"
              >
                <ShoppingCart className="h-3 w-3" />
                <span>{isAdding ? "Added!" : "Add"}</span>
              </button>
            )}
          </div>
        </div>
      </div>
    </Link>
  );
}

