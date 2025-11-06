import { ExploreFeed } from "@/components/explore-feed";

export default function HomePage() {
  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold">Explore Feed</h1>
        <p className="mt-2 text-muted-foreground">
          Discover fashion items and find your perfect style
        </p>
      </div>
      <ExploreFeed />
    </div>
  );
}

