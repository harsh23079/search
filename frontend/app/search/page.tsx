import { SearchInterface } from "@/components/search-interface";

export default function SearchPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">AI Fashion Assistant</h1>
        <p className="mt-2 text-muted-foreground">
          Chat with our AI to find the perfect fashion items. Describe what you want or show us an image!
        </p>
      </div>
      <SearchInterface />
    </div>
  );
}