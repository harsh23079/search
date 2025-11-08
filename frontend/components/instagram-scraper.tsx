"use client";

import { useState } from "react";
import { scrapeSocialMedia, batchScrapeSocialMedia, ScrapeResponse, BatchScrapeResponse, ScrapedPost, getProxiedImageUrl } from "@/lib/api";
import { Loader2, Download, Plus, X, Instagram, ExternalLink, CheckCircle2, XCircle, ChevronDown, ChevronUp, Bug, Heart, MessageCircle, User, Calendar, Hash } from "lucide-react";

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
  const [selectedPostIndex, setSelectedPostIndex] = useState<number | null>(null);

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

  const getPostOwner = (post: ScrapedPost): { username?: string; fullName?: string } | null => {
    const data = post.structured_data || post.raw_data || {};

    const username =
      data.ownerUsername ||
      data.owner_username ||
      data.username ||
      data.owner?.username ||
      data.owner?.ownerUsername;

    const fullName =
      data.ownerFullName ||
      data.owner_full_name ||
      data.fullName ||
      data.owner?.fullName ||
      data.owner?.ownerFullName;

    if (!username && !fullName) {
      return null;
    }

    return { username, fullName };
  };

  const getPostStats = (post: ScrapedPost): { likes: number | null; comments: number | null } => {
    const data = post.structured_data || post.raw_data || {};
    const likeCandidates = [
      data.likesCount,
      data.likeCount,
      data.likes,
      data.edge_liked_by?.count,
      data.edge_media_preview_like?.count,
      data.edgeMediaPreviewLike?.count,
    ];

    const commentCandidates = [
      data.commentsCount,
      data.commentCount,
      data.comments,
      data.edge_media_to_comment?.count,
      data.edgeMediaToComment?.count,
      data.edge_media_preview_comment?.count,
    ];

    const parseCount = (values: any[]): number | null => {
      for (const value of values) {
        if (typeof value === "number" && !Number.isNaN(value)) {
          return value;
        }
        if (typeof value === "string") {
          const parsed = parseInt(value.replace(/[^0-9]/g, ""), 10);
          if (!Number.isNaN(parsed)) return parsed;
        }
      }
      return null;
    };

    return {
      likes: parseCount(likeCandidates),
      comments: parseCount(commentCandidates),
    };
  };

  const getPostHashtags = (post: ScrapedPost): string[] => {
    const data = post.structured_data || post.raw_data || {};
    let hashtags: string[] = [];

    if (Array.isArray(data.hashtags)) {
      hashtags = data.hashtags.filter((tag: any) => typeof tag === "string");
    }

    if (hashtags.length === 0) {
      const caption = getPostCaption(post);
      const matches = caption.match(/#(\w+)/g);
      if (matches) {
        hashtags = matches.map((tag) => tag.replace("#", ""));
      }
    }

    return Array.from(new Set(hashtags)).slice(0, 12);
  };

  const getPostDateLabel = (post: ScrapedPost): string => {
    try {
      const rawDate =
        post.structured_data?.timestamp ||
        post.structured_data?.takenAtTimestamp ||
        post.structured_data?.taken_at_timestamp ||
        post.scraped_date;

      if (!rawDate) {
        return new Date(post.scraped_date).toLocaleDateString();
      }

      const parsed = typeof rawDate === "number" ? new Date(rawDate * 1000) : new Date(rawDate);
      if (Number.isNaN(parsed.getTime())) {
        return new Date(post.scraped_date).toLocaleDateString();
      }

      return parsed.toLocaleDateString(undefined, {
        year: "numeric",
        month: "short",
        day: "numeric",
      });
    } catch (error) {
      return new Date(post.scraped_date).toLocaleDateString();
    }
  };

  const getPostComments = (post: ScrapedPost): Array<{ username?: string; text: string; ownerId?: string }> => {
    const data = post.structured_data || post.raw_data || {};
    const comments: Array<{ username?: string; text: string; ownerId?: string }> = [];

    // Try to get firstComment
    if (data.firstComment && typeof data.firstComment === "string" && data.firstComment.trim()) {
      comments.push({ text: data.firstComment });
    }

    // Try to get latestComments array
    if (Array.isArray(data.latestComments) && data.latestComments.length > 0) {
      for (const comment of data.latestComments) {
        if (typeof comment === "string" && comment.trim()) {
          comments.push({ text: comment });
        } else if (typeof comment === "object" && comment !== null) {
          const commentText = comment.text || comment.comment || comment.content || "";
          const commentUsername = comment.username || comment.ownerUsername || comment.owner?.username;
          const commentOwnerId = comment.ownerId || comment.owner?.id;
          
          if (commentText.trim()) {
            comments.push({
              username: commentUsername,
              text: commentText,
              ownerId: commentOwnerId,
            });
          }
        }
      }
    }

    // Try to get comments array (alternative field name)
    if (Array.isArray(data.comments) && data.comments.length > 0) {
      for (const comment of data.comments) {
        if (typeof comment === "string" && comment.trim()) {
          // Avoid duplicates
          if (!comments.some(c => c.text === comment)) {
            comments.push({ text: comment });
          }
        } else if (typeof comment === "object" && comment !== null) {
          const commentText = comment.text || comment.comment || comment.content || "";
          if (commentText.trim() && !comments.some(c => c.text === commentText)) {
            comments.push({
              username: comment.username || comment.ownerUsername,
              text: commentText,
              ownerId: comment.ownerId || comment.owner?.id,
            });
          }
        }
      }
    }

    // Remove duplicates and return up to 10 comments
    const uniqueComments = Array.from(
      new Map(comments.map(c => [c.text, c])).values()
    ).slice(0, 10);

    return uniqueComments;
  };

  const handleCardClick = (index: number) => {
    setSelectedPostIndex(index);
  };

  const handleCloseModal = () => {
    setSelectedPostIndex(null);
  };

  const handleOpenInstagram = (postUrl?: string | null) => {
    if (!postUrl) return;
    window.open(postUrl, "_blank", "noopener,noreferrer");
  };

  return (
    <div className="flex h-full flex-col overflow-hidden">
      {/* Mode Toggle - Fixed */}
      <div className="flex gap-2 border-b pb-4 shrink-0 mb-6">
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

      {/* Form - Fixed */}
      <div className="space-y-4 p-6 border rounded-lg bg-card shrink-0 mb-6">
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

      {/* Scrollable Content Area */}
      <div className="flex-1 overflow-y-auto min-h-0">
        {/* Error Display */}
        {error && (
          <div className="p-4 border border-destructive rounded-lg bg-destructive/10 mb-6">
            <div className="flex items-center gap-2 text-destructive">
              <XCircle className="h-5 w-5" />
              <span className="font-medium">Error</span>
            </div>
            <p className="mt-2 text-sm">{error}</p>
          </div>
        )}

        {/* Results Display */}
        {result && (
        <div className="space-y-4 pb-4">
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
                  const imageUrl = getPostImage(post);
                  const postUrl = getPostUrl(post);
                  const caption = getPostCaption(post);
                  const owner = getPostOwner(post);
                  const stats = getPostStats(post);
                  const hashtags = getPostHashtags(post);
                  const dateLabel = getPostDateLabel(post);
                  const isClickable = Boolean(postUrl);
 
                   return (
                    <div
                      key={index}
                      role="button"
                      tabIndex={0}
                      onClick={() => handleCardClick(index)}
                      onKeyDown={(event) => {
                        if (event.key === "Enter" || event.key === " ") {
                          event.preventDefault();
                          handleCardClick(index);
                        }
                      }}
                      className="group relative overflow-hidden rounded-lg border bg-card transition-shadow cursor-pointer hover:shadow-xl focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2"
                    >
                      <div className="aspect-square relative flex items-center justify-center bg-muted">
                        {imageUrl ? (
                          <img
                            src={getProxiedImageUrl(imageUrl)}
                            alt={`Post ${index + 1}`}
                            className="h-full w-full object-cover"
                            loading="lazy"
                            onError={async (e) => {
                              const proxiedUrl = getProxiedImageUrl(imageUrl);
                              const img = e.target as HTMLImageElement;
                              const currentSrc = img.src;

                              console.error(`❌ Failed to load image for post ${index + 1}`);
                              console.error(`Original URL:`, imageUrl);
                              console.error(`Proxied URL:`, proxiedUrl);
                              console.error(`Current src:`, currentSrc);

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
                                }
                                console.error(`💡 Test proxy manually: ${proxiedUrl}`);
                              }

                              img.style.display = 'none';
                              const parent = img.parentElement;
                              if (parent) {
                                parent.innerHTML = `
                                  <div class="flex h-full w-full flex-col items-center justify-center gap-2 bg-muted p-4">
                                    <svg class="h-12 w-12 text-muted-foreground" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"></path>
                                    </svg>
                                    <p class="text-xs text-muted-foreground text-center">Failed to load image</p>
                                  </div>
                                `;
                              }
                            }}
                          />
                        ) : (
                          <div className="flex h-full w-full flex-col items-center justify-center gap-3 p-4 text-muted-foreground">
                            <Instagram className="h-10 w-10" />
                            <p className="text-xs text-center">No image found</p>
                          </div>
                        )}
                        <div className="absolute inset-0 bg-black/0 group-hover:bg-black/10 transition-colors flex items-center justify-center">
                          <div className="opacity-0 group-hover:opacity-100 transition-opacity inline-flex items-center gap-2 rounded-full bg-black/70 px-4 py-2 text-sm text-white">
                            <span>View Details</span>
                          </div>
                        </div>
                      </div>

                      <div className="p-4 space-y-2">
                        <p className="text-sm font-medium text-foreground line-clamp-2">{caption}</p>
                        <div className="flex flex-wrap items-center gap-3 text-xs text-muted-foreground">
                          {owner?.username && (
                            <span className="inline-flex items-center gap-1">
                              <User className="h-3.5 w-3.5" />
                              <span>@{owner.username}</span>
                            </span>
                          )}
                          <span className="inline-flex items-center gap-1">
                            <Calendar className="h-3.5 w-3.5" />
                            <span>{dateLabel}</span>
                          </span>
                          <span className="inline-flex items-center gap-1 capitalize">
                            <Instagram className="h-3.5 w-3.5" />
                            <span>{post.source}</span>
                          </span>
                        </div>
                      </div>

                      {!imageUrl && (
                        <div className="px-4 pb-4">
                          <button
                            onClick={(event) => {
                              event.stopPropagation();
                              setExpandedDebug({ ...expandedDebug, [index]: !expandedDebug[index] });
                            }}
                            className="flex items-center gap-1 text-xs text-muted-foreground transition-colors hover:text-foreground"
                          >
                            <Bug className="h-3 w-3" />
                            {expandedDebug[index] ? "Hide" : "Show"} debug data
                            {expandedDebug[index] ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />}
                          </button>
                          {expandedDebug[index] && (
                            <div className="mt-2 max-h-48 overflow-auto rounded bg-muted p-3 text-xs">
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
                      )}

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

      {/* Post Detail Modal */}
      {selectedPostIndex !== null && result?.posts && result.posts[selectedPostIndex] && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 p-4"
          onClick={handleCloseModal}
        >
          <div
            className="relative flex h-full max-h-[90vh] w-full max-w-6xl flex-col overflow-hidden rounded-lg bg-background shadow-2xl md:flex-row"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Close Button */}
            <button
              onClick={handleCloseModal}
              className="absolute top-4 right-4 z-10 rounded-full bg-black/50 p-2 text-white transition-colors hover:bg-black/70 focus:outline-none focus:ring-2 focus:ring-white"
              aria-label="Close modal"
            >
              <X className="h-5 w-5" />
            </button>

            {/* Image Section */}
            <div className="flex h-full w-full items-center justify-center bg-muted md:w-1/2">
              {(() => {
                const post = result.posts[selectedPostIndex];
                const imageUrl = getPostImage(post);
                return imageUrl ? (
                  <img
                    src={getProxiedImageUrl(imageUrl)}
                    alt={`Post ${selectedPostIndex + 1}`}
                    className="max-h-full w-full object-contain"
                  />
                ) : (
                  <div className="flex flex-col items-center justify-center gap-4 p-8 text-muted-foreground">
                    <Instagram className="h-16 w-16" />
                    <p className="text-sm">No image available</p>
                  </div>
                );
              })()}
            </div>

            {/* Details Section */}
            <div className="flex h-full w-full flex-col gap-6 overflow-y-auto p-6 md:w-1/2">
              {(() => {
                const post = result.posts[selectedPostIndex];
                const imageUrl = getPostImage(post);
                const postUrl = getPostUrl(post);
                const caption = getPostCaption(post);
                const owner = getPostOwner(post);
                const stats = getPostStats(post);
                const hashtags = getPostHashtags(post);
                const dateLabel = getPostDateLabel(post);

                return (
                  <>
                    {/* Header */}
                    <div className="space-y-2 border-b pb-4">
                      {owner && (
                        <div className="flex items-center gap-2">
                          <User className="h-4 w-4 text-muted-foreground" />
                          <span className="font-semibold">
                            {owner.fullName || `@${owner.username}`}
                          </span>
                          {owner.username && owner.fullName && (
                            <span className="text-sm text-muted-foreground">@{owner.username}</span>
                          )}
                        </div>
                      )}
                      <div className="flex items-center gap-2 text-sm text-muted-foreground">
                        <Calendar className="h-4 w-4" />
                        <span>{dateLabel}</span>
                        <span>•</span>
                        <Instagram className="h-4 w-4" />
                        <span className="capitalize">{post.source}</span>
                      </div>
                    </div>

                    {/* Caption */}
                    <div className="space-y-2">
                      <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">Caption</p>
                      <p className="whitespace-pre-line text-base leading-relaxed text-foreground">{caption}</p>
                    </div>

                    {/* Stats */}
                    {(stats.likes !== null || stats.comments !== null) && (
                      <div className="flex flex-wrap gap-6 text-base">
                        {stats.likes !== null && (
                          <div className="flex items-center gap-2">
                            <Heart className="h-5 w-5 text-red-500" />
                            <span className="font-medium">{stats.likes.toLocaleString()}</span>
                            <span className="text-sm text-muted-foreground">likes</span>
                          </div>
                        )}
                        {stats.comments !== null && (
                          <div className="flex items-center gap-2">
                            <MessageCircle className="h-5 w-5 text-blue-500" />
                            <span className="font-medium">{stats.comments.toLocaleString()}</span>
                            <span className="text-sm text-muted-foreground">comments</span>
                          </div>
                        )}
                      </div>
                    )}

                    {/* Hashtags */}
                    {hashtags.length > 0 && (
                      <div className="space-y-2">
                        <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">Hashtags</p>
                        <div className="flex flex-wrap gap-2">
                          {hashtags.map((tag) => (
                            <span
                              key={tag}
                              className="inline-flex items-center gap-1 rounded-full bg-primary/10 px-3 py-1.5 text-sm text-primary"
                            >
                              <Hash className="h-3.5 w-3.5" />
                              {tag}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Comments */}
                    {(() => {
                      const comments = getPostComments(post);
                      if (comments.length > 0) {
                        return (
                          <div className="space-y-2">
                            <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                              Comments ({comments.length})
                            </p>
                            <div className="space-y-3 max-h-64 overflow-y-auto rounded-lg border bg-muted/30 p-3">
                              {comments.map((comment, idx) => (
                                <div key={idx} className="space-y-1">
                                  {comment.username && (
                                    <div className="flex items-center gap-2">
                                      <User className="h-3.5 w-3.5 text-muted-foreground" />
                                      <span className="text-sm font-medium text-foreground">
                                        {comment.username}
                                      </span>
                                    </div>
                                  )}
                                  <p className="text-sm text-foreground leading-relaxed pl-5">
                                    {comment.text}
                                  </p>
                                </div>
                              ))}
                            </div>
                          </div>
                        );
                      }
                      return null;
                    })()}

                    {/* Open Instagram Button */}
                    {postUrl && (
                      <button
                        onClick={() => handleOpenInstagram(postUrl)}
                        className="mt-auto flex w-full items-center justify-center gap-2 rounded-lg bg-primary px-6 py-3 font-medium text-primary-foreground transition-colors hover:bg-primary/90 focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2"
                      >
                        <ExternalLink className="h-5 w-5" />
                        <span>View on Instagram</span>
                      </button>
                    )}
                  </>
                );
              })()}
            </div>
          </div>
        </div>
        )}
      </div>
    </div>
  );
}

