"use client";

import Link from "next/link";
import { useTheme } from "next-themes";
import { Moon, Sun, Search, Home, ShoppingCart, Instagram, FileText } from "lucide-react";
import { useEffect, useState } from "react";
import { useCart } from "@/contexts/cart-context";

export function Navigation() {
  const { theme, setTheme } = useTheme();
  const [mounted, setMounted] = useState(false);
  const { cart, getItemCount } = useCart();
  const cartCount = getItemCount();

  useEffect(() => {
    setMounted(true);
  }, []);

  return (
    <nav className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="container mx-auto flex h-16 items-center justify-between px-4">
        <Link href="/" className="flex items-center space-x-2">
          <span className="text-xl font-bold">Fashion-AI Search</span>
        </Link>

        <div className="flex items-center space-x-4">
          <Link
            href="/"
            className="flex items-center space-x-1 text-sm font-medium transition-colors hover:text-primary"
          >
            <Home className="h-4 w-4" />
            <span>Explore</span>
          </Link>
          <Link
            href="/search"
            className="flex items-center space-x-1 text-sm font-medium transition-colors hover:text-primary"
          >
            <Search className="h-4 w-4" />
            <span>Search</span>
          </Link>
          <Link
            href="/scrape"
            className="flex items-center space-x-1 text-sm font-medium transition-colors hover:text-primary"
          >
            <Instagram className="h-4 w-4" />
            <span>Scrape</span>
          </Link>
          <Link
            href="/posts"
            className="flex items-center space-x-1 text-sm font-medium transition-colors hover:text-primary"
          >
            <FileText className="h-4 w-4" />
            <span>Posts</span>
          </Link>

          <Link
            href="/cart"
            className="relative flex items-center space-x-1 text-sm font-medium transition-colors hover:text-primary"
          >
            <ShoppingCart className="h-5 w-5" />
            {cartCount > 0 && (
              <span className="absolute -right-2 -top-2 flex min-w-[1.25rem] items-center justify-center rounded-full bg-primary px-1.5 py-0.5 text-xs font-bold text-primary-foreground">
                {cartCount > 99 ? "99+" : cartCount}
              </span>
            )}
            <span className="hidden sm:inline">Cart</span>
          </Link>

          {mounted && (
            <button
              onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
              className="rounded-md p-2 hover:bg-accent"
              aria-label="Toggle theme"
            >
              {theme === "dark" ? (
                <Sun className="h-5 w-5" />
              ) : (
                <Moon className="h-5 w-5" />
              )}
            </button>
          )}
        </div>
      </div>
    </nav>
  );
}

