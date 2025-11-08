import { InstagramScraper } from "@/components/instagram-scraper";

export default function ScrapePage() {
  return (
    <div className="flex h-full flex-col overflow-hidden">
      <div className="mb-6 shrink-0">
        <h1 className="text-3xl font-bold">Instagram Scraper</h1>
        <p className="mt-2 text-muted-foreground">
          Scrape posts from Instagram profiles and hashtags
        </p>
      </div>
      <div className="flex-1 min-h-0 overflow-hidden">
        <InstagramScraper />
      </div>
    </div>
  );
}

