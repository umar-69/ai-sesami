# Sesame AI Voice Chat

A web application built with Svelte frontend and Python backend for interacting with the Sesame AI voice system. This project integrates the [Sesame AI](https://github.com/ijub/sesame_ai) library to enable conversational AI voice interactions.

## Project Structure

```
project/
├── api/
│   └── voice.py            # Python serverless function for the voice API
├── frontend/               # Svelte frontend
│   ├── public/
│   │   └── index.html      # HTML entry point
│   ├── src/
│   │   └── App.svelte      # Main Svelte component
│   └── package.json        # Frontend dependencies
├── requirements.txt        # Python dependencies
└── vercel.json             # Vercel configuration
```

## Local Development

### Prerequisites

- Node.js (>=14.x)
- npm or yarn
- Python (>=3.8)
- [Vercel CLI](https://vercel.com/docs/cli) (optional, for local testing)

### Setup

1. Clone this repository:
   ```
   git clone https://github.com/your-username/sesame-ai-voice-chat.git
   cd sesame-ai-voice-chat
   ```

2. Install frontend dependencies:
   ```
   cd frontend
   npm install
   ```

3. Install Python dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Run the frontend development server:
   ```
   cd frontend
   npm run dev
   ```

5. For local backend testing, you can use the Vercel CLI:
   ```
   npm install -g vercel
   vercel dev
   ```

## Deployment

This project is designed to be deployed on Vercel. To deploy:

1. Push your code to a Git repository (GitHub, GitLab, or Bitbucket).
2. Create a new project on [Vercel](https://vercel.com).
3. Import your repository and deploy.
4. Vercel will automatically detect the project structure and deploy the frontend and backend.

## How It Works

- The frontend sends text queries to the `/api/voice` endpoint.
- The Python serverless function processes the query using the Sesame AI library.
- The backend responds with the AI's text reply.
- The frontend displays the response to the user.

## License

MIT

## Acknowledgements

This project uses the Sesame AI library by [ijub](https://github.com/ijub). 