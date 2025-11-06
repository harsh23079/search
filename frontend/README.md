# Fashion-AI Search Frontend

A modern Next.js frontend for multimodal fashion search, inspired by the Next.js Commerce template from Vercel.

## Project Overview

This project provides a polished, production-ready frontend for exploring and searching fashion items using both text queries and image similarity search. The architecture and design system are inspired by the [Next.js Commerce](https://github.com/vercel/commerce) template, adapted for multimodal search capabilities.

**Project scaffold inspired by Next.js Commerce template (Vercel) — adapted for multimodal search**

## Features

- 🎨 **Explore Feed**: Browse fashion items in a beautiful grid layout
- 🔍 **Text Search**: Search for products using natural language queries
- 🖼️ **Image Search**: Upload images to find visually similar products
- 🌓 **Dark Mode**: Full light/dark theme support with smooth transitions
- 📱 **Responsive Design**: Optimized for mobile, tablet, and desktop
- ⚡ **Fast & Modern**: Built with Next.js 14 App Router and TypeScript

## Tech Stack

- **Next.js 14** (App Router)
- **TypeScript**
- **Tailwind CSS** (with Commerce-inspired design system)
- **next-themes** (dark mode)
- **lucide-react** (icons)

## Prerequisites

- [devenv](https://devenv.sh/) installed
- Backend API running on `http://localhost:8000`

## Setup

### 1. Install Dependencies

```bash
devenv shell
pnpm install
```

### 2. Environment Variables

Create a `.env.local` file (already included with defaults):

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_API_BASE_PATH=/api/v1
```

### 3. Start Development Server

```bash
# In devenv shell
pnpm dev
```

Or use devenv to run all services:

```bash
devenv up
```

The application will be available at `http://localhost:3000`

## Project Structure

```
app/
├── layout.tsx          # Root layout with theme provider
├── page.tsx           # Homepage (Explore Feed)
├── search/page.tsx    # Search interface
└── product/[id]/page.tsx  # Product detail

components/
├── navigation.tsx      # Top navigation bar
├── product-card.tsx   # Product card component
├── search-interface.tsx  # Search UI (text + image)
├── explore-feed.tsx   # Product grid feed
└── theme-provider.tsx # Dark mode provider

lib/
└── api.ts             # API client functions

types/
└── product.ts         # TypeScript interfaces
```

## API Integration

The frontend integrates with the backend API at `http://localhost:8000/api/v1`:

### Endpoints Used

- `GET /api/v1/health` - Health check
- `POST /api/v1/search/text` - Text search
- `POST /api/v1/search/similar` - Image similarity search
- `POST /api/v1/detect` - Item detection (available in API client)

### Response Transformation

The API client automatically transforms nested API responses into the frontend's `Product` type format.

## Pages

### `/` - Explore Feed
Browse a curated feed of fashion items in a responsive grid layout.

### `/search` - Search Interface
- **Text Search**: Enter queries like "red shoes" or "casual dress"
- **Image Search**: Upload an image to find visually similar products

### `/product/[id]` - Product Detail
View detailed information about a specific product, including:
- High-resolution images
- Price and category
- Similarity scores (for search results)
- Key similarities and metadata

## Design System

The design system follows Next.js Commerce patterns:

- **Color System**: HSL-based CSS variables for theming
- **Spacing**: Consistent Tailwind utility classes
- **Components**: Card-based layouts with hover effects
- **Typography**: Clean, readable font hierarchy
- **Responsive Grid**: 
  - 1 column (mobile)
  - 2-3 columns (tablet)
  - 3-4 columns (desktop)

## Development

### Running the Project

```bash
# Start development server
pnpm dev

# Build for production
pnpm build

# Start production server
pnpm start

# Lint code
pnpm lint
```

### Testing Backend Connection

Before building UI components, verify your backend is running:

```bash
curl http://localhost:8000/api/v1/health
```

You can also visit `http://localhost:8000/docs` for Swagger API documentation.

## Notes

- **CORS**: Backend is configured to allow all origins
- **Image Upload**: Uses `file` as the form field name (not `image`)
- **Error Handling**: Displays user-friendly error messages
- **Loading States**: Shows spinners during API calls
- **Image Optimization**: Uses Next.js `Image` component for optimized loading

## License

MIT

