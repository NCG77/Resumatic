import { NextRequest, NextResponse } from "next/server";

export const maxDuration = 120; // 2 minutes for upload

export async function POST(request: NextRequest) {
  try {
    const formData = await request.formData();
    console.log("[Upload API Route] Forwarding to Django");

    const response = await fetch("http://127.0.0.1:8000/api/upload-resume/", {
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
