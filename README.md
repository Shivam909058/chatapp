# Real-time Chat Application

A secure, real-time chat application built with FastAPI, WebSockets, and Supabase.

## Features
- Real-time messaging
- File sharing
- Room-based chat
- Secure authentication
- Typing indicators
- Online user status
- Message persistence

## Tech Stack
- FastAPI
- WebSockets
- Supabase
- Docker
- HTML/CSS/JavaScript

## Development
1. Clone the repository
2. Create a `.env` file with your Supabase credentials
3. Install dependencies: `pip install -r requirements.txt`
4. Run the server: `uvicorn receiver:app --reload`

## Deployment
The application is deployed on Render.com using Docker.

## Environment Variables
- `SUPABASE_URL`: Your Supabase project URL
- `SUPABASE_KEY`: Your Supabase anon key 