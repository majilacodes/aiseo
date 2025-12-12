import { NextRequest, NextResponse } from 'next/server';

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    
    const response = await fetch(`${BACKEND_URL}/api/v1/jobs`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
      // Add timeout to prevent hanging
      signal: AbortSignal.timeout(300000), // 5 minutes timeout
    });

    const data = await response.json();
    
    return NextResponse.json(data, { status: response.status });
  } catch (error: any) {
    // Handle connection errors gracefully
    if (error.name === 'AbortError' || error.name === 'TimeoutError') {
      return NextResponse.json(
        { error: 'Request timeout. The backend server may be taking too long to respond.' },
        { status: 504 }
      );
    }
    
    // Handle socket hang up and connection errors
    if (error.code === 'ECONNREFUSED' || error.code === 'ECONNRESET' || 
        error.message?.includes('socket hang up') || 
        error.message?.includes('ECONNRESET')) {
      return NextResponse.json(
        { error: 'Unable to connect to the backend server. Please make sure the backend is running on http://localhost:8000. You can start it with: uvicorn app.main:app --reload' },
        { status: 503 }
      );
    }
    
    if (error instanceof TypeError && error.message.includes('fetch')) {
      return NextResponse.json(
        { error: 'Network error. Please check if the backend server is running.' },
        { status: 503 }
      );
    }
    
    return NextResponse.json(
      { error: error.message || 'An unexpected error occurred' },
      { status: 500 }
    );
  }
}


