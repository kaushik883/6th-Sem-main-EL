# LogiSight Frontend

Pure frontend application for freight audit and invoice analysis. **Zero external dependencies** - only requires a backend API.

## 🚀 Quick Start

```bash
# Install dependencies
npm install

# Set backend URL
echo "VITE_API_URL=http://localhost:8001" > .env

# Run development server
npm run dev

# Build for production
npm run build
```

## 📋 What's Included

### Pages (12 total):
1. Landing & Login
2. Dashboard
3. Companies (super admin)
4. Quotes (list, create, detail)
5. Invoices (list, detail, analysis)
6. Charge Master
7. Tracking
8. AI Copilot

### Features:
- JWT authentication
- Role-based access control
- Form validation
- Error handling
- Responsive design

## � Backend Requirements

The frontend expects a backend API at `VITE_API_URL`. See `API_CONTRACT.md` for complete specification.

### Key Endpoints:
- `POST /auth/login` - Authentication
- `GET /quotes` - List quotes
- `POST /invoices/{id}/analyze` - Detect anomalies
- `GET /charges` - Charge master
- And 35+ more...

## 📚 Documentation

- `API_CONTRACT.md` - Complete backend API specification
- `src/api/types.ts` - TypeScript type definitions
- `src/api/client.ts` - API client implementation

## 🛠️ Tech Stack

- React 18 + TypeScript
- React Router 7
- TanStack Query
- Axios
- Tailwind CSS
- React Hook Form + Zod

## 📱 Browser Support

- Chrome, Firefox, Safari, Edge (latest)
- Desktop & tablet optimized
- Mobile works but not optimized

---

**For complete feature documentation, see the main README.md**
