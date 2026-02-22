import { NextRequest, NextResponse } from "next/server";
export const maxDuration = 120;

const BACKEND_URL = process.env.BACKEND_URL || "http://127.0.0.1:8000";

export async function POST(request: NextRequest) {
  try {
    const formData = await request.formData();
    console.log("[Upload API Route] Forwarding to Django");

    const response = await fetch(`${BACKEND_URL}/api/upload-resume/`, {
      method: "POST",
      body: formData,
    });

    const data = await response.json();
    console.log("[Upload API Route] Django response status:", response.status);

    if (!response.ok) {
      return NextResponse.json(data, { status: response.status });
    }

    return NextResponse.json(data);
  } catch (error) {
    console.error("[Upload API Route] Error:", error);
    return NextResponse.json(
      { error: error instanceof Error ? error.message : "Upload proxy error" },
      { status: 500 }
    );
  }
}
