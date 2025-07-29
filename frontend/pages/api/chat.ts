import type { NextApiRequest, NextApiResponse } from "next";

export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse
) {
  if (req.method !== "POST") {
    return res.status(405).json({ error: "Method not allowed" });
  }

  try {
    const { messages, resumeData, session_id } = req.body;

    // Limit to 10 messages per session as required
    if (messages.length > 10) {
      return res.status(400).json({
        error: "Maximum 10 messages per session allowed",
      });
    }

    console.log(
      "🚀 Forwarding chat request to backend with database persistence..."
    );
    console.log("📋 Session ID:", session_id);

    // Get the latest user message
    const latestMessage = messages[messages.length - 1];
    if (!latestMessage || latestMessage.role !== "user") {
      return res.status(400).json({ error: "Invalid message format" });
    }

    // Prepare request for backend API
    const backendRequest = {
      message: latestMessage.content,
      resume_data: resumeData,
      chat_history: messages.slice(0, -1), // All messages except the latest
      session_id: session_id,
    };

    // Call backend API with database persistence
    // Use internal Docker network URL for server-side requests
    const internalUrl = process.env.INTERNAL_API_URL;
    const publicUrl = process.env.NEXT_PUBLIC_API_URL;
    const defaultUrl = "http://localhost:8002";
    
    console.log("🔍 Environment URLs:", { internalUrl, publicUrl, defaultUrl });
    
    const apiUrl = internalUrl || publicUrl || defaultUrl;
    const backendUrl = `${apiUrl}/chat`;
    
    console.log("🔄 Making request to backend:", backendUrl);
    console.log("📤 Request payload:", JSON.stringify(backendRequest, null, 2));
    
    const backendResponse = await fetch(backendUrl, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(backendRequest),
    });

    console.log("📥 Backend response status:", backendResponse.status);
    console.log("📥 Backend response headers:", Object.fromEntries(backendResponse.headers.entries()));

    if (!backendResponse.ok) {
      const errorText = await backendResponse.text();
      console.error("❌ Backend API error:", backendResponse.status, errorText);
      throw new Error(`Backend API error: ${backendResponse.status} - ${errorText}`);
    }

    const responseData = await backendResponse.json();
    console.log("✅ Backend API call successful! Chat saved to database.");

    // Return the response in the format expected by AI SDK
    res.setHeader("Content-Type", "text/plain; charset=utf-8");
    res.setHeader("Cache-Control", "no-cache");
    res.setHeader("Connection", "keep-alive");
    res.write(responseData.response);
    res.end();
  } catch (error: any) {
    console.error("❌ Chat API error:", error.message);
    console.error("❌ Full error details:", error);
    console.error("❌ Error stack:", error.stack);
    
    // Provide more specific error information
    let errorMessage = "Failed to process chat request";
    if (error.message.includes("fetch failed")) {
      errorMessage = "Cannot connect to backend server";
    } else if (error.message.includes("ECONNREFUSED")) {
      errorMessage = "Backend server is not running";
    }
    
    res.status(500).json({ 
      error: errorMessage, 
      details: error.message,
      timestamp: new Date().toISOString()
    });
  }
}
