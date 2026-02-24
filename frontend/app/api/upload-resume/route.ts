import { NextRequest, NextResponse } from "next/server";

export const maxDuration = 120;

const BACKEND_URL = process.env.BACKEND_URL || "http://127.0.0.1:8000";

export async function POST(request: NextRequest) {
  try {
    const incomingFormData = await request.formData();
    console.log("[Upload API Route] Forwarding to Django");

    const file = incomingFormData.get("file");

    if (!file || !(file instanceof Blob)) {
      return NextResponse.json(
        { error: "No file received in API route" },
        { status: 400 }
      );
    }

    const forwardFormData = new FormData();
    forwardFormData.append("file", file, (file as any).name);

    const response = await fetch(`${BACKEND_URL}/api/upload-resume/`, {
      method: "POST",
      body: forwardFormData,
    });

    const data = await response.json();
    console.log("[Upload API Route] Django response status:", response.status);

    return NextResponse.json(data, { status: response.status });

  } catch (error) {
    console.error("[Upload API Route] Error:", error);
    return NextResponse.json(
      { error: error instanceof Error ? error.message : "Upload proxy error" },
      { status: 500 }
    );
  }
}