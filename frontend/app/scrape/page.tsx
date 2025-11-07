import { InstagramScraper } from "@/components/instagram-scraper";

export default function ScrapePage() {
  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold">Instagram Scraper</h1>
        <p className="mt-2 text-muted-foreground">
          Scrape posts from Instagram profiles and hashtags
        </p>
      </div>
      <InstagramScraper />
    </div>
  );
}

