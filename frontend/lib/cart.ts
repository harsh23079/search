import { Product } from "@/types/product";

export interface CartItem {
  product: Product;
  quantity: number;
}

const CART_STORAGE_KEY = "fashion-ai-cart";

export function getCart(): CartItem[] {
  if (typeof window === "undefined") return [];
  
  try {
    const stored = localStorage.getItem(CART_STORAGE_KEY);
    return stored ? JSON.parse(stored) : [];
  } catch {
    return [];
  }
}

export function saveCart(cart: CartItem[]): void {
  if (typeof window === "undefined") return;
  
  try {
    localStorage.setItem(CART_STORAGE_KEY, JSON.stringify(cart));
  } catch (error) {
    console.error("Failed to save cart to localStorage:", error);
  }
}

export function addToCart(product: Product, quantity: number = 1): CartItem[] {
  const cart = getCart();
  const existingIndex = cart.findIndex((item) => item.product.id === product.id);
  
  if (existingIndex >= 0) {
    cart[existingIndex].quantity += quantity;
  } else {
    cart.push({ product, quantity });
  }
  
  saveCart(cart);
  return cart;
}

export function removeFromCart(productId: string): CartItem[] {
  const cart = getCart().filter((item) => item.product.id !== productId);
  saveCart(cart);
  return cart;
}

export function updateCartItemQuantity(productId: string, quantity: number): CartItem[] {
  const cart = getCart();
  const item = cart.find((item) => item.product.id === productId);
  
  if (item) {
    if (quantity <= 0) {
      return removeFromCart(productId);
    }
    item.quantity = quantity;
    saveCart(cart);
  }
  
  return cart;
}

export function clearCart(): void {
  if (typeof window === "undefined") return;
  localStorage.removeItem(CART_STORAGE_KEY);
}

export function getCartItemCount(): number {
  return getCart().reduce((total, item) => total + item.quantity, 0);
}

export function getCartTotal(): number {
  return getCart().reduce((total, item) => {
    const price = item.product.price || 0;
    return total + price * item.quantity;
  }, 0);
}

