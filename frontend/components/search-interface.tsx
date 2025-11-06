"use client";

import { useState, useRef, useEffect } from "react";
import { Send, Image as ImageIcon, Loader2, Sparkles, X } from "lucide-react";
import { Product } from "@/types/product";
import { searchText, searchSimilarImage } from "@/lib/api";
import { ProductCard } from "./product-card";

interface Message {
  type: "user" | "ai";
  content: string;
  imageUrl?: string;
  timestamp: Date;
}

export function SearchInterface() {
  const [messages, setMessages] = useState<Message[]>([
    {
      type: "ai",
      content: "Hi! I'm your Fashion AI assistant. Describe what you're looking for, or upload an image to find similar products. How can I help you today?",
      timestamp: new Date(),
    },
  ]);
  const [input, setInput] = useState("");
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, products]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const queryText = input.trim();
    if (!queryText && !selectedFile) return;

    const currentFile = selectedFile;
    const currentPreviewUrl = previewUrl;
    
    const userMessage: Message = {
      type: "user",
      content: queryText || "Searching for similar products...",
      imageUrl: currentPreviewUrl || undefined,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setLoading(true);
    setError(null);

    try {
      let results: Product[] = [];

      if (currentFile) {
        // Image search
        results = await searchSimilarImage(currentFile, 20);
        setMessages((prev) => [
          ...prev,
          {
            type: "ai",
            content: `I found ${results.length} similar products based on your image! Here's what matches:`,
            timestamp: new Date(),
          },
        ]);
      } else if (queryText) {
        // Text search
        results = await searchText({ query: queryText, limit: 20 });
        setMessages((prev) => [
          ...prev,
          {
            type: "ai",
            content: `I found ${results.length} products matching "${queryText}". Here are the results:`,
            timestamp: new Date(),
          },
        ]);
      }

      setProducts(results);
      
      // Clear image after search
      if (currentFile) {
        setSelectedFile(null);
        if (currentPreviewUrl) {
          URL.revokeObjectURL(currentPreviewUrl);
          setPreviewUrl(null);
        }
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "Search failed";
      setError(errorMessage);
      setMessages((prev) => [
        ...prev,
        {
          type: "ai",
          content: `I'm sorry, I encountered an error: ${errorMessage}. Please try again.`,
          timestamp: new Date(),
        },
      ]);
      setProducts([]);
    } finally {
      setLoading(false);
    }
  };

  const handleImageUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (!file.type.startsWith("image/")) {
      setError("Please upload an image file");
      return;
    }

    setSelectedFile(file);
    setPreviewUrl(URL.createObjectURL(file));
    setError(null);
  };

  const clearImage = () => {
    setSelectedFile(null);
    if (previewUrl) {
      URL.revokeObjectURL(previewUrl);
      setPreviewUrl(null);
    }
  };

  const handleImageButtonClick = () => {
    fileInputRef.current?.click();
  };

  return (
    <div className="flex h-[calc(100vh-12rem)] flex-col">
      {/* Chat Messages */}
      <div className="flex-1 space-y-4 overflow-y-auto rounded-lg border bg-muted/20 p-4">
        {messages.map((message, idx) => (
          <div
            key={idx}
            className={`flex gap-3 ${
              message.type === "user" ? "justify-end" : "justify-start"
            }`}
          >
            {message.type === "ai" && (
              <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-primary/10">
                <Sparkles className="h-4 w-4 text-primary" />
              </div>
            )}
            <div
              className={`max-w-[80%] rounded-lg px-4 py-2 ${
                message.type === "user"
                  ? "bg-primary text-primary-foreground"
                  : "bg-background border"
              }`}
            >
              {message.imageUrl && (
                <div className="mb-2 overflow-hidden rounded-md">
                  <img
                    src={message.imageUrl}
                    alt="Uploaded"
                    className="max-h-32 w-auto object-contain"
                  />
                </div>
              )}
              <p className="text-sm">{message.content}</p>
            </div>
            {message.type === "user" && (
              <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-muted">
                <span className="text-xs font-medium">You</span>
              </div>
            )}
          </div>
        ))}

        {loading && (
          <div className="flex gap-3 justify-start">
            <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-primary/10">
              <Sparkles className="h-4 w-4 text-primary" />
            </div>
            <div className="rounded-lg bg-background border px-4 py-2">
              <div className="flex items-center gap-2">
                <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />
                <span className="text-sm text-muted-foreground">Searching...</span>
              </div>
            </div>
          </div>
        )}

        {/* Products Grid */}
        {!loading && products.length > 0 && (
          <div className="mt-4 space-y-4">
            <div className="flex gap-3 justify-start">
              <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-primary/10">
                <Sparkles className="h-4 w-4 text-primary" />
              </div>
              <div className="flex-1">
                <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
                  {products.map((product) => (
                    <ProductCard key={product.id} product={product} />
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <form onSubmit={handleSubmit} className="mt-4 space-y-2">
        {/* Image Preview */}
        {previewUrl && (
          <div className="relative inline-block">
            <div className="relative h-24 w-24 overflow-hidden rounded-lg border">
              <img
                src={previewUrl}
                alt="Preview"
                className="h-full w-full object-cover"
              />
            </div>
            <button
              type="button"
              onClick={clearImage}
              className="absolute -right-2 -top-2 rounded-full bg-destructive p-1 text-destructive-foreground hover:bg-destructive/90"
            >
              <X className="h-3 w-3" />
            </button>
          </div>
        )}

        {/* Input Bar */}
        <div className="flex gap-2">
          <input
            ref={fileInputRef}
            type="file"
            accept="image/*"
            onChange={handleImageUpload}
            className="hidden"
          />
          <button
            type="button"
            onClick={handleImageButtonClick}
            className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg border bg-background hover:bg-accent"
            aria-label="Upload image"
          >
            <ImageIcon className="h-5 w-5" />
          </button>
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Describe what you're looking for... (e.g., red shoes, casual dress)"
            className="flex-1 rounded-lg border bg-background px-4 py-2 focus:outline-none focus:ring-2 focus:ring-ring"
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                handleSubmit(e);
              }
            }}
          />
          <button
            type="submit"
            disabled={loading || (!input.trim() && !selectedFile)}
            className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-primary text-primary-foreground transition-colors hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed"
            aria-label="Send message"
          >
            {loading ? (
              <Loader2 className="h-5 w-5 animate-spin" />
            ) : (
              <Send className="h-5 w-5" />
            )}
          </button>
        </div>
        <p className="text-xs text-muted-foreground text-center">
          Type your query or upload an image to find products
        </p>
      </form>
    </div>
  );
}

