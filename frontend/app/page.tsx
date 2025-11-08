"use client";

import { ExploreFeed } from "@/components/explore-feed";
import { useState } from "react";
import { Search, X } from "lucide-react";

export default function HomePage() {
  const [searchQuery, setSearchQuery] = useState("");

  return (
    <div className="flex h-full flex-col overflow-hidden">
      <div className="mb-6 shrink-0">
        <div className="flex flex-col md:flex-row md:items-start md:justify-between gap-4 mb-4">
          <div className="flex-1">
            <h1 className="text-3xl font-bold">Explore Feed</h1>
            <p className="mt-2 text-muted-foreground">
              Discover fashion items and find your perfect style
            </p>
          </div>
          <div className="flex-1 max-w-full md:max-w-md">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <input
                type="text"
                placeholder="Search products by name, brand, or description..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-10 pr-10 py-2 rounded-lg border border-input bg-background text-foreground placeholder:text-muted-foreground focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary transition-colors"
              />
              {searchQuery && (
                <button
                  onClick={() => setSearchQuery("")}
                  className="absolute right-3 top-1/2 transform -translate-y-1/2 text-muted-foreground hover:text-foreground"
                  aria-label="Clear search"
                >
                  <X className="h-4 w-4" />
                </button>
              )}
            </div>
          </div>
        </div>
      </div>
      <div className="flex-1 min-h-0 overflow-hidden">
        <ExploreFeed searchQuery={searchQuery} />
      </div>
    </div>
  );
}

