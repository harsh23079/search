"use client";

import { useState } from "react";
import { X, Filter, ChevronDown, ChevronUp } from "lucide-react";

export interface FilterState {
  categories: string[];
  brands: string[];
  colors: string[];
  styleTags: string[];
  minPrice: number | null;
  maxPrice: number | null;
}

interface ProductFiltersProps {
  filters: FilterState;
  onFiltersChange: (filters: FilterState) => void;
  availableCategories: string[];
  availableBrands: string[];
  availableColors: string[];
  availableStyleTags: string[];
  maxPriceValue: number;
}

const PRICE_RANGES = [
  { label: "Under ₹1,000", min: 0, max: 1000 },
  { label: "₹1,000 - ₹5,000", min: 1000, max: 5000 },
  { label: "₹5,000 - ₹10,000", min: 5000, max: 10000 },
  { label: "₹10,000 - ₹25,000", min: 10000, max: 25000 },
  { label: "₹25,000 - ₹50,000", min: 25000, max: 50000 },
  { label: "Over ₹50,000", min: 50000, max: Infinity },
];

export function ProductFilters({
  filters,
  onFiltersChange,
  availableCategories,
  availableBrands,
  availableColors,
  availableStyleTags,
  maxPriceValue,
}: ProductFiltersProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [expandedSections, setExpandedSections] = useState<Record<string, boolean>>({
    category: true,
    brand: true,
    price: true,
    color: true,
    style: true,
  });

  const toggleSection = (section: string) => {
    setExpandedSections((prev) => ({ ...prev, [section]: !prev[section] }));
  };

  const handleCategoryToggle = (category: string) => {
    const newCategories = filters.categories.includes(category)
      ? filters.categories.filter((c) => c !== category)
      : [...filters.categories, category];
    onFiltersChange({ ...filters, categories: newCategories });
  };

  const handleBrandToggle = (brand: string) => {
    const newBrands = filters.brands.includes(brand)
      ? filters.brands.filter((b) => b !== brand)
      : [...filters.brands, brand];
    onFiltersChange({ ...filters, brands: newBrands });
  };

  const handleColorToggle = (color: string) => {
    const newColors = filters.colors.includes(color)
      ? filters.colors.filter((c) => c !== color)
      : [...filters.colors, color];
    onFiltersChange({ ...filters, colors: newColors });
  };

  const handleStyleTagToggle = (tag: string) => {
    const newTags = filters.styleTags.includes(tag)
      ? filters.styleTags.filter((t) => t !== tag)
      : [...filters.styleTags, tag];
    onFiltersChange({ ...filters, styleTags: newTags });
  };

  const handlePriceRangeSelect = (min: number, max: number) => {
    // Toggle: if clicking the same range, unselect it
    const currentMax = filters.maxPrice === null ? Infinity : filters.maxPrice;
    const isCurrentlySelected = filters.minPrice === min && currentMax === max;
    
    if (isCurrentlySelected) {
      // Unselect by clearing price filters
      onFiltersChange({
        ...filters,
        minPrice: null,
        maxPrice: null,
      });
    } else {
      // Select the new range
      onFiltersChange({
        ...filters,
        minPrice: min,
        maxPrice: max === Infinity ? null : max,
      });
    }
  };

  const handlePriceChange = (type: "min" | "max", value: string) => {
    const numValue = value === "" ? null : Number(value);
    onFiltersChange({
      ...filters,
      [type === "min" ? "minPrice" : "maxPrice"]: numValue,
    });
  };

  const clearFilters = () => {
    onFiltersChange({
      categories: [],
      brands: [],
      colors: [],
      styleTags: [],
      minPrice: null,
      maxPrice: null,
    });
  };

  const hasActiveFilters =
    filters.categories.length > 0 ||
    filters.brands.length > 0 ||
    filters.colors.length > 0 ||
    filters.styleTags.length > 0 ||
    filters.minPrice !== null ||
    filters.maxPrice !== null;

  const activeFilterCount =
    filters.categories.length +
    filters.brands.length +
    filters.colors.length +
    filters.styleTags.length +
    (filters.minPrice !== null ? 1 : 0) +
    (filters.maxPrice !== null ? 1 : 0);

  // Color mapping for visual display
  const colorMap: Record<string, string> = {
    black: "#000000",
    white: "#FFFFFF",
    red: "#FF0000",
    blue: "#0000FF",
    green: "#008000",
    yellow: "#FFFF00",
    orange: "#FFA500",
    pink: "#FFC0CB",
    purple: "#800080",
    brown: "#A52A2A",
    gray: "#808080",
    grey: "#808080",
    beige: "#F5F5DC",
    navy: "#000080",
    tan: "#D2B48C",
  };

  return (
    <>
      {/* Mobile Filter Toggle */}
      <div className="lg:hidden">
        <div className="flex items-center justify-between mb-4">
          <button
            onClick={() => setIsOpen(!isOpen)}
            className="flex items-center gap-2 rounded-lg border bg-background px-4 py-2 text-sm font-medium transition-colors hover:bg-accent"
          >
            <Filter className="h-4 w-4" />
            <span>Filters</span>
            {hasActiveFilters && (
              <span className="ml-1 rounded-full bg-primary px-2 py-0.5 text-xs text-primary-foreground">
                {activeFilterCount}
              </span>
            )}
          </button>
          {hasActiveFilters && (
            <button
              onClick={clearFilters}
              className="text-sm text-muted-foreground hover:text-foreground"
            >
              Clear all
            </button>
          )}
        </div>
      </div>

      {/* Filter Sidebar */}
      <div
        className={`${
          isOpen ? "block" : "hidden"
        } lg:block fixed lg:relative top-0 left-0 z-40 h-screen lg:max-h-[calc(100vh-8rem)] bg-background border-r lg:border rounded-lg lg:border-0 w-80 lg:w-full max-w-xs lg:max-w-none shadow-lg lg:shadow-none flex flex-col`}
      >
        <div className="lg:hidden flex items-center justify-between p-6 pb-4 shrink-0 border-b">
          <h2 className="text-lg font-semibold">Filters</h2>
          <button
            onClick={() => setIsOpen(false)}
            className="p-2 hover:bg-accent rounded-lg"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto overflow-x-hidden p-6 lg:p-4 space-y-6 min-h-0">
          {/* Categories */}
          <div>
            <button
              onClick={() => toggleSection("category")}
              className="flex w-full items-center justify-between py-2 text-sm font-semibold"
            >
              <span>Category {availableCategories.length > 0 && `(${availableCategories.length})`}</span>
              {expandedSections.category ? (
                <ChevronUp className="h-4 w-4" />
              ) : (
                <ChevronDown className="h-4 w-4" />
              )}
            </button>
            {expandedSections.category && (
              <div className="mt-2 space-y-2">
                {availableCategories.length > 0 ? (
                  availableCategories.map((category) => (
                    <label
                      key={category}
                      className="flex items-center gap-2 cursor-pointer hover:text-primary"
                    >
                      <input
                        type="checkbox"
                        checked={filters.categories.includes(category)}
                        onChange={() => handleCategoryToggle(category)}
                        className="h-4 w-4 rounded border-gray-300 text-primary focus:ring-primary"
                      />
                      <span className="text-sm capitalize">{category}</span>
                    </label>
                  ))
                ) : (
                  <p className="text-xs text-muted-foreground">No categories available</p>
                )}
              </div>
            )}
          </div>

          {/* Brands */}
          <div>
            <button
              onClick={() => toggleSection("brand")}
              className="flex w-full items-center justify-between py-2 text-sm font-semibold"
            >
              <span>Brand {availableBrands.length > 0 && `(${availableBrands.length})`}</span>
              {expandedSections.brand ? (
                <ChevronUp className="h-4 w-4" />
              ) : (
                <ChevronDown className="h-4 w-4" />
              )}
            </button>
            {expandedSections.brand && (
              <div className="mt-2 space-y-2 max-h-60 overflow-y-auto">
                {availableBrands.length > 0 ? (
                  availableBrands.map((brand) => (
                    <label
                      key={brand}
                      className="flex items-center gap-2 cursor-pointer hover:text-primary"
                    >
                      <input
                        type="checkbox"
                        checked={filters.brands.includes(brand)}
                        onChange={() => handleBrandToggle(brand)}
                        className="h-4 w-4 rounded border-gray-300 text-primary focus:ring-primary"
                      />
                      <span className="text-sm capitalize">{brand}</span>
                    </label>
                  ))
                ) : (
                  <p className="text-xs text-muted-foreground">No brands available</p>
                )}
              </div>
            )}
          </div>

          {/* Price Range */}
          <div>
            <button
              onClick={() => toggleSection("price")}
              className="flex w-full items-center justify-between py-2 text-sm font-semibold"
            >
              <span>Price</span>
              {expandedSections.price ? (
                <ChevronUp className="h-4 w-4" />
              ) : (
                <ChevronDown className="h-4 w-4" />
              )}
            </button>
            {expandedSections.price && (
              <div className="mt-2 space-y-3">
                {/* Quick Price Ranges */}
                <div className="space-y-2">
                  {PRICE_RANGES.map((range, idx) => {
                    const isSelected =
                      filters.minPrice === range.min &&
                      (range.max === Infinity
                        ? filters.maxPrice === null
                        : filters.maxPrice === range.max);
                    return (
                      <button
                        key={idx}
                        onClick={() => handlePriceRangeSelect(range.min, range.max)}
                        className={`w-full text-left px-3 py-2 rounded-lg text-sm transition-colors ${
                          isSelected
                            ? "bg-primary text-primary-foreground"
                            : "bg-secondary hover:bg-secondary/80"
                        }`}
                      >
                        {range.label}
                      </button>
                    );
                  })}
                </div>

                {/* Custom Price Range */}
                <div className="pt-2 border-t">
                  <p className="text-xs text-muted-foreground mb-2">Custom Range</p>
                  <div className="flex items-center gap-2">
                    <input
                      type="number"
                      placeholder="Min"
                      value={filters.minPrice ?? ""}
                      onChange={(e) => handlePriceChange("min", e.target.value)}
                      min="0"
                      max={maxPriceValue}
                      className="w-full rounded-lg border bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
                    />
                    <span className="text-muted-foreground">-</span>
                    <input
                      type="number"
                      placeholder="Max"
                      value={filters.maxPrice ?? ""}
                      onChange={(e) => handlePriceChange("max", e.target.value)}
                      min="0"
                      max={maxPriceValue}
                      className="w-full rounded-lg border bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
                    />
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Colors */}
          <div>
            <button
              onClick={() => toggleSection("color")}
              className="flex w-full items-center justify-between py-2 text-sm font-semibold"
            >
              <span>Color {availableColors.length > 0 && `(${availableColors.length})`}</span>
              {expandedSections.color ? (
                <ChevronUp className="h-4 w-4" />
              ) : (
                <ChevronDown className="h-4 w-4" />
              )}
            </button>
            {expandedSections.color && (
              <div className="mt-2">
                {availableColors.length > 0 ? (
                  <div className="flex flex-wrap gap-2">
                    {availableColors.map((color) => {
                      const isSelected = filters.colors.includes(color);
                      const colorHex = colorMap[color.toLowerCase()] || "#CCCCCC";
                      return (
                        <button
                          key={color}
                          onClick={() => handleColorToggle(color)}
                          className={`relative h-10 w-10 rounded-full border-2 transition-all ${
                            isSelected
                              ? "border-primary scale-110 ring-2 ring-primary ring-offset-2"
                              : "border-border hover:scale-105"
                          }`}
                          style={{ backgroundColor: colorHex }}
                          title={color}
                        >
                          {isSelected && (
                            <div className="absolute inset-0 flex items-center justify-center">
                              <span className="text-xs">✓</span>
                            </div>
                          )}
                        </button>
                      );
                    })}
                  </div>
                ) : (
                  <p className="text-xs text-muted-foreground">No colors available</p>
                )}
              </div>
            )}
          </div>

          {/* Style Tags */}
          <div>
            <button
              onClick={() => toggleSection("style")}
              className="flex w-full items-center justify-between py-2 text-sm font-semibold"
            >
              <span>Style {availableStyleTags.length > 0 && `(${availableStyleTags.length})`}</span>
              {expandedSections.style ? (
                <ChevronUp className="h-4 w-4" />
              ) : (
                <ChevronDown className="h-4 w-4" />
              )}
            </button>
            {expandedSections.style && (
              <div className="mt-2">
                {availableStyleTags.length > 0 ? (
                  <div className="flex flex-wrap gap-2">
                    {availableStyleTags.map((tag) => (
                      <button
                        key={tag}
                        onClick={() => handleStyleTagToggle(tag)}
                        className={`rounded-full px-3 py-1 text-xs font-medium transition-colors ${
                          filters.styleTags.includes(tag)
                            ? "bg-primary text-primary-foreground"
                            : "bg-secondary text-secondary-foreground hover:bg-secondary/80"
                        }`}
                      >
                        {tag}
                      </button>
                    ))}
                  </div>
                ) : (
                  <p className="text-xs text-muted-foreground">No style tags available</p>
                )}
              </div>
            )}
          </div>

          {/* Clear Filters */}
          {hasActiveFilters && (
            <div className="bg-background pt-4 border-t">
              <button
                onClick={clearFilters}
                className="w-full rounded-lg border border-destructive bg-destructive/10 px-4 py-2 text-sm font-medium text-destructive transition-colors hover:bg-destructive/20"
              >
                Clear All Filters
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Mobile Overlay */}
      {isOpen && (
        <div
          className="lg:hidden fixed inset-0 bg-black/50 z-30"
          onClick={() => setIsOpen(false)}
        />
      )}
    </>
  );
}
