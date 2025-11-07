"use client";

import { useState, useEffect } from "react";
import { 
  getSavedPosts, SavedPost, getProxiedImageUrl,
  getExtractedItemsForPost, getExtractedItemWithMatches,
  ExtractedItem, SimilarProduct, deletePost
} from "@/lib/api";
import { Loader2, Instagram, Calendar, User, Heart, MessageCircle, Hash, ExternalLink, X, FileText, RefreshCw, Package, TrendingUp, Trash2 } from "lucide-react";
import { ScrapedPost } from "@/lib/api";

export default function PostsPage() {
  const [posts, setPosts] = useState<SavedPost[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedPostId, setSelectedPostId] = useState<string | null>(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPosts, setTotalPosts] = useState(0);
  const postsPerPage = 20;
  
  // Extracted items state
  const [extractedItems, setExtractedItems] = useState<ExtractedItem[]>([]);
  const [extractedItemsLoading, setExtractedItemsLoading] = useState(false);
  const [extractedItemsWithMatches, setExtractedItemsWithMatches] = useState<Map<string, SimilarProduct[]>>(new Map());
  const [deleting, setDeleting] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [postToDelete, setPostToDelete] = useState<string | null>(null);

  useEffect(() => {
    loadPosts();
  }, [currentPage]);

  const loadPosts = async () => {
    setLoading(true);
    setError(null);
    try {
      console.log(`[Posts Page] Loading posts - Page ${currentPage}, Limit: ${postsPerPage}`);
      const response = await getSavedPosts(
        postsPerPage,
        (currentPage - 1) * postsPerPage
      );
      
      console.log(`[Posts Page] Received response:`, response);
      
      // Handle response structure
      if (response && response.posts) {
        setPosts(response.posts);
        setTotalPosts(response.total || response.posts.length);
        console.log(`[Posts Page] Loaded ${response.posts.length} posts, Total: ${response.total || response.posts.length}`);
      } else {
        console.warn(`[Posts Page] Unexpected response structure:`, response);
        setPosts([]);
        setTotalPosts(0);
      }
    } catch (err: any) {
      console.error(`[Posts Page] Error loading posts:`, err);
      setError(err.message || "Failed to load posts");
      setPosts([]);
      setTotalPosts(0);
    } finally {
      setLoading(false);
    }
  };

  const getPostImage = (post: SavedPost | ScrapedPost): string | null => {
    // Handle flat structure (from database)
    if ('display_url' in post && post.display_url && typeof post.display_url === 'string' && post.display_url.startsWith('http')) {
      return post.display_url;
    }
    
    if ('images' in post && Array.isArray(post.images) && post.images.length > 0) {
      const firstImage = post.images[0];
      if (typeof firstImage === 'string' && firstImage.startsWith('http')) {
        return firstImage;
      }
    }
    
    // Handle nested structure (from file storage)
    if ('post_data' in post && post.post_data) {
      const scrapedPost = post.post_data;
      const data = scrapedPost.structured_data || scrapedPost.raw_data || {};
      
      if (data.displayUrl && typeof data.displayUrl === 'string' && data.displayUrl.startsWith('http')) {
        return data.displayUrl;
      }
      
      if (data.images && Array.isArray(data.images) && data.images.length > 0) {
        const firstImage = data.images[0];
        if (typeof firstImage === 'string' && firstImage.startsWith('http')) {
          return firstImage;
        }
      }
      
      if (data.childPosts && Array.isArray(data.childPosts) && data.childPosts.length > 0) {
        const firstChild = data.childPosts[0];
        if (firstChild.displayUrl && typeof firstChild.displayUrl === 'string' && firstChild.displayUrl.startsWith('http')) {
          return firstChild.displayUrl;
        }
      }
    }
    
    return null;
  };

  const getPostUrl = (post: SavedPost | ScrapedPost): string | null => {
    // Handle flat structure
    if ('url' in post && post.url && typeof post.url === 'string') {
      if (post.url.includes('instagram.com/p/') || post.url.includes('instagram.com/reel/')) {
        return post.url;
      }
    }
    
    if ('short_code' in post && post.short_code && typeof post.short_code === 'string') {
      return `https://www.instagram.com/p/${post.short_code}/`;
    }
    
    // Handle nested structure
    if ('post_data' in post && post.post_data) {
      const scrapedPost = post.post_data;
      const data = scrapedPost.structured_data || scrapedPost.raw_data || {};
      
      const postUrlFields = ['postUrl', 'post_url', 'shortCode', 'short_code', 'permalink', 'link'];
      
      for (const field of postUrlFields) {
        if (data[field] && typeof data[field] === 'string') {
          if ((field === 'shortCode' || field === 'short_code') && !data[field].startsWith('http')) {
            return `https://www.instagram.com/p/${data[field]}/`;
          }
          if (data[field].startsWith('http')) {
            return data[field];
          }
        }
      }
      
      if (data.url && typeof data.url === 'string') {
        if (data.url.includes('instagram.com/p/') || data.url.includes('instagram.com/reel/')) {
          return data.url;
        }
        if (!data.url.match(/\.(jpg|jpeg|png|gif|webp|mp4|mov)/i)) {
          return data.url;
        }
      }
    }
    
    return null;
  };

  const getPostCaption = (post: SavedPost | ScrapedPost): string => {
    // Handle flat structure
    if ('caption' in post && post.caption && typeof post.caption === 'string') {
      return post.caption;
    }
    
    // Handle nested structure
    if ('post_data' in post && post.post_data) {
      const scrapedPost = post.post_data;
      if (scrapedPost.structured_data?.caption) return scrapedPost.structured_data.caption;
      if (scrapedPost.raw_data?.caption) return scrapedPost.raw_data.caption;
      if (scrapedPost.structured_data?.text) return scrapedPost.structured_data.text;
    }
    
    return "No caption available";
  };

  const getPostOwner = (post: SavedPost | ScrapedPost): { username?: string; fullName?: string } | null => {
    // Handle flat structure
    if ('owner_username' in post || 'owner_full_name' in post) {
      const username = post.owner_username;
      const fullName = post.owner_full_name;
      if (!username && !fullName) return null;
      return { username, fullName };
    }
    
    // Handle nested structure
    if ('post_data' in post && post.post_data) {
      const scrapedPost = post.post_data;
      const data = scrapedPost.structured_data || scrapedPost.raw_data || {};
      const username = data.ownerUsername || data.owner_username || data.username || data.owner?.username;
      const fullName = data.ownerFullName || data.owner_full_name || data.fullName || data.owner?.fullName;
      if (!username && !fullName) return null;
      return { username, fullName };
    }
    
    return null;
  };

  const getPostStats = (post: SavedPost | ScrapedPost): { likes: number | null; comments: number | null } => {
    const parseCount = (value: any): number | null => {
      if (typeof value === "number" && !Number.isNaN(value) && value >= 0) return value;
      if (typeof value === "string") {
        const parsed = parseInt(value.replace(/[^0-9]/g, ""), 10);
        if (!Number.isNaN(parsed) && parsed >= 0) return parsed;
      }
      return null;
    };
    
    // Handle flat structure
    if ('likes_count' in post || 'comments_count' in post) {
      return {
        likes: parseCount(post.likes_count),
        comments: parseCount(post.comments_count)
      };
    }
    
    // Handle nested structure
    if ('post_data' in post && post.post_data) {
      const scrapedPost = post.post_data;
      const data = scrapedPost.structured_data || scrapedPost.raw_data || {};
      const likeCandidates = [data.likesCount, data.likeCount, data.likes, data.edge_liked_by?.count];
      const commentCandidates = [data.commentsCount, data.commentCount, data.comments, data.edge_media_to_comment?.count];
      
      const parseCountArray = (values: any[]): number | null => {
        for (const value of values) {
          const result = parseCount(value);
          if (result !== null) return result;
        }
        return null;
      };
      
      return { likes: parseCountArray(likeCandidates), comments: parseCountArray(commentCandidates) };
    }
    
    return { likes: null, comments: null };
  };

  const getPostHashtags = (post: SavedPost | ScrapedPost): string[] => {
    // Handle flat structure
    if ('hashtags' in post && Array.isArray(post.hashtags)) {
      return post.hashtags.filter((tag: any) => typeof tag === "string").slice(0, 12);
    }
    
    // Handle nested structure
    if ('post_data' in post && post.post_data) {
      const scrapedPost = post.post_data;
      const data = scrapedPost.structured_data || scrapedPost.raw_data || {};
      let hashtags: string[] = [];
      if (Array.isArray(data.hashtags)) {
        hashtags = data.hashtags.filter((tag: any) => typeof tag === "string");
      }
      if (hashtags.length === 0) {
        const caption = getPostCaption(post);
        const matches = caption.match(/#(\w+)/g);
        if (matches) hashtags = matches.map((tag) => tag.replace("#", ""));
      }
      return Array.from(new Set(hashtags)).slice(0, 12);
    }
    
    return [];
  };

  const getPostComments = (post: SavedPost | ScrapedPost): Array<{ username?: string; text: string }> => {
    const comments: Array<{ username?: string; text: string }> = [];
    
    // Handle nested structure
    if ('post_data' in post && post.post_data) {
      const scrapedPost = post.post_data;
      const data = scrapedPost.structured_data || scrapedPost.raw_data || {};
      
      if (data.firstComment && typeof data.firstComment === "string" && data.firstComment.trim()) {
        comments.push({ text: data.firstComment });
      }
      
      if (Array.isArray(data.latestComments) && data.latestComments.length > 0) {
        for (const comment of data.latestComments) {
          if (typeof comment === "string" && comment.trim()) {
            comments.push({ text: comment });
          } else if (typeof comment === "object" && comment !== null) {
            const commentText = comment.text || comment.comment || comment.content || "";
            const commentUsername = comment.username || comment.ownerUsername;
            if (commentText.trim()) {
              comments.push({ username: commentUsername, text: commentText });
            }
          }
        }
      }
    }
    
    return Array.from(new Map(comments.map(c => [c.text, c])).values()).slice(0, 10);
  };

  const handleCardClick = async (postId: string) => {
    setSelectedPostId(postId);
    setExtractedItems([]);
    setExtractedItemsWithMatches(new Map());
    
    // Fetch extracted items for this post
    setExtractedItemsLoading(true);
    try {
      const response = await getExtractedItemsForPost(postId);
      setExtractedItems(response.items || []);
      
      // Fetch similar products for each extracted item
      const matchesMap = new Map<string, SimilarProduct[]>();
      for (const item of response.items || []) {
        try {
          const itemResponse = await getExtractedItemWithMatches(item.id);
          if (itemResponse.matched_products && itemResponse.matched_products.length > 0) {
            // Get top 5 similar products
            const top5 = itemResponse.matched_products
              .sort((a, b) => b.similarity_score - a.similarity_score)
              .slice(0, 5);
            matchesMap.set(item.id, top5);
          }
        } catch (err) {
          console.error(`Error fetching matches for item ${item.id}:`, err);
        }
      }
      setExtractedItemsWithMatches(matchesMap);
    } catch (err: any) {
      console.error(`Error fetching extracted items for post ${postId}:`, err);
      setExtractedItems([]);
    } finally {
      setExtractedItemsLoading(false);
    }
  };

  const handleCloseModal = () => {
    setSelectedPostId(null);
    setExtractedItems([]);
    setExtractedItemsWithMatches(new Map());
  };

  const handleOpenInstagram = (postUrl?: string | null) => {
    if (!postUrl) return;
    window.open(postUrl, "_blank", "noopener,noreferrer");
  };

  const handleDeleteClick = (postId: string) => {
    setPostToDelete(postId);
    setShowDeleteConfirm(true);
  };

  const handleDeleteConfirm = async () => {
    if (!postToDelete) return;

    setDeleting(true);
    setShowDeleteConfirm(false);
    
    try {
      await deletePost(postToDelete, true);
      // Remove the post from the list
      setPosts(posts.filter(p => p.id !== postToDelete));
      // Close the modal
      handleCloseModal();
      // Reload posts to refresh the list
      await loadPosts();
    } catch (err: any) {
      console.error(`Error deleting post ${postToDelete}:`, err);
      alert(`Failed to delete post: ${err.message}`);
    } finally {
      setDeleting(false);
      setPostToDelete(null);
    }
  };

  const handleDeleteCancel = () => {
    setShowDeleteConfirm(false);
    setPostToDelete(null);
  };

  const totalPages = Math.ceil(totalPosts / postsPerPage);
  
  // Get selected post data for modal
  const selectedPost = selectedPostId ? posts.find(p => p.id === selectedPostId) : null;
  
  // Compute modal data if post is selected
  const modalData = selectedPost ? {
    imageUrl: getPostImage(selectedPost),
    postUrl: getPostUrl(selectedPost),
    caption: getPostCaption(selectedPost),
    owner: getPostOwner(selectedPost),
    stats: getPostStats(selectedPost),
    hashtags: getPostHashtags(selectedPost),
    comments: getPostComments(selectedPost),
    scrapedDate: selectedPost.scraped_at || selectedPost.scraped_date || new Date().toISOString(),
  } : null;

  if (loading && posts.length === 0) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="text-center">
          <Loader2 className="h-12 w-12 animate-spin mx-auto text-primary" />
          <p className="mt-4 text-muted-foreground">Loading posts...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Scraped Posts</h1>
          <p className="mt-2 text-muted-foreground">
            View all saved scraped posts from Instagram and Pinterest
          </p>
          {totalPosts > 0 && (
            <p className="mt-1 text-sm text-muted-foreground">
              Total: {totalPosts} posts
            </p>
          )}
        </div>
        <button
          onClick={loadPosts}
          disabled={loading}
          className="flex items-center gap-2 px-4 py-2 border rounded-md hover:bg-accent transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
          <span>Refresh</span>
        </button>
      </div>

      {error && (
        <div className="p-4 border border-destructive rounded-lg bg-destructive/10">
          <p className="text-destructive">{error}</p>
        </div>
      )}

      {posts.length === 0 && !loading ? (
        <div className="text-center py-16">
          <FileText className="h-16 w-16 text-muted-foreground mx-auto mb-4" />
          <p className="text-lg text-muted-foreground">No saved posts found</p>
          <p className="text-sm text-muted-foreground mt-2">
            Scrape some posts with "Save to database" enabled to see them here
          </p>
        </div>
      ) : (
        <>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {posts
              .filter((savedPost) => {
                // Filter out posts without image data (either flat or nested)
                const hasImage = savedPost.display_url || 
                                 (Array.isArray(savedPost.images) && savedPost.images.length > 0) ||
                                 (savedPost.post_data && (savedPost.post_data.structured_data || savedPost.post_data.raw_data));
                if (!hasImage) {
                  console.warn(`[Posts Page] No image data for post ${savedPost.id}:`, savedPost);
                  return false;
                }
                return true;
              })
              .map((savedPost, index) => {
              try {
                // Handle both flat and nested structures
                const imageUrl = getPostImage(savedPost);
                const postUrl = getPostUrl(savedPost);
                const caption = getPostCaption(savedPost);
                const owner = getPostOwner(savedPost);
                const stats = getPostStats(savedPost);
                const hashtags = getPostHashtags(savedPost);
                const comments = getPostComments(savedPost);
                
                // Get scraped date
                const scrapedDate = savedPost.scraped_at || savedPost.scraped_date || new Date().toISOString();

                // Debug logging
                if (!imageUrl) {
                  console.warn(`[Posts Page] No image URL found for post ${savedPost.id}:`, savedPost);
                } else {
                  console.log(`[Posts Page] Found image URL for post ${savedPost.id}:`, imageUrl);
                }

              return (
                <div
                  key={savedPost.id}
                  role="button"
                  tabIndex={0}
                  onClick={() => handleCardClick(savedPost.id)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" || e.key === " ") {
                      e.preventDefault();
                      handleCardClick(savedPost.id);
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
                        onError={(e) => {
                          console.error(`[Posts Page] Failed to load image for post ${savedPost.id}:`, {
                            originalUrl: imageUrl,
                            proxiedUrl: getProxiedImageUrl(imageUrl),
                            error: e
                          });
                          const target = e.target as HTMLImageElement;
                          target.style.display = 'none';
                          // Show fallback
                          const parent = target.parentElement;
                          if (parent) {
                            const fallback = document.createElement('div');
                            fallback.className = 'flex h-full w-full flex-col items-center justify-center gap-3 p-4 text-muted-foreground';
                            fallback.innerHTML = `
                              <svg class="h-10 w-10" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                              </svg>
                              <p class="text-xs text-center">Image failed to load</p>
                            `;
                            parent.appendChild(fallback);
                          }
                        }}
                        onLoad={() => {
                          console.log(`[Posts Page] Successfully loaded image for post ${savedPost.id}`);
                        }}
                      />
                    ) : (
                      <div className="flex h-full w-full flex-col items-center justify-center gap-3 p-4 text-muted-foreground">
                        <Instagram className="h-10 w-10" />
                        <p className="text-xs text-center">No image found</p>
                      </div>
                    )}
                    <div className="absolute inset-0 bg-black/0 group-hover:bg-black/10 transition-colors flex items-center justify-center pointer-events-none">
                      <div className="opacity-0 group-hover:opacity-100 transition-opacity inline-flex items-center gap-2 rounded-full bg-black/70 px-4 py-2 text-sm text-white pointer-events-auto">
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
                        <span>{new Date(scrapedDate).toLocaleDateString()}</span>
                      </span>
                    </div>
                  </div>
                </div>
              );
              } catch (err) {
                console.error(`[Posts Page] Error rendering post ${savedPost.id}:`, err);
                return (
                  <div
                    key={savedPost.id}
                    className="p-4 border border-destructive rounded-lg bg-destructive/10"
                  >
                    <p className="text-destructive text-sm">Error loading post data</p>
                  </div>
                );
              }
            })}
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-center gap-2 mt-8">
              <button
                onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
                disabled={currentPage === 1}
                className="px-4 py-2 border rounded-md disabled:opacity-50 disabled:cursor-not-allowed hover:bg-accent"
              >
                Previous
              </button>
              <span className="px-4 py-2 text-sm text-muted-foreground">
                Page {currentPage} of {totalPages}
              </span>
              <button
                onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
                disabled={currentPage === totalPages}
                className="px-4 py-2 border rounded-md disabled:opacity-50 disabled:cursor-not-allowed hover:bg-accent"
              >
                Next
              </button>
            </div>
          )}
        </>
      )}

      {/* Post Detail Modal */}
      {selectedPost && modalData && (
        <div
          key={selectedPost.id}
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 p-4"
          onClick={handleCloseModal}
        >
          <div
            className="relative flex h-full max-h-[90vh] w-full max-w-6xl flex-col overflow-hidden rounded-lg bg-background shadow-2xl md:flex-row"
            onClick={(e) => e.stopPropagation()}
          >
            <button
              onClick={handleCloseModal}
              className="absolute top-4 right-4 z-10 rounded-full bg-black/50 p-2 text-white transition-colors hover:bg-black/70"
            >
              <X className="h-5 w-5" />
            </button>

            <div className="flex h-full w-full items-center justify-center bg-muted md:w-1/2">
              {modalData.imageUrl ? (
                <img
                  src={getProxiedImageUrl(modalData.imageUrl)}
                  alt={`Post ${selectedPost.id}`}
                  className="max-h-full w-full object-contain"
                />
              ) : (
                <div className="flex flex-col items-center justify-center gap-4 p-8 text-muted-foreground">
                  <Instagram className="h-16 w-16" />
                  <p className="text-sm">No image available</p>
                </div>
              )}
            </div>

            <div className="flex h-full w-full flex-col gap-6 overflow-y-auto p-6 md:w-1/2">
              <div className="space-y-2 border-b pb-4">
                <h2 className="text-2xl font-bold">Extracted Items</h2>
                <p className="text-sm text-muted-foreground">
                  Fashion items extracted from this post
                </p>
              </div>

              {extractedItemsLoading ? (
                <div className="flex items-center justify-center py-12">
                  <Loader2 className="h-8 w-8 animate-spin text-primary" />
                  <span className="ml-3 text-muted-foreground">Loading extracted items...</span>
                </div>
              ) : extractedItems.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-12 text-center">
                  <Package className="h-12 w-12 text-muted-foreground mb-4" />
                  <p className="text-lg font-medium text-foreground">No items extracted yet</p>
                  <p className="text-sm text-muted-foreground mt-2">
                    Extract items from this post to see similar products
                  </p>
                </div>
              ) : (
                <div className="space-y-8">
                  {extractedItems.map((item) => {
                    const similarProducts = extractedItemsWithMatches.get(item.id) || [];
                    
                    return (
                      <div key={item.id} className="space-y-4 border-b pb-6 last:border-b-0">
                        {/* Extracted Item Info */}
                        <div className="space-y-3">
                          {/* Extracted Item Image - Use post image or first similar product image */}
                          <div className="relative w-full h-48 rounded-lg overflow-hidden bg-muted">
                            {(() => {
                              // Try to get image from first similar product
                              const firstProduct = similarProducts[0];
                              if (firstProduct?.product_info?.image_url) {
                                return (
                                  <img
                                    src={getProxiedImageUrl(firstProduct.product_info.image_url)}
                                    alt={item.item_name || item.category}
                                    className="w-full h-full object-cover"
                                  />
                                );
                              }
                              // Fallback to post image
                              if (modalData.imageUrl) {
                                return (
                                  <img
                                    src={getProxiedImageUrl(modalData.imageUrl)}
                                    alt={item.item_name || item.category}
                                    className="w-full h-full object-cover"
                                  />
                                );
                              }
                              return (
                                <div className="w-full h-full flex items-center justify-center">
                                  <Package className="h-12 w-12 text-muted-foreground" />
                                </div>
                              );
                            })()}
                          </div>
                          
                          <div className="flex items-center justify-between">
                            <h3 className="text-lg font-semibold text-foreground">
                              {item.item_name || item.category}
                            </h3>
                            {item.extraction_confidence && (
                              <span className="text-xs px-2 py-1 rounded-full bg-primary/10 text-primary">
                                {Math.round(item.extraction_confidence * 100)}% confidence
                              </span>
                            )}
                          </div>
                          
                          <div className="flex flex-wrap gap-2 text-sm text-muted-foreground">
                            {item.category && (
                              <span className="px-2 py-1 rounded bg-muted">
                                {item.category}
                              </span>
                            )}
                            {item.subcategory && (
                              <span className="px-2 py-1 rounded bg-muted">
                                {item.subcategory}
                              </span>
                            )}
                            {item.brand && (
                              <span className="px-2 py-1 rounded bg-muted">
                                {item.brand}
                              </span>
                            )}
                          </div>
                          
                          {item.colors && item.colors.length > 0 && (
                            <div className="flex items-center gap-2">
                              <span className="text-xs text-muted-foreground">Colors:</span>
                              <div className="flex gap-1">
                                {item.colors.map((color, idx) => (
                                  <span
                                    key={idx}
                                    className="px-2 py-0.5 rounded text-xs bg-muted"
                                  >
                                    {color}
                                  </span>
                                ))}
                              </div>
                            </div>
                          )}
                        </div>

                        {/* Similar Products */}
                        {similarProducts.length > 0 ? (
                          <div className="space-y-3">
                            <div className="flex items-center gap-2">
                              <TrendingUp className="h-4 w-4 text-primary" />
                              <h4 className="text-sm font-semibold text-foreground">
                                Similar Products ({similarProducts.length})
                              </h4>
                            </div>
                            
                            <div className="grid grid-cols-1 gap-3">
                              {similarProducts.map((product) => {
                                const matchPercentage = Math.round(product.similarity_score * 100);
                                
                                return (
                                  <div
                                    key={product.product_id}
                                    className="flex items-center gap-3 p-3 rounded-lg border bg-card hover:bg-accent/50 transition-colors"
                                  >
                                    {product.product_info.image_url ? (
                                      <img
                                        src={getProxiedImageUrl(product.product_info.image_url)}
                                        alt={product.product_info.name}
                                        className="w-16 h-16 object-cover rounded"
                                      />
                                    ) : (
                                      <div className="w-16 h-16 bg-muted rounded flex items-center justify-center">
                                        <Package className="h-6 w-6 text-muted-foreground" />
                                      </div>
                                    )}
                                    
                                    <div className="flex-1 min-w-0">
                                      <p className="font-medium text-sm text-foreground truncate">
                                        {product.product_info.name}
                                      </p>
                                      {product.product_info.brand && (
                                        <p className="text-xs text-muted-foreground">
                                          {product.product_info.brand}
                                        </p>
                                      )}
                                      <p className="text-sm font-semibold text-primary mt-1">
                                        {product.product_info.currency} {product.product_info.price.toLocaleString()}
                                      </p>
                                    </div>
                                    
                                    <div className="flex flex-col items-end gap-1">
                                      <div className="flex items-center gap-1">
                                        <span className="text-lg font-bold text-primary">
                                          {matchPercentage}%
                                        </span>
                                        <TrendingUp className="h-4 w-4 text-primary" />
                                      </div>
                                      <span className="text-xs text-muted-foreground">Match</span>
                                    </div>
                                  </div>
                                );
                              })}
                            </div>
                          </div>
                        ) : (
                          <div className="text-sm text-muted-foreground">
                            No similar products found
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              )}

              <div className="mt-auto flex gap-3">
                {modalData.postUrl && (
                  <button
                    onClick={() => handleOpenInstagram(modalData.postUrl)}
                    className="flex-1 flex items-center justify-center gap-2 rounded-lg bg-primary px-6 py-3 font-medium text-primary-foreground transition-colors hover:bg-primary/90"
                  >
                    <ExternalLink className="h-5 w-5" />
                    <span>View on Instagram</span>
                  </button>
                )}
                <button
                  onClick={() => selectedPost && handleDeleteClick(selectedPost.id)}
                  disabled={deleting}
                  className="flex items-center justify-center gap-2 rounded-lg border border-destructive px-6 py-3 font-medium text-destructive transition-colors hover:bg-destructive/10 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {deleting ? (
                    <Loader2 className="h-5 w-5 animate-spin" />
                  ) : (
                    <Trash2 className="h-5 w-5" />
                  )}
                  <span>{deleting ? 'Deleting...' : 'Delete Post'}</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Delete Confirmation Dialog */}
      {showDeleteConfirm && (
        <div
          className="fixed inset-0 z-[60] flex items-center justify-center bg-black/60 p-4"
          onClick={handleDeleteCancel}
        >
          <div
            className="relative w-full max-w-md rounded-lg bg-background shadow-2xl border border-border"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Close Button */}
            <button
              onClick={handleDeleteCancel}
              className="absolute top-4 right-4 rounded-full bg-muted p-1.5 text-muted-foreground transition-colors hover:bg-muted/80 focus:outline-none focus:ring-2 focus:ring-primary"
              aria-label="Close"
            >
              <X className="h-4 w-4" />
            </button>

            {/* Content */}
            <div className="p-6">
              <div className="flex items-center gap-4 mb-4">
                <div className="flex h-12 w-12 items-center justify-center rounded-full bg-destructive/10">
                  <Trash2 className="h-6 w-6 text-destructive" />
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-foreground">Delete Post</h3>
                  <p className="text-sm text-muted-foreground">This action cannot be undone</p>
                </div>
              </div>

              <p className="text-sm text-foreground mb-6">
                Are you sure you want to delete this post? This will also delete all extracted items for this post.
              </p>

              {/* Actions */}
              <div className="flex gap-3 justify-end">
                <button
                  onClick={handleDeleteCancel}
                  disabled={deleting}
                  className="px-4 py-2 rounded-lg border border-border bg-background text-foreground font-medium transition-colors hover:bg-accent disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Cancel
                </button>
                <button
                  onClick={handleDeleteConfirm}
                  disabled={deleting}
                  className="px-4 py-2 rounded-lg bg-destructive text-destructive-foreground font-medium transition-colors hover:bg-destructive/90 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                >
                  {deleting ? (
                    <>
                      <Loader2 className="h-4 w-4 animate-spin" />
                      <span>Deleting...</span>
                    </>
                  ) : (
                    <span>Delete</span>
                  )}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

