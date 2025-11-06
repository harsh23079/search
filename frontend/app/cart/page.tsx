"use client";

import { useCart } from "@/contexts/cart-context";
import { formatPrice } from "@/lib/currency";
import { Minus, Plus, Trash2, ShoppingCart } from "lucide-react";
import Link from "next/link";

export default function CartPage() {
  const { cart, removeFromCart, updateCartItemQuantity, clearCart, getTotal, isLoading } =
    useCart();

  if (isLoading) {
    return (
      <div className="flex min-h-[400px] items-center justify-center">
        <p className="text-muted-foreground">Loading cart...</p>
      </div>
    );
  }

  if (cart.length === 0) {
    return (
      <div className="flex min-h-[400px] flex-col items-center justify-center space-y-4">
        <ShoppingCart className="h-16 w-16 text-muted-foreground" />
        <div className="text-center">
          <h2 className="text-2xl font-bold">Your cart is empty</h2>
          <p className="mt-2 text-muted-foreground">Add some products to get started!</p>
        </div>
        <Link
          href="/"
          className="rounded-lg bg-primary px-6 py-2 text-primary-foreground transition-colors hover:bg-primary/90"
        >
          Continue Shopping
        </Link>
      </div>
    );
  }

  const total = getTotal();
  const firstItemCurrency = cart[0]?.product.currency || "USD";

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold">Shopping Cart</h1>
        <button
          onClick={clearCart}
          className="text-sm text-destructive hover:underline"
        >
          Clear Cart
        </button>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        {/* Cart Items */}
        <div className="lg:col-span-2 space-y-4">
          {cart.map((item) => (
            <div
              key={item.product.id}
              className="flex gap-4 rounded-lg border bg-card p-4"
            >
              <Link href={`/product/${item.product.id}`} className="shrink-0">
                <div className="h-24 w-24 overflow-hidden rounded-lg border bg-muted">
                  {item.product.image_url ? (
                    <img
                      src={item.product.image_url}
                      alt={item.product.name}
                      className="h-full w-full object-cover"
                    />
                  ) : (
                    <div className="flex h-full items-center justify-center text-xs text-muted-foreground">
                      No Image
                    </div>
                  )}
                </div>
              </Link>

              <div className="flex flex-1 flex-col justify-between">
                <div>
                  <Link
                    href={`/product/${item.product.id}`}
                    className="font-semibold hover:underline"
                  >
                    {item.product.name}
                  </Link>
                  {item.product.category && (
                    <p className="mt-1 text-sm text-muted-foreground">
                      {item.product.category}
                    </p>
                  )}
                </div>

                <div className="mt-2 flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => updateCartItemQuantity(item.product.id, item.quantity - 1)}
                      className="rounded border p-1 hover:bg-accent"
                      aria-label="Decrease quantity"
                    >
                      <Minus className="h-4 w-4" />
                    </button>
                    <span className="w-8 text-center text-sm font-medium">
                      {item.quantity}
                    </span>
                    <button
                      onClick={() => updateCartItemQuantity(item.product.id, item.quantity + 1)}
                      className="rounded border p-1 hover:bg-accent"
                      aria-label="Increase quantity"
                    >
                      <Plus className="h-4 w-4" />
                    </button>
                  </div>

                  <div className="flex items-center gap-4">
                    <span className="font-bold">
                      {formatPrice(
                        (item.product.price || 0) * item.quantity,
                        item.product.currency
                      )}
                    </span>
                    <button
                      onClick={() => removeFromCart(item.product.id)}
                      className="text-destructive hover:text-destructive/80"
                      aria-label="Remove item"
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Order Summary */}
        <div className="lg:col-span-1">
          <div className="sticky top-24 rounded-lg border bg-card p-6 space-y-4">
            <h2 className="text-xl font-semibold">Order Summary</h2>

            <div className="space-y-2 border-t pt-4">
              <div className="flex justify-between text-sm">
                <span className="text-muted-foreground">Items</span>
                <span>{cart.length}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-muted-foreground">Total Quantity</span>
                <span>{cart.reduce((sum, item) => sum + item.quantity, 0)}</span>
              </div>
            </div>

            <div className="border-t pt-4">
              <div className="flex justify-between text-lg font-bold">
                <span>Total</span>
                <span>{formatPrice(total, firstItemCurrency)}</span>
              </div>
            </div>

            <button className="w-full rounded-lg bg-primary px-6 py-3 font-medium text-primary-foreground transition-colors hover:bg-primary/90">
              Proceed to Checkout
            </button>

            <Link
              href="/"
              className="block w-full text-center text-sm text-muted-foreground hover:text-foreground"
            >
              Continue Shopping
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}

