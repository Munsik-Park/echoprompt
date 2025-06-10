# Frontend

This is the frontend application for EchoPrompt.

## Environment Variables

Required environment variables:
- `VITE_API_PORT`: Port number for the API server
- `VITE_FRONTEND_PORT`: Port number for the frontend server
- `VITE_API_URL`: Full URL for the API server (e.g. `http://localhost:${VITE_API_PORT}`)
- `VITE_FRONTEND_URL`: Full URL for the frontend server (e.g. `http://localhost:${VITE_FRONTEND_PORT}`)

Environment variables can be placed in a `.env` file.

## Development

To start the development server:

```bash
npm run dev
```

## Testing

To run the tests:

```bash
npm test
```

## Building

To build the application:

```bash
npm run build
```
