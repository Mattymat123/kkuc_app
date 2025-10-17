# Calendar Slot Picker Components

Interactive React components for displaying and selecting available appointment time slots in the KKUC booking flow.

## Components

### TimeSlotPicker
Main container component that displays available time slots in a responsive grid.

**Features:**
- 2-column grid on desktop, 1-column on mobile
- Smooth slide-in animations with staggered effect
- Auto-submits selection to backend via @assistant-ui/react
- Manages selected state with useState hook

**Usage:**
```tsx
import { TimeSlotPicker } from '@/components/calendar';

<TimeSlotPicker data={{ slots: [...] }} />
```

### TimeSlotBox
Individual time slot button component with KKUC branding.

**Features:**
- KKUC brand color (#DF6141) for selected/hover states
- Checkmark indicator when selected
- Displays day name, date, and time
- Smooth animations and transitions
- Accessible keyboard navigation

## Customization

### Colors
The primary brand color is set to `#DF6141`. To change it:

1. **TimeSlotBox.tsx** - Line 35: `border: '2px solid #DF6141'` for selected border
2. **TimeSlotBox.tsx** - Line 36: `backgroundColor: 'rgba(223, 97, 65, 0.05)'` for selected background
3. **TimeSlotBox.tsx** - Line 51: `color: '#DF6141'` for checkmark icon
4. **TimeSlotBox.tsx** - Line 75: `color: '#DF6141'` for time display

### Layout
To change from 2-column to 3-column on desktop:

**TimeSlotPicker.tsx** - Line 32:
```tsx
// Current: 2 columns
<Col key={index} xs={24} sm={24} md={12} lg={12} xl={12}>

// Change to: 3 columns (8 spans per column = 24/3)
<Col key={index} xs={24} sm={24} md={8} lg={8} xl={8}>
```

### Animation Timing
To adjust the slide-in animation speed:

**TimeSlotBox.tsx** - Lines 18-22:
```tsx
transition={{ 
  duration: 0.3,        // Animation speed (in seconds)
  delay: index * 0.1,   // Stagger delay between slots
  ease: "easeOut"       // Easing function
}}
```

### Styling
All components use Ant Design components with inline styles. Common customizations:

- **Padding**: `bodyStyle={{ padding: '20px' }}` (padding inside slot boxes)
- **Border Radius**: `borderRadius: '12px'` (corner roundness)
- **Gap**: `gutter={[16, 16]}` (space between slots - horizontal and vertical)
- **Font Sizes**: `fontSize: '18px'`, `fontSize: '15px'`, `fontSize: '22px'`

## How It Works

1. **Backend** sends slot data as a markdown code block:
   ```
   ```calendar-slots
   {"slots": [...]}
   ```
   ```

2. **markdown-text.tsx** detects the `language-calendar-slots` class and renders TimeSlotPicker instead of code block

3. **TimeSlotPicker** displays slots in a grid and manages selection state

4. **TimeSlotBox** renders individual slots with animations

5. When user clicks a slot, TimeSlotPicker sends the slot number (1-based) to backend via `threadRuntime.append()`

6. **Backend** receives the selection and continues the booking flow

## File Structure

```
frontend/components/calendar/
├── types.ts              # TypeScript interfaces
├── TimeSlotBox.tsx       # Individual slot component
├── TimeSlotPicker.tsx    # Main picker container
├── index.ts              # Exports
└── README.md             # This file
```

## Dependencies

- `@assistant-ui/react` - For thread runtime communication
- `antd` - For Card component and Grid system
- `@ant-design/icons` - For CheckCircleFilled icon
- `motion/react-m` - For animations

## Example Slot Data

```typescript
{
  "slots": [
    {
      "day": "Mandag",
      "date": "20.01.2025",
      "time": "14:00",
      "datetime": "2025-01-20T14:00:00"
    },
    // ... more slots
  ]
}
