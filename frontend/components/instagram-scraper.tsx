"use client";

import { useState } from "react";
import { scrapeSocialMedia, batchScrapeSocialMedia, ScrapeResponse, BatchScrapeResponse, ScrapedPost, getProxiedImageUrl } from "@/lib/api";
import { Loader2, Download, Plus, X, Instagram, ExternalLink, CheckCircle2, XCircle, ChevronDown, ChevronUp, Bug } from "lucide-react";

export function InstagramScraper() {
  const [mode, setMode] = useState<"single" | "batch">("single");
  const [url, setUrl] = useState("");
  const [urls, setUrls] = useState<string[]>([""]);
  const [postLimit, setPostLimit] = useState(50);
  const [saveToDb, setSaveToDb] = useState(false);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<ScrapeResponse | BatchScrapeResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [expandedDebug, setExpandedDebug] = useState<{ [key: number]: boolean }>({});

  const handleAddUrl = () => {
    setUrls([...urls, ""]);
  };

  const handleRemoveUrl = (index: number) => {
    setUrls(urls.filter((_, i) => i !== index));
  };

  const handleUrlChange = (index: number, value: string) => {
    const newUrls = [...urls];
    newUrls[index] = value;
    setUrls(newUrls);
  };

  const handleSingleScrape = async () => {
    if (!url.trim()) {
      setError("Please enter a URL");
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const response = await scrapeSocialMedia(
        {
          url: url.trim(),
          post_limit: postLimit,
          use_api: true,
        },
        saveToDb
      );
      setResult(response);
    } catch (err: any) {
      setError(err.message || "Failed to scrape Instagram");
    } finally {
      setLoading(false);
    }
  };

  const handleBatchScrape = async () => {
    const validUrls = urls.filter((u) => u.trim());
    if (validUrls.length === 0) {
      setError("Please enter at least one URL");
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const response = await batchScrapeSocialMedia(
        {
          urls: validUrls,
          post_limit: postLimit,
          use_api: true,
        },
        saveToDb
      );
      setResult(response);
    } catch (err: any) {
      setError(err.message || "Failed to batch scrape");
    } finally {
      setLoading(false);
    }
  };

  const getPostImage = (post: ScrapedPost): string | null => {
    const data = post.structured_data || post.raw_data || {};
    
    // Priority 1: Check displayUrl first (main/cover image - most reliable)
    if (data.displayUrl && typeof data.displayUrl === 'string' && data.displayUrl.startsWith('http')) {
      return data.displayUrl;
    }
    
    // Priority 2: Check images array (for Sidecar/carousel posts)
    if (data.images && Array.isArray(data.images) && data.images.length > 0) {
      const firstImage = data.images[0];
      if (typeof firstImage === 'string' && firstImage.startsWith('http')) {
        return firstImage;
      }
    }
    
    // Priority 3: Handle childPosts (for Sidecar posts with nested structure)
    if (data.childPosts && Array.isArray(data.childPosts) && data.childPosts.length > 0) {
      const firstChild = data.childPosts[0];
      if (firstChild.displayUrl && typeof firstChild.displayUrl === 'string' && firstChild.displayUrl.startsWith('http')) {
        return firstChild.displayUrl;
      }
      if (firstChild.images && Array.isArray(firstChild.images) && firstChild.images.length > 0) {
        const childImage = firstChild.images[0];
        if (typeof childImage === 'string' && childImage.startsWith('http')) {
          return childImage;
        }
      }
    }
    
    // Priority 4: Check other common image URL fields
    const imageFields = [
      'imageUrl',
      'image',
      'thumbnailUrl',
      'mediaUrl',
      'media',
      'photoUrl',
      'image_url',
      'imageUrlHD',
      'display_url',
      'thumbnail_url',
      'media_url',
    ];
    
    for (const field of imageFields) {
      if (data[field] && typeof data[field] === 'string' && data[field].startsWith('http')) {
        return data[field];
      }
    }
    
    // Priority 5: Handle old sidecarChildren format
    if (data.sidecarChildren && Array.isArray(data.sidecarChildren) && data.sidecarChildren.length > 0) {
      const firstChild = data.sidecarChildren[0];
      if (firstChild.displayUrl && typeof firstChild.displayUrl === 'string' && firstChild.displayUrl.startsWith('http')) {
        return firstChild.displayUrl;
      }
      for (const field of imageFields) {
        if (firstChild[field] && typeof firstChild[field] === 'string' && firstChild[field].startsWith('http')) {
          return firstChild[field];
        }
      }
    }
    
    // Priority 6: Handle nested structures
    if (data.media && typeof data.media === 'object') {
      for (const field of imageFields) {
        if (data.media[field] && typeof data.media[field] === 'string' && data.media[field].startsWith('http')) {
          return data.media[field];
        }
      }
    }
    
    // Priority 7: Check if there's a type field indicating it's a video (use thumbnail)
    if (data.type === 'Video' || data.type === 'video') {
      if (data.displayUrl && typeof data.displayUrl === 'string' && data.displayUrl.startsWith('http')) {
        return data.displayUrl; // Video thumbnail
      }
      if (data.videoUrl) return data.videoUrl;
      if (data.video_url) return data.video_url;
      if (data.thumbnailUrl) return data.thumbnailUrl;
      if (data.thumbnail_url) return data.thumbnail_url;
    }
    
    return null;
  };

  const getPostUrl = (post: ScrapedPost): string | null => {
    const data = post.structured_data || post.raw_data || {};
    
    // Prioritize post URL fields (not image URLs)
    const postUrlFields = [
      'postUrl',
      'post_url',
      'shortCode', // Instagram short code - we can construct URL
      'short_code',
      'permalink',
      'link',
    ];
    
    for (const field of postUrlFields) {
      if (data[field] && typeof data[field] === 'string') {
        // If it's a short code, construct the full URL
        if ((field === 'shortCode' || field === 'short_code') && !data[field].startsWith('http')) {
          return `https://www.instagram.com/p/${data[field]}/`;
        }
        if (data[field].startsWith('http')) {
          return data[field];
        }
      }
    }
    
    // Fallback to url field, but only if it looks like a post URL (not an image)
    if (data.url && typeof data.url === 'string') {
      // Check if it's an Instagram post URL (not an image URL)
      if (data.url.includes('instagram.com/p/') || data.url.includes('instagram.com/reel/')) {
        return data.url;
      }
      // If it doesn't look like an image URL, use it
      if (!data.url.match(/\.(jpg|jpeg|png|gif|webp|mp4|mov)/i)) {
        return data.url;
      }
    }
    
    return null;
  };

  const getPostCaption = (post: ScrapedPost): string => {
    if (post.structured_data?.caption) return post.structured_data.caption;
    if (post.raw_data?.caption) return post.raw_data.caption;
    if (post.structured_data?.text) return post.structured_data.text;
    return "No caption available";
  };

  return (
    <div className="space-y-6">
      {/* Mode Toggle */}
      <div className="flex gap-2 border-b pb-4">
        <button
          onClick={() => {
            setMode("single");
            setResult(null);
            setError(null);
          }}
          className={`px-4 py-2 rounded-md font-medium transition-colors ${
            mode === "single"
              ? "bg-primary text-primary-foreground"
              : "bg-muted text-muted-foreground hover:bg-muted/80"
          }`}
        >
          Single URL
        </button>
        <button
          onClick={() => {
            setMode("batch");
            setResult(null);
            setError(null);
          }}
          className={`px-4 py-2 rounded-md font-medium transition-colors ${
            mode === "batch"
              ? "bg-primary text-primary-foreground"
              : "bg-muted text-muted-foreground hover:bg-muted/80"
          }`}
        >
          Batch URLs
        </button>
      </div>

      {/* Form */}
      <div className="space-y-4 p-6 border rounded-lg bg-card">
        {mode === "single" ? (
          <div className="space-y-4">
            <div>
              <label htmlFor="url" className="block text-sm font-medium mb-2">
                Instagram URL
              </label>
              <input
                id="url"
                type="text"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                placeholder="https://www.instagram.com/username/ or https://www.instagram.com/explore/tags/hashtag/"
                className="w-full px-4 py-2 border rounded-md bg-background"
                disabled={loading}
              />
              <p className="mt-1 text-xs text-muted-foreground">
                Supports Instagram profiles and hashtags
              </p>
            </div>
          </div>
        ) : (
          <div className="space-y-4">
            <label className="block text-sm font-medium mb-2">Instagram URLs</label>
            {urls.map((urlValue, index) => (
              <div key={index} className="flex gap-2">
                <input
                  type="text"
                  value={urlValue}
                  onChange={(e) => handleUrlChange(index, e.target.value)}
                  placeholder={`URL ${index + 1}`}
                  className="flex-1 px-4 py-2 border rounded-md bg-background"
                  disabled={loading}
                />
                {urls.length > 1 && (
                  <button
                    onClick={() => handleRemoveUrl(index)}
                    className="px-3 py-2 border rounded-md hover:bg-destructive hover:text-destructive-foreground transition-colors"
                    disabled={loading}
                  >
                    <X className="h-4 w-4" />
                  </button>
                )}
              </div>
            ))}
            <button
              onClick={handleAddUrl}
              className="flex items-center gap-2 px-4 py-2 border rounded-md hover:bg-muted transition-colors"
              disabled={loading}
            >
              <Plus className="h-4 w-4" />
              Add URL
            </button>
          </div>
        )}

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label htmlFor="postLimit" className="block text-sm font-medium mb-2">
              Post Limit
            </label>
            <input
              id="postLimit"
              type="number"
              min="1"
              max="1000"
              value={postLimit}
              onChange={(e) => setPostLimit(parseInt(e.target.value) || 50)}
              className="w-full px-4 py-2 border rounded-md bg-background"
              disabled={loading}
            />
          </div>
          <div className="flex items-end">
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={saveToDb}
                onChange={(e) => setSaveToDb(e.target.checked)}
                className="w-4 h-4"
                disabled={loading}
              />
              <span className="text-sm">Save to database</span>
            </label>
          </div>
        </div>

        <button
          onClick={mode === "single" ? handleSingleScrape : handleBatchScrape}
          disabled={loading}
          className="w-full flex items-center justify-center gap-2 px-6 py-3 bg-primary text-primary-foreground rounded-md font-medium hover:bg-primary/90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {loading ? (
            <>
              <Loader2 className="h-5 w-5 animate-spin" />
              Scraping...
            </>
          ) : (
            <>
              <Instagram className="h-5 w-5" />
              {mode === "single" ? "Scrape Instagram" : "Batch Scrape"}
            </>
          )}
        </button>
      </div>

      {/* Error Display */}
      {error && (
        <div className="p-4 border border-destructive rounded-lg bg-destructive/10">
          <div className="flex items-center gap-2 text-destructive">
            <XCircle className="h-5 w-5" />
            <span className="font-medium">Error</span>
          </div>
          <p className="mt-2 text-sm">{error}</p>
        </div>
      )}

      {/* Results Display */}
      {result && (
        <div className="space-y-4">
          <div className="p-4 border rounded-lg bg-muted/50">
            <div className="flex items-center gap-2 mb-2">
              {result.success ? (
                <CheckCircle2 className="h-5 w-5 text-green-500" />
              ) : (
                <XCircle className="h-5 w-5 text-red-500" />
              )}
              <h3 className="font-semibold">{result.message}</h3>
            </div>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-4 text-sm">
              <div>
                <span className="text-muted-foreground">Total Posts:</span>
                <span className="ml-2 font-medium">{result.total_posts}</span>
              </div>
              {"platform" in result && result.platform && (
                <div>
                  <span className="text-muted-foreground">Platform:</span>
                  <span className="ml-2 font-medium capitalize">{result.platform}</span>
                </div>
              )}
              {"urls_processed" in result && (
                <>
                  <div>
                    <span className="text-muted-foreground">Processed:</span>
                    <span className="ml-2 font-medium">{result.urls_processed}</span>
                  </div>
                  <div>
                    <span className="text-muted-foreground">Failed:</span>
                    <span className="ml-2 font-medium text-destructive">{result.urls_failed}</span>
                  </div>
                </>
              )}
            </div>
            {"estimated_cost" in result && result.estimated_cost && (
              <div className="mt-2 text-sm">
                <span className="text-muted-foreground">Estimated Cost:</span>
                <span className="ml-2 font-medium">${result.estimated_cost.toFixed(4)}</span>
              </div>
            )}
          </div>

          {/* Posts Grid */}
          {result.posts && result.posts.length > 0 && (
            <div>
              <h4 className="text-lg font-semibold mb-4">Scraped Posts ({result.posts.length})</h4>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {result.posts.map((post, index) => {
                  console.log ('seee poss result',post)
                  const imageUrl = getPostImage(post);
                  const postUrl = getPostUrl(post);
                  const caption = getPostCaption(post);

                  return (
                    <div
                      key={index}
                      className="border rounded-lg overflow-hidden bg-card hover:shadow-lg transition-shadow"
                    >
                      {imageUrl ? (
                        <div className="aspect-square relative bg-muted group">
                          <img
                            src={getProxiedImageUrl(imageUrl)}

                            alt={`Post ${index + 1}`}
                            className="w-full h-full object-cover"
                            loading="lazy"
                            onLoad={() => {
                              // Image loaded successfully
                              console.log(`✅ Image loaded for post ${index + 1} via proxy`);
                            }}
                            onError={async (e) => {
                              // Log error for debugging
                              const proxiedUrl = getProxiedImageUrl(imageUrl);
                              const img = e.target as HTMLImageElement;
                              const currentSrc = img.src;
                              
                              console.error(`❌ Failed to load image for post ${index + 1}`);
                              console.error(`Original URL:`, imageUrl);
                              console.error(`Proxied URL:`, proxiedUrl);
                              console.error(`Current src:`, currentSrc);
                              
                              // Test the proxy endpoint directly to get actual error
                              if (currentSrc.includes('/proxy-image')) {
                                try {
                                  const testResponse = await fetch(proxiedUrl, { method: 'HEAD' });
                                  console.error(`⚠️ Proxy endpoint response: ${testResponse.status} ${testResponse.statusText}`);
                                  if (!testResponse.ok) {
                                    const errorText = await testResponse.text().catch(() => 'No error details');
                                    console.error(`⚠️ Proxy error details:`, errorText);
                                  }
                                } catch (fetchError) {
                                  console.error(`⚠️ Failed to test proxy endpoint:`, fetchError);
                                  console.error(`💡 Make sure backend is running on http://localhost:8000`);
                                }
                                console.error(`💡 Test proxy manually: ${proxiedUrl}`);
                              }
                              
                              // Show error message
                              img.style.display = 'none';
                              const parent = img.parentElement;
                              if (parent) {
                                parent.innerHTML = `
                                  <div class="w-full h-full flex flex-col items-center justify-center p-4 bg-muted cursor-pointer" onclick="window.open('${postUrl || '#'}', '_blank')">
                                    <svg class="h-12 w-12 text-muted-foreground mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"></path>
                                    </svg>
                                    <p class="text-xs text-muted-foreground text-center">Failed to load image</p>
                                    <p class="text-xs text-muted-foreground text-center mt-1">Check console for details</p>
                                    ${postUrl ? `<p class="text-xs text-muted-foreground text-center mt-1">Click to view on Instagram</p>` : ''}
                                  </div>
                                `;
                              }
                            }}
                          />
                          {/* Show image URL on hover for debugging */}
                          {expandedDebug[index] && (
                            <div className="absolute bottom-0 left-0 right-0 bg-black/75 text-white text-xs p-2 break-all">
                              <div className="font-mono text-[10px]">{imageUrl.substring(0, 100)}...</div>
                            </div>
                          )}
                          {postUrl && (
                            <a
                              href={postUrl}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="absolute top-2 right-2 p-2 bg-black/50 rounded-full hover:bg-black/70 transition-colors z-10"
                              onClick={(e) => e.stopPropagation()}
                            >
                              <ExternalLink className="h-4 w-4 text-white" />
                            </a>
                          )}
                        </div>
                      ) : (
                        <div className="aspect-square bg-muted flex flex-col items-center justify-center p-4">
                          <Instagram className="h-12 w-12 text-muted-foreground mb-2" />
                          <p className="text-xs text-muted-foreground text-center">No image found</p>
                        </div>
                      )}
                      <div className="p-4">
                        <p className="text-sm text-muted-foreground line-clamp-3">{caption}</p>
                        <div className="mt-2 flex items-center gap-2 text-xs text-muted-foreground">
                          <span>{new Date(post.scraped_date).toLocaleDateString()}</span>
                          <span>•</span>
                          <span className="capitalize">{post.source}</span>
                        </div>
                        {!imageUrl && (
                          <button
                            onClick={() => setExpandedDebug({ ...expandedDebug, [index]: !expandedDebug[index] })}
                            className="mt-2 flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground transition-colors"
                          >
                            <Bug className="h-3 w-3" />
                            {expandedDebug[index] ? "Hide" : "Show"} debug data
                            {expandedDebug[index] ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />}
                          </button>
                        )}
                        {!imageUrl && expandedDebug[index] && (
                          <div className="mt-2 p-3 bg-muted rounded text-xs overflow-auto max-h-48">
                            <pre className="whitespace-pre-wrap">
                              {JSON.stringify(
                                {
                                  structured_data: post.structured_data,
                                  raw_data: post.raw_data,
                                },
                                null,
                                2
                              )}
                            </pre>
                          </div>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* Batch Errors */}
          {"errors" in result && result.errors && result.errors.length > 0 && (
            <div className="p-4 border border-destructive rounded-lg bg-destructive/10">
              <h4 className="font-semibold text-destructive mb-2">Errors</h4>
              <ul className="space-y-1 text-sm">
                {result.errors.map((err, index) => (
                  <li key={index}>
                    <span className="font-medium">{err.url}:</span> {err.error}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

