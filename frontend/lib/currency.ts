/**
 * Format price with currency symbol
 */
export function formatPrice(price: number, currency?: string): string {
  const currencyCode = currency?.toUpperCase() || "USD";
  
  // Currency symbol mapping
  const currencySymbols: Record<string, string> = {
    INR: "₹",
    USD: "$",
    EUR: "€",
    GBP: "£",
    JPY: "¥",
    CAD: "C$",
    AUD: "A$",
  };

  const symbol = currencySymbols[currencyCode] || currencyCode;
  
  // Check if price is a whole number
  const isWholeNumber = price % 1 === 0;
  
  // Format number with appropriate decimal places
  // INR: no decimals for whole numbers, 2 decimals otherwise
  // Other currencies: always 2 decimals
  const formattedPrice = price.toLocaleString("en-IN", {
    minimumFractionDigits: currencyCode === "INR" ? (isWholeNumber ? 0 : 2) : 2,
    maximumFractionDigits: currencyCode === "INR" ? (isWholeNumber ? 0 : 2) : 2,
  });

  // For INR, symbol comes before the number
  if (currencyCode === "INR") {
    return `${symbol}${formattedPrice}`;
  }
  
  return `${symbol}${formattedPrice}`;
}

