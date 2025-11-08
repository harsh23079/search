"use client";

import { useState, useEffect } from "react";
import { 
  getSavedPosts, SavedPost, getProxiedImageUrl,
  deletePost, searchSimilarImage
} from "@/lib/api";
import { Product } from "@/types/product";
import { Loader2, Instagram, Calendar, User, Heart, MessageCircle, ExternalLink, X, FileText, RefreshCw, Trash2, Search, Package } from "lucide-react";
import { ScrapedPost } from "@/lib/api";
import { ProductCard } from "@/components/product-card";

export default function PostsPage() {
  const [posts, setPosts] = useState<SavedPost[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedPostId, setSelectedPostId] = useState<string | null>(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPosts, setTotalPosts] = useState(0);
  const postsPerPage = 20;
  
  const [deleting, setDeleting] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [postToDelete, setPostToDelete] = useState<string | null>(null);
  
  // Search similar products state
  const [searchingSimilar, setSearchingSimilar] = useState(false);
  const [similarProducts, setSimilarProducts] = useState<Product[]>([]);
  const [showSimilarModal, setShowSimilarModal] = useState(false);
  const [searchError, setSearchError] = useState<string | null>(null);

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
  };

  const handleCloseModal = () => {
    setSelectedPostId(null);
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

  const handleFindSimilar = async (e: React.MouseEvent, post: SavedPost) => {
    e.stopPropagation(); // Prevent card click
    
    console.log('═══════════════════════════════════════════════════════════');
    console.log('[Find Similar] 🚀 STARTING: Button clicked for post:', post.id);
    console.log('═══════════════════════════════════════════════════════════');
    
    setSearchingSimilar(true);
    setSearchError(null);
    setSimilarProducts([]);
    
    try {
      // Step 1: Get image URL
      const imageUrl = getPostImage(post);
      console.log('[Find Similar] Step 1: Image URL extracted:', imageUrl);
      
      if (!imageUrl) {
        console.error('[Find Similar] ❌ ERROR: No image URL found for post');
        setSearchError("No image available for this post");
        setSearchingSimilar(false);
        return;
      }

      // Step 2: Get proxied URL
      const proxiedUrl = getProxiedImageUrl(imageUrl);
      console.log('[Find Similar] Step 2: Proxied URL:', proxiedUrl);
      console.log('[Find Similar] Step 3: Fetching image from proxy...');

      // Step 3: Fetch the image as Blob
      const response = await fetch(proxiedUrl, { mode: "cors" });
      console.log('[Find Similar] Step 3: Fetch response:', {
        status: response.status,
        statusText: response.statusText,
        ok: response.ok,
        contentType: response.headers.get('content-type')
      });
      
      if (!response.ok) {
        throw new Error(`Failed to fetch image: ${response.status} ${response.statusText}`);
      }
      
      // Step 4: Convert to Blob
      const blob = await response.blob();
      console.log('[Find Similar] Step 4: Blob created:', {
        size: blob.size,
        type: blob.type,
        sizeKB: (blob.size / 1024).toFixed(2) + ' KB'
      });
      
      // Step 5: Create File from Blob (same as search-interface.tsx)
      const file = new File([blob], `post-${post.id}.jpg`, { type: blob.type });
      console.log('[Find Similar] Step 5: File created:', {
        name: file.name,
        size: file.size,
        type: file.type,
        sizeKB: (file.size / 1024).toFixed(2) + ' KB'
      });

      // Step 6: Call searchSimilarImage API (same as search-interface.tsx)
      console.log('[Find Similar] Step 6: Calling searchSimilarImage() API...');
      console.log('[Find Similar] File details (same as search-interface.tsx):', {
        name: file.name,
        size: file.size,
        type: file.type,
        isFile: file instanceof File,
        isBlob: file instanceof Blob
      });
      
      const results = await searchSimilarImage(file, 20);
      
      console.log('═══════════════════════════════════════════════════════════');
      console.log('[Find Similar] ✅ SEARCH SUCCESS! Results:', results.length);
      console.log('═══════════════════════════════════════════════════════════');
      
      setSimilarProducts(results);
      setShowSimilarModal(true);
    } catch (err) {
      console.error('[Find Similar] ❌ ERROR:', err);
      console.error('[Find Similar] Error details:', {
        message: err instanceof Error ? err.message : 'Unknown error',
        stack: err instanceof Error ? err.stack : undefined
      });
      const errorMessage = err instanceof Error ? err.message : 'Failed to search for similar products';
      setSearchError(errorMessage);
    } finally {
      setSearchingSimilar(false);
    }
  };

  const handleCloseSimilarModal = () => {
    setShowSimilarModal(false);
    setSimilarProducts([]);
    setSearchError(null);
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
    <div className="flex h-full flex-col overflow-hidden">
      {/* Header Section - Fixed */}
      <div className="flex items-center justify-between shrink-0 mb-6">
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

      {/* Error Message - Fixed */}
      {error && (
        <div className="p-4 border border-destructive rounded-lg bg-destructive/10 shrink-0 mb-4">
          <p className="text-destructive">{error}</p>
        </div>
      )}

      {/* Scrollable Content Area */}
      <div className="flex-1 overflow-y-auto min-h-0">
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
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 pb-4">
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
                    <div className="absolute inset-0 bg-black/0 group-hover:bg-black/10 transition-colors flex flex-col items-center justify-center gap-2 pointer-events-none">
                      <div className="opacity-0 group-hover:opacity-100 transition-opacity flex flex-col items-center gap-2 pointer-events-auto">
                        {/* Find Similar Button */}
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            handleFindSimilar(e, savedPost);
                          }}
                          disabled={searchingSimilar}
                          className="flex items-center gap-2 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground shadow-lg transition-all hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed"
                          title="Find similar products"
                        >
                          {searchingSimilar ? (
                            <Loader2 className="h-4 w-4 animate-spin" />
                          ) : (
                            <Search className="h-4 w-4" />
                          )}
                          <span>{searchingSimilar ? 'Searching...' : 'Find Similar'}</span>
                        </button>
                        {/* Delete Button */}
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            handleDeleteClick(savedPost.id);
                          }}
                          disabled={deleting}
                          className="flex items-center gap-2 rounded-lg bg-destructive/90 px-4 py-2 text-sm font-medium text-destructive-foreground shadow-lg transition-all hover:bg-destructive disabled:opacity-50 disabled:cursor-not-allowed"
                          title="Delete post"
                        >
                          {deleting ? (
                            <Loader2 className="h-4 w-4 animate-spin" />
                          ) : (
                            <Trash2 className="h-4 w-4" />
                          )}
                          <span>{deleting ? 'Deleting...' : 'Delete'}</span>
                        </button>
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
              <div className="flex items-center justify-center gap-2 mt-8 mb-4">
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
      </div>

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
              <div className="space-y-4">
                {/* Post Caption */}
                {modalData.caption && (
                  <div className="space-y-2">
                    <h2 className="text-xl font-bold">Caption</h2>
                    <p className="text-sm text-foreground whitespace-pre-wrap">{modalData.caption}</p>
                  </div>
                )}

                {/* Post Stats */}
                {(modalData.stats.likes !== null || modalData.stats.comments !== null) && (
                  <div className="flex items-center gap-6 text-sm">
                    {modalData.stats.likes !== null && (
                      <div className="flex items-center gap-2">
                        <Heart className="h-4 w-4 text-muted-foreground" />
                        <span className="text-muted-foreground">{modalData.stats.likes.toLocaleString()} likes</span>
                      </div>
                    )}
                    {modalData.stats.comments !== null && (
                      <div className="flex items-center gap-2">
                        <MessageCircle className="h-4 w-4 text-muted-foreground" />
                        <span className="text-muted-foreground">{modalData.stats.comments.toLocaleString()} comments</span>
                      </div>
                    )}
                  </div>
                )}

                {/* Owner Info */}
                {modalData.owner?.username && (
                  <div className="flex items-center gap-2">
                    <User className="h-4 w-4 text-muted-foreground" />
                    <span className="text-sm text-foreground">@{modalData.owner.username}</span>
                    {modalData.owner.fullName && (
                      <span className="text-sm text-muted-foreground">({modalData.owner.fullName})</span>
                    )}
                  </div>
                )}

                {/* Hashtags */}
                {modalData.hashtags && modalData.hashtags.length > 0 && (
                  <div className="space-y-2">
                    <h3 className="text-sm font-semibold text-foreground">Hashtags</h3>
                    <div className="flex flex-wrap gap-2">
                      {modalData.hashtags.map((tag, idx) => (
                        <span
                          key={idx}
                          className="px-2 py-1 rounded bg-muted text-xs text-muted-foreground"
                        >
                          #{tag}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {/* Comments */}
                {modalData.comments && modalData.comments.length > 0 && (
                  <div className="space-y-2">
                    <h3 className="text-sm font-semibold text-foreground">Comments</h3>
                    <div className="space-y-2 max-h-48 overflow-y-auto">
                      {modalData.comments.slice(0, 5).map((comment, idx) => (
                        <div key={idx} className="text-xs text-muted-foreground">
                          {comment.username && <span className="font-medium">@{comment.username}: </span>}
                          <span>{comment.text}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              <div className="mt-auto flex gap-3">
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    if (selectedPost) {
                      handleFindSimilar(e, selectedPost);
                    }
                  }}
                  disabled={searchingSimilar}
                  className="flex-1 flex items-center justify-center gap-2 rounded-lg bg-primary px-6 py-3 font-medium text-primary-foreground transition-colors hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {searchingSimilar ? (
                    <Loader2 className="h-5 w-5 animate-spin" />
                  ) : (
                    <Search className="h-5 w-5" />
                  )}
                  <span>{searchingSimilar ? 'Searching...' : 'Find Similar'}</span>
                </button>
                {modalData.postUrl && (
                  <button
                    onClick={() => handleOpenInstagram(modalData.postUrl)}
                    className="flex items-center justify-center gap-2 rounded-lg border border-border px-6 py-3 font-medium text-foreground transition-colors hover:bg-accent"
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
                Do you really want to delete this post? This action cannot be undone.
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

      {/* Similar Products Modal */}
      {showSimilarModal && (
        <div
          className="fixed inset-0 z-[70] flex items-center justify-center bg-black/80 p-4"
          onClick={handleCloseSimilarModal}
        >
          <div
            className="relative w-full max-w-6xl max-h-[90vh] rounded-lg bg-background shadow-2xl border border-border overflow-hidden flex flex-col"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Header */}
            <div className="flex items-center justify-between p-6 border-b">
              <div>
                <h2 className="text-2xl font-bold">Similar Products</h2>
                <p className="text-sm text-muted-foreground mt-1">
                  Found {similarProducts.length} similar products
                </p>
              </div>
              <button
                onClick={handleCloseSimilarModal}
                className="rounded-full bg-muted p-2 text-muted-foreground transition-colors hover:bg-muted/80"
                aria-label="Close"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            {/* Content */}
            <div className="flex-1 overflow-y-auto p-6">
              {searchError ? (
                <div className="flex flex-col items-center justify-center py-12 text-center">
                  <X className="h-12 w-12 text-destructive mb-4" />
                  <p className="text-lg font-medium text-foreground">Search Error</p>
                  <p className="text-sm text-muted-foreground mt-2">{searchError}</p>
                  <button
                    onClick={handleCloseSimilarModal}
                    className="mt-4 px-4 py-2 rounded-lg bg-primary text-primary-foreground hover:bg-primary/90"
                  >
                    Close
                  </button>
                </div>
              ) : similarProducts.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-12 text-center">
                  <Package className="h-12 w-12 text-muted-foreground mb-4" />
                  <p className="text-lg font-medium text-foreground">No similar products found</p>
                  <p className="text-sm text-muted-foreground mt-2">
                    Try searching with a different image
                  </p>
                </div>
              ) : (
                <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
                  {similarProducts.map((product) => (
                    <ProductCard key={product.id} product={product} />
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

