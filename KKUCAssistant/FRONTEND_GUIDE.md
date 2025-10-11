# Frontend Customization Guide

A comprehensive guide to customizing and extending the Assistant UI frontend. This guide is designed for developers with HTML/CSS background transitioning to React and TypeScript.

## Table of Contents
1. [Getting Started](#getting-started)
2. [Project Structure](#project-structure)
3. [Basic Styling with Tailwind CSS](#basic-styling-with-tailwind-css)
4. [Component Customization](#component-customization)
5. [Creating Custom Tool UIs (Generative UI)](#creating-custom-tool-uis-generative-ui)
6. [Advanced Customization](#advanced-customization)
7. [Common Patterns](#common-patterns)

---

## Getting Started

### Basic Commands

```bash
# Navigate to frontend directory
cd KKUCAssistant/frontend

# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build

# Start production server
npm start
```

### Key Technologies

- **Next.js 15**: React framework (like a more powerful version of HTML pages)
- **TypeScript**: JavaScript with types (adds safety to your code)
- **Tailwind CSS**: Utility-first CSS framework (like inline styles but better)
- **Assistant UI**: Pre-built chat components
- **shadcn/ui**: Reusable component library

---

## Project Structure

```
frontend/
├── app/                          # Pages and routes (like HTML pages)
│   ├── page.tsx                  # Home page (index.html equivalent)
│   ├── layout.tsx                # Wrapper for all pages (like a master template)
│   ├── globals.css               # Global styles
│   └── api/chat/route.ts         # Backend communication endpoint
├── components/                   # Reusable UI pieces
│   ├── assistant-modal.tsx       # Main chat modal component
│   ├── MyAssistant.tsx           # Full-page chat component
│   ├── GetStockPriceToolUI.tsx   # Example tool UI (generative UI)
│   └── ui/                       # Base UI components (buttons, dialogs, etc.)
└── lib/                          # Utility functions
```

---

## Basic Styling with Tailwind CSS

### Understanding Tailwind (For HTML/CSS Developers)

Tailwind uses utility classes instead of writing CSS. Think of it as inline styles with superpowers.

**HTML/CSS Way:**
```html
<div style="padding: 16px; background-color: blue; color: white;">
  Hello
</div>
```

**Tailwind Way:**
```tsx
<div className="p-4 bg-blue-500 text-white">
  Hello
</div>
```

### Common Tailwind Classes

| CSS Property | Tailwind Class | Example |
|--------------|----------------|---------|
| `padding: 16px` | `p-4` | `<div className="p-4">` |
| `margin: 8px` | `m-2` | `<div className="m-2">` |
| `background-color: blue` | `bg-blue-500` | `<div className="bg-blue-500">` |
| `color: white` | `text-white` | `<div className="text-white">` |
| `font-size: 24px` | `text-2xl` | `<div className="text-2xl">` |
| `display: flex` | `flex` | `<div className="flex">` |
| `border-radius: 8px` | `rounded-lg` | `<div className="rounded-lg">` |

### Spacing Scale
- `p-1` = 4px
- `p-2` = 8px
- `p-4` = 16px
- `p-6` = 24px
- `p-8` = 32px

### Modifying Global Styles

**File:** `frontend/app/globals.css`

```css
@tailwind base;
@tailwind components;
@tailwind utilities;

/* Add your custom CSS here */
@layer base {
  body {
    @apply bg-gray-50;
  }
}

@layer components {
  .custom-button {
    @apply px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600;
  }
}
```

---

## Component Customization

### 1. Changing the Modal Appearance

**File:** `frontend/components/assistant-modal.tsx`

The modal uses the `AssistantModal` component from `@assistant-ui/react`. To customize:

```tsx
'use client';

import { useChat } from 'ai/react';
import { AssistantModal } from '@assistant-ui/react';
import { makeMarkdownText } from '@assistant-ui/react-markdown';
import { useVercelUseChatRuntime } from '@assistant-ui/react-ai-sdk';

const MarkdownText = makeMarkdownText();

export function MyAssistantModal() {
  const chat = useChat({
    api: '/api/chat',
  });

  const runtime = useVercelUseChatRuntime(chat);

  return (
    <AssistantModal
      runtime={runtime}
      assistantMessage={{ 
        components: { 
          Text: MarkdownText 
        } 
      }}
      // Add custom styling here
      className="custom-modal-class"
    />
  );
}
```

### 2. Changing the Welcome Message

The welcome message "How can I help you today?" comes from the Assistant UI library. To customize it, you can create a custom Thread component.

**Create:** `frontend/components/CustomThread.tsx`

```tsx
'use client';

import { Thread } from '@assistant-ui/react';
import { makeMarkdownText } from '@assistant-ui/react-markdown';

const MarkdownText = makeMarkdownText();

export function CustomThread({ runtime }: { runtime: any }) {
  return (
    <div className="h-full flex flex-col">
      {/* Custom welcome section */}
      <div className="p-6 bg-gradient-to-r from-blue-500 to-purple-600 text-white">
        <h1 className="text-3xl font-bold mb-2">Welcome to Your Assistant!</h1>
        <p className="text-lg">Ask me anything about stocks, weather, or general questions.</p>
      </div>
      
      {/* Chat thread */}
      <Thread
        runtime={runtime}
        assistantMessage={{ components: { Text: MarkdownText } }}
        className="flex-1"
      />
    </div>
  );
}
```

### 3. Customizing Colors and Fonts

**File:** `frontend/app/layout.tsx`

```tsx
import type { Metadata } from "next";
import localFont from "next/font/local";
import "./globals.css";

// Custom fonts
const geistSans = localFont({
  src: "./fonts/GeistVF.woff",
  variable: "--font-geist-sans",
  weight: "100 900",
});

export const metadata: Metadata = {
  title: "My Custom Assistant",  // Change browser tab title
  description: "AI-powered assistant",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body
        className={`${geistSans.variable} antialiased bg-gray-100`}
        // Add custom background color or classes here
      >
        {children}
      </body>
    </html>
  );
}
```

### 4. Changing the Modal Button Position

**File:** `frontend/app/page.tsx`

```tsx
import { MyAssistantModal } from "@/components/assistant-modal";

export default function Home() {
  return (
    <main className="h-dvh relative">
      {/* Add your custom content here */}
      <div className="p-8">
        <h1 className="text-4xl font-bold">My Website</h1>
        <p>Welcome to my site with an AI assistant!</p>
      </div>
      
      {/* The modal button appears in bottom-right by default */}
      <MyAssistantModal />
    </main>
  );
}
```

---

## Creating Custom Tool UIs (Generative UI)

Generative UI allows you to create custom visualizations for tool responses. Instead of showing plain text, you can display rich, interactive components.

### Understanding the Pattern

When your backend agent calls a tool (like `get_stock_price`), you can create a custom UI to display the results beautifully.

### Example: Stock Price Tool UI

**File:** `frontend/components/GetStockPriceToolUI.tsx`

Let's break down this file step by step:

#### Step 1: Define Types (Data Structure)

```tsx
// This is like defining what data you expect to receive
type GetStockPriceToolArgs = {
    stock_symbol: string;  // Input: what stock to look up
}

type GetStockPriceToolResult = {
    // Output: all the stock data
    symbol: string;
    company_name: string;
    current_price: number;
    change: number;
    // ... more fields
}
```

**Think of types as:** A contract that says "this data will have these fields"

#### Step 2: Create Reusable Components

```tsx
// Loading spinner (like a loading GIF)
const LoadingSpinner = () => (
    <div className="flex justify-center items-center p-4">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900"></div>
    </div>
);

// Reusable info display (like a <div> with consistent styling)
const StockInfoItem = ({ label, value, className = '' }: { 
    label: string; 
    value: string | number; 
    className?: string 
}) => (
    <div>
        <p className="text-gray-600">{label}</p>
        <p className={`font-semibold ${className}`}>{value}</p>
    </div>
);
```

#### Step 3: Create the Main Display Component

```tsx
const StockPriceDisplay = ({ result }: { result: GetStockPriceToolResult }) => {
    if (!result) return null;
    
    // Calculate color based on positive/negative change
    const changeColor = (result.change ?? 0) >= 0 ? 'text-green-600' : 'text-red-600';
    const changePrefix = (result.change ?? 0) >= 0 ? '+' : '';
    
    return (
        <div className="p-4 border rounded-lg shadow-md">
            <h1 className="text-2xl font-bold mb-4">{result.company_name}</h1>
            
            {/* Grid layout (like CSS Grid) */}
            <div className="grid grid-cols-2 gap-4">
                <StockInfoItem label="Symbol" value={result.symbol ?? 'N/A'} />
                <StockInfoItem label="Current Price" value={`$${result.current_price?.toFixed(2) ?? 'N/A'}`} />
                <StockInfoItem 
                    label="Change" 
                    value={`${changePrefix}${result.change?.toFixed(2) ?? 'N/A'}`}
                    className={changeColor}
                />
                {/* More items... */}
            </div>
        </div>
    );
};
```

#### Step 4: Register the Tool UI

```tsx
export const GetStockPriceToolUI = makeAssistantToolUI<GetStockPriceToolArgs, GetStockPriceToolResult>({
    toolName: "get_stock_price",  // Must match backend tool name
    render: ({ result }) => {
        if (!result) return <LoadingSpinner />;
        return <StockPriceDisplay result={result} />;
    }
});
```

### Creating Your Own Tool UI

Let's create a weather tool UI as an example:

**Create:** `frontend/components/WeatherToolUI.tsx`

```tsx
import { makeAssistantToolUI } from '@assistant-ui/react';

// Step 1: Define types
type WeatherToolArgs = {
    location: string;
}

type WeatherToolResult = {
    location: string;
    temperature: number;
    condition: string;
    humidity: number;
    wind_speed: number;
}

// Step 2: Create display component
const WeatherDisplay = ({ result }: { result: WeatherToolResult }) => {
    // Map conditions to emojis
    const weatherEmoji = {
        'sunny': '☀️',
        'cloudy': '☁️',
        'rainy': '🌧️',
        'snowy': '❄️',
    }[result.condition.toLowerCase()] || '🌤️';

    return (
        <div className="p-6 bg-gradient-to-br from-blue-400 to-blue-600 rounded-xl text-white shadow-lg">
            <div className="text-center mb-4">
                <div className="text-6xl mb-2">{weatherEmoji}</div>
                <h2 className="text-3xl font-bold">{result.location}</h2>
            </div>
            
            <div className="grid grid-cols-2 gap-4 text-center">
                <div className="bg-white/20 rounded-lg p-4">
                    <p className="text-sm opacity-80">Temperature</p>
                    <p className="text-3xl font-bold">{result.temperature}°F</p>
                </div>
                <div className="bg-white/20 rounded-lg p-4">
                    <p className="text-sm opacity-80">Condition</p>
                    <p className="text-xl font-semibold">{result.condition}</p>
                </div>
                <div className="bg-white/20 rounded-lg p-4">
                    <p className="text-sm opacity-80">Humidity</p>
                    <p className="text-xl font-semibold">{result.humidity}%</p>
                </div>
                <div className="bg-white/20 rounded-lg p-4">
                    <p className="text-sm opacity-80">Wind Speed</p>
                    <p className="text-xl font-semibold">{result.wind_speed} mph</p>
                </div>
            </div>
        </div>
    );
};

// Step 3: Register the tool
export const WeatherToolUI = makeAssistantToolUI<WeatherToolArgs, WeatherToolResult>({
    toolName: "get_weather",  // Must match your backend tool name
    render: ({ result }) => {
        if (!result) {
            return (
                <div className="flex items-center gap-2 p-4">
                    <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-500"></div>
                    <span>Fetching weather data...</span>
                </div>
            );
        }
        return <WeatherDisplay result={result} />;
    }
});
```

### Step 4: Register Your Tool UI

**File:** `frontend/components/assistant-modal.tsx`

```tsx
'use client';

import { useChat } from 'ai/react';
import { AssistantModal } from '@assistant-ui/react';
import { makeMarkdownText } from '@assistant-ui/react-markdown';
import { useVercelUseChatRuntime } from '@assistant-ui/react-ai-sdk';
import { GetStockPriceToolUI } from './GetStockPriceToolUI';
import { WeatherToolUI } from './WeatherToolUI';  // Import your new tool
import { ToolFallback } from './ToolFallBack';

const MarkdownText = makeMarkdownText();

export function MyAssistantModal() {
  const chat = useChat({
    api: '/api/chat',
  });

  const runtime = useVercelUseChatRuntime(chat);

  return (
    <AssistantModal
      runtime={runtime}
      assistantMessage={{ components: { Text: MarkdownText, ToolFallback } }}
      tools={[
        GetStockPriceToolUI,
        WeatherToolUI,  // Add your new tool here
      ]}
    />
  );
}
```

---

## Advanced Customization

### 1. Creating Interactive Tool UIs

You can make tool UIs interactive with buttons and state:

```tsx
import { makeAssistantToolUI } from '@assistant-ui/react';
import { useState } from 'react';

type ChartToolResult = {
    data: number[];
    labels: string[];
}

const ChartDisplay = ({ result }: { result: ChartToolResult }) => {
    const [viewType, setViewType] = useState<'bar' | 'line'>('bar');

    return (
        <div className="p-4 border rounded-lg">
            {/* Toggle buttons */}
            <div className="flex gap-2 mb-4">
                <button
                    onClick={() => setViewType('bar')}
                    className={`px-4 py-2 rounded ${
                        viewType === 'bar' ? 'bg-blue-500 text-white' : 'bg-gray-200'
                    }`}
                >
                    Bar Chart
                </button>
                <button
                    onClick={() => setViewType('line')}
                    className={`px-4 py-2 rounded ${
                        viewType === 'line' ? 'bg-blue-500 text-white' : 'bg-gray-200'
                    }`}
                >
                    Line Chart
                </button>
            </div>

            {/* Display based on selection */}
            <div className="h-64 bg-gray-100 rounded flex items-center justify-center">
                {viewType === 'bar' ? '📊 Bar Chart' : '📈 Line Chart'}
            </div>
        </div>
    );
};

export const ChartToolUI = makeAssistantToolUI<{}, ChartToolResult>({
    toolName: "generate_chart",
    render: ({ result }) => {
        if (!result) return <div>Loading chart...</div>;
        return <ChartDisplay result={result} />;
    }
});
```

### 2. Adding Animations

Use Tailwind's animation classes:

```tsx
<div className="animate-pulse">Loading...</div>
<div className="animate-bounce">↓</div>
<div className="animate-spin">⟳</div>

{/* Custom animation */}
<div className="transition-all duration-300 hover:scale-110">
    Hover me!
</div>
```

### 3. Responsive Design

Make your UI work on mobile and desktop:

```tsx
<div className="
    p-4           /* padding on mobile */
    md:p-8        /* larger padding on medium screens and up */
    grid 
    grid-cols-1   /* 1 column on mobile */
    md:grid-cols-2 /* 2 columns on medium screens */
    lg:grid-cols-3 /* 3 columns on large screens */
    gap-4
">
    {/* Your content */}
</div>
```

### 4. Custom Themes

Create a theme configuration:

**File:** `frontend/lib/theme.ts`

```tsx
export const theme = {
    colors: {
        primary: 'bg-blue-500',
        secondary: 'bg-purple-500',
        success: 'bg-green-500',
        danger: 'bg-red-500',
    },
    text: {
        primary: 'text-gray-900',
        secondary: 'text-gray-600',
        light: 'text-gray-400',
    },
    spacing: {
        small: 'p-2',
        medium: 'p-4',
        large: 'p-8',
    }
};
```

Use it in components:

```tsx
import { theme } from '@/lib/theme';

<div className={`${theme.colors.primary} ${theme.spacing.medium} ${theme.text.primary}`}>
    Themed content
</div>
```

---

## Common Patterns

### Pattern 1: Conditional Rendering

```tsx
// Show different content based on condition
{isLoading ? (
    <LoadingSpinner />
) : (
    <DataDisplay data={data} />
)}

// Show content only if condition is true
{error && (
    <div className="text-red-500">Error: {error}</div>
)}
```

### Pattern 2: Mapping Over Arrays

```tsx
// Like a for loop in HTML
const items = ['Apple', 'Banana', 'Orange'];

<ul>
    {items.map((item, index) => (
        <li key={index} className="p-2">
            {item}
        </li>
    ))}
</ul>
```

### Pattern 3: Event Handlers

```tsx
// Like onclick in HTML
<button 
    onClick={() => console.log('Clicked!')}
    className="px-4 py-2 bg-blue-500 text-white rounded"
>
    Click Me
</button>

// With a function
const handleClick = () => {
    console.log('Button clicked!');
};

<button onClick={handleClick}>
    Click Me
</button>
```

### Pattern 4: Props (Passing Data)

```tsx
// Like HTML attributes but more powerful
type CardProps = {
    title: string;
    description: string;
    imageUrl?: string;  // Optional prop
}

const Card = ({ title, description, imageUrl }: CardProps) => (
    <div className="border rounded-lg p-4">
        {imageUrl && <img src={imageUrl} alt={title} />}
        <h3 className="text-xl font-bold">{title}</h3>
        <p className="text-gray-600">{description}</p>
    </div>
);

// Usage
<Card 
    title="My Card" 
    description="This is a card" 
    imageUrl="/image.jpg"
/>
```

---

## Quick Reference

### File Locations

| What to Change | File Location |
|----------------|---------------|
| Home page content | `frontend/app/page.tsx` |
| Site title & metadata | `frontend/app/layout.tsx` |
| Global styles | `frontend/app/globals.css` |
| Modal component | `frontend/components/assistant-modal.tsx` |
| Create new tool UI | `frontend/components/YourToolUI.tsx` |
| Backend connection | `frontend/app/api/chat/route.ts` |

### Common Tasks

**Add a new page:**
1. Create `frontend/app/about/page.tsx`
2. Add content like in `page.tsx`

**Change colors:**
1. Use Tailwind classes: `bg-blue-500`, `text-red-600`, etc.
2. Or modify `globals.css` for global changes

**Add a new tool UI:**
1. Create component in `frontend/components/`
2. Import and add to `tools` array in `assistant-modal.tsx`

**Modify spacing:**
- Use `p-{size}` for padding
- Use `m-{size}` for margin
- Use `gap-{size}` for flex/grid gaps

---

## Resources

- [Tailwind CSS Docs](https://tailwindcss.com/docs)
- [Assistant UI Docs](https://www.assistant-ui.com/docs)
- [shadcn/ui Components](https://ui.shadcn.com/docs/components)
- [Next.js Docs](https://nextjs.org/docs)
- [React Docs](https://react.dev)

---

## Troubleshooting

### Issue: Changes not showing up
**Solution:** 
1. Save the file
2. Check terminal for errors
3. Refresh browser (Cmd/Ctrl + R)
4. If still not working, restart dev server: `npm run dev`

### Issue: TypeScript errors
**Solution:**
1. Make sure types match (check the type definitions)
2. Add `?` for optional fields: `value?: string`
3. Use `any` as last resort: `data: any`

### Issue: Styling not working
**Solution:**
1. Check class names are correct
2. Make sure Tailwind classes are separated by spaces
3. Check for typos in class names
4. Verify `globals.css` imports Tailwind

---

## Next Steps

1. **Start Simple:** Modify colors and text in existing components
2. **Practice Tailwind:** Try different utility classes
3. **Create a Tool UI:** Follow the weather example above
4. **Experiment:** Break things and fix them - that's how you learn!
5. **Read Docs:** Check the resources section for deeper learning

Remember: Every expert was once a beginner. Start small, experiment often, and don't be afraid to make mistakes!
