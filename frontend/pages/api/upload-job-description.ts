import type { NextApiRequest, NextApiResponse } from "next";

export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse
) {
  if (req.method !== "POST") {
    return res.status(405).json({ error: "Method not allowed" });
  }

  try {
    // Create FormData to forward the file
    const formData = new FormData();
    
    // Get file from request
    // Note: This is a simplified version - in a real implementation,
    // you'd need proper file handling middleware like multer
    
    // Forward to backend
    const apiUrl = process.env.INTERNAL_API_URL || process.env.NEXT_PUBLIC_API_URL || "http://localhost:8002";
    const response = await fetch(`${apiUrl}/upload-job-description`, {
      method: "POST",
      body: req.body, // Forward the raw body
    });

    if (!response.ok) {
      throw new Error(`Backend responded with ${response.status}`);
    }

    const data = await response.json();
    res.status(200).json(data);
  } catch (error) {
    console.error("Error uploading job description:", error);
    res.status(500).json({ 
      error: "Failed to upload job description",
      details: error instanceof Error ? error.message : "Unknown error"
    });
  }
}

export const config = {
  api: {
    bodyParser: false, // Disable body parsing to handle file uploads
  },
};
