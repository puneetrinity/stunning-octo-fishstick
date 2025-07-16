# ChatSEO Platform Frontend

A modern React.js frontend for the ChatSEO platform, built with Next.js 14, TypeScript, and Tailwind CSS.

## Features

- **Modern React Stack**: Next.js 14 with App Router, TypeScript, and Tailwind CSS
- **Authentication**: JWT-based authentication with protected routes
- **Real-time Monitoring**: Live updates for monitoring sessions with progress tracking
- **Responsive Design**: Mobile-first design with comprehensive responsive breakpoints
- **Advanced UI Components**: Professional dashboard with charts, tables, and forms
- **API Integration**: Comprehensive REST API integration with error handling
- **State Management**: Zustand for client-side state management
- **Form Handling**: React Hook Form with validation
- **Data Visualization**: Recharts for analytics and reporting
- **Notifications**: React Hot Toast for user feedback

## Technology Stack

### Core Framework
- **Next.js 14**: React framework with App Router
- **React 18**: Latest React features with hooks
- **TypeScript**: Type safety throughout the application
- **Tailwind CSS**: Utility-first CSS framework

### UI & Components
- **Headless UI**: Accessible UI components
- **Heroicons**: Beautiful SVG icons
- **Recharts**: Chart library for data visualization
- **Framer Motion**: Animation library
- **Lucide React**: Additional icon library

### Data & State
- **Axios**: HTTP client for API calls
- **React Query**: Data fetching and caching
- **Zustand**: State management
- **React Hook Form**: Form handling and validation

### Development Tools
- **ESLint**: Code linting
- **Prettier**: Code formatting
- **TypeScript**: Type checking

## Getting Started

### Prerequisites
- Node.js 18+ 
- npm or yarn
- Running ChatSEO backend API

### Installation

1. **Install dependencies**
   ```bash
   npm install
   ```

2. **Set up environment variables**
   ```bash
   cp .env.example .env.local
   ```
   
   Configure the following variables:
   ```
   NEXT_PUBLIC_API_URL=http://localhost:8000
   ```

3. **Run the development server**
   ```bash
   npm run dev
   ```

4. **Open your browser**
   Navigate to [http://localhost:3000](http://localhost:3000)

### Build for Production

```bash
npm run build
npm run start
```

## Project Structure

```
frontend/
├── src/
│   ├── components/          # Reusable UI components
│   │   ├── Layout/         # Layout components (Header, Sidebar, etc.)
│   │   ├── UI/             # Basic UI components (Button, Input, etc.)
│   │   └── Dashboard/      # Dashboard-specific components
│   ├── hooks/              # Custom React hooks
│   ├── lib/                # Utility libraries and API clients
│   ├── pages/              # Next.js pages
│   ├── styles/             # Global styles and Tailwind configuration
│   └── types/              # TypeScript type definitions
├── public/                 # Static assets
├── package.json
├── tailwind.config.js
├── next.config.js
└── tsconfig.json
```

## Key Features

### 1. Authentication System
- JWT-based authentication
- Protected routes with automatic redirects
- User session management
- Login/logout functionality

### 2. Dashboard
- Real-time statistics and metrics
- Interactive charts and visualizations
- Recent activity feeds
- Top performing brands overview

### 3. Monitoring Interface
- Multi-platform monitoring configuration
- Real-time progress tracking
- Session management
- Results visualization

### 4. Brand Management
- Brand CRUD operations
- Alias management
- Primary brand designation

### 5. Analytics & Reporting
- Comprehensive analytics dashboard
- Competitor analysis
- Sentiment tracking
- Platform performance metrics

## API Integration

The frontend integrates with the ChatSEO backend API through:

- **Authentication API**: Login, register, user management
- **Monitoring API**: Start/stop monitoring, real-time status
- **Analytics API**: Dashboard stats, charts, reports
- **Brands API**: Brand management operations
- **Citations API**: Mention and citation management

## Component Architecture

### Layout Components
- **Layout**: Main application layout wrapper
- **Header**: Top navigation with user info and search
- **Sidebar**: Navigation menu with route indicators

### UI Components
- **Button**: Configurable button with loading states
- **LoadingSpinner**: Loading indicator in multiple sizes
- **StatsCard**: Dashboard statistics display

### Forms
- **React Hook Form**: Form validation and submission
- **Error Handling**: Comprehensive error display
- **Loading States**: Visual feedback during operations

## Styling

### Tailwind CSS Configuration
- **Custom Colors**: Primary, secondary, success, warning, error palettes
- **Custom Components**: Reusable component classes
- **Responsive Design**: Mobile-first approach
- **Dark Mode**: Built-in support for future enhancement

### Design System
- **Typography**: Inter font family with consistent scales
- **Spacing**: Consistent spacing scale
- **Shadows**: Elevation-based shadow system
- **Border Radius**: Consistent border radius scale

## State Management

### Authentication State
- User authentication status
- Current user information
- Authentication token management

### Application State
- Dashboard statistics
- Monitoring session data
- Brand information
- UI state (loading, errors, etc.)

## Security Features

- **JWT Token Management**: Secure token storage and refresh
- **Protected Routes**: Authentication-required pages
- **Input Validation**: Client-side and server-side validation
- **CSRF Protection**: Built-in Next.js security features
- **XSS Prevention**: Sanitized user inputs

## Performance Optimizations

- **Code Splitting**: Automatic code splitting with Next.js
- **Image Optimization**: Next.js Image component
- **Bundle Analysis**: Bundle size monitoring
- **Caching**: API response caching with React Query
- **Lazy Loading**: Component lazy loading

## Development Guidelines

### Code Style
- **TypeScript**: Strict type checking enabled
- **ESLint**: Configured with Next.js and TypeScript rules
- **Prettier**: Consistent code formatting
- **File Naming**: PascalCase for components, camelCase for utilities

### Component Guidelines
- **Functional Components**: Use hooks instead of class components
- **Props Interface**: Define interfaces for all component props
- **Error Boundaries**: Implement error boundaries for robustness
- **Accessibility**: Follow WCAG guidelines

### Testing (Future Enhancement)
- Unit tests with Jest and React Testing Library
- Integration tests for API interactions
- E2E tests with Cypress
- Visual regression testing

## Deployment

### Production Build
```bash
npm run build
npm run start
```

### Docker Deployment
```dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
RUN npm run build
EXPOSE 3000
CMD ["npm", "start"]
```

### Environment Variables
- `NEXT_PUBLIC_API_URL`: Backend API URL
- `NEXT_PUBLIC_ENVIRONMENT`: Production environment flag

## Future Enhancements

### Planned Features
- **Real-time Updates**: WebSocket integration for live data
- **Advanced Analytics**: More sophisticated reporting
- **Export Functionality**: PDF and Excel export capabilities
- **Mobile App**: React Native mobile application
- **Dark Mode**: Complete dark mode implementation

### Technical Improvements
- **Testing Suite**: Comprehensive test coverage
- **Performance Monitoring**: Application performance tracking
- **Error Tracking**: Integrated error reporting
- **Analytics**: User behavior tracking
- **Internationalization**: Multi-language support

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is part of the ChatSEO platform and is proprietary software.

## Support

For technical support and questions, please contact the development team or open an issue in the repository.