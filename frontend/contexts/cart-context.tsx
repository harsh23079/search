"use client";

import React, { createContext, useContext, useState, useEffect, useCallback } from "react";
import { Product } from "@/types/product";
import {
  getCart,
  addToCart as addItem,
  removeFromCart as removeItem,
  updateCartItemQuantity as updateQuantity,
  clearCart as clearAll,
  CartItem,
} from "@/lib/cart";

interface CartContextType {
  cart: CartItem[];
  isLoading: boolean;
  addToCart: (product: Product, quantity?: number) => void;
  removeFromCart: (productId: string) => void;
  updateCartItemQuantity: (productId: string, quantity: number) => void;
  clearCart: () => void;
  getItemCount: () => number;
  getTotal: () => number;
  isInCart: (productId: string) => boolean;
  getItemQuantity: (productId: string) => number;
}

const CartContext = createContext<CartContextType | undefined>(undefined);

export function CartProvider({ children }: { children: React.ReactNode }) {
  const [cart, setCart] = useState<CartItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  // Load cart from localStorage on mount
  useEffect(() => {
    setCart(getCart());
    setIsLoading(false);

    // Listen for storage events (for cross-tab sync)
    const handleStorageChange = (e: StorageEvent) => {
      if (e.key === "fashion-ai-cart") {
        setCart(getCart());
      }
    };

    window.addEventListener("storage", handleStorageChange);
    return () => window.removeEventListener("storage", handleStorageChange);
  }, []);

  const addToCart = useCallback((product: Product, quantity: number = 1) => {
    const updatedCart = addItem(product, quantity);
    setCart(updatedCart);
  }, []);

  const removeFromCart = useCallback((productId: string) => {
    const updatedCart = removeItem(productId);
    setCart(updatedCart);
  }, []);

  const updateCartItemQuantity = useCallback((productId: string, quantity: number) => {
    const updatedCart = updateQuantity(productId, quantity);
    setCart(updatedCart);
  }, []);

  const clearCart = useCallback(() => {
    clearAll();
    setCart([]);
  }, []);

  const getItemCount = useCallback(() => {
    return cart.reduce((total, item) => total + item.quantity, 0);
  }, [cart]);

  const getTotal = useCallback(() => {
    return cart.reduce((total, item) => {
      const price = item.product.price || 0;
      return total + price * item.quantity;
    }, 0);
  }, [cart]);

  const isInCart = useCallback((productId: string) => {
    return cart.some((item) => item.product.id === productId);
  }, [cart]);

  const getItemQuantity = useCallback((productId: string) => {
    const item = cart.find((item) => item.product.id === productId);
    return item ? item.quantity : 0;
  }, [cart]);

  return (
    <CartContext.Provider
      value={{
        cart,
        isLoading,
        addToCart,
        removeFromCart,
        updateCartItemQuantity,
        clearCart,
        getItemCount,
        getTotal,
        isInCart,
        getItemQuantity,
      }}
    >
      {children}
    </CartContext.Provider>
  );
}

export function useCart() {
  const context = useContext(CartContext);
  if (context === undefined) {
    throw new Error("useCart must be used within a CartProvider");
  }
  return context;
}

