import { NextRequest, NextResponse } from "next/server";

// Increase the max duration for this route (in seconds)
export const maxDuration = 300; // 5 minutes

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    console.log("[API Route] Forwarding to Django:", {
      index_name: body.index_name,
      jd_length: body.jd?.length,
    });

    const response = await fetch("http://127.0.0.1:8000/api/tailor-resume/", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(body),
    });

    const data = await response.json();
    console.log("[API Route] Django response status:", response.status);

    if (!response.ok) {
      return NextResponse.json(data, { status: response.status });
    }

    return NextResponse.json(data);
  } catch (error) {
    console.error("[API Route] Error:", error);
    return NextResponse.json(
      { error: error instanceof Error ? error.message : "Proxy error" },
      { status: 500 }
    );
  }
}
