/**
 * Next.js API Route: /api/profiles
 *
 * Acts as a proxy to the FastAPI backend.
 * Design decision: Next.js never talks directly to Postgres — all DB operations
 * go through FastAPI (see design.md: "Next.js as proxy, not direct DB client").
 */

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export async function POST(request: Request) {
  const formData = await request.formData();

  try {
    const response = await fetch(`${API_URL}/api/v1/profiles`, {
      method: "POST",
      body: formData,
    });

    const data = await response.json();
    return Response.json(data, { status: response.status });
  } catch (error) {
    console.error("Error proxying POST /api/profiles:", error);
    return Response.json({ detail: "Failed to reach the API" }, { status: 502 });
  }
}

export async function GET() {
  try {
    const response = await fetch(`${API_URL}/api/v1/profiles`, {
      cache: "no-store",
    });

    const data = await response.json();
    return Response.json(data, { status: response.status });
  } catch (error) {
    console.error("Error proxying GET /api/profiles:", error);
    return Response.json({ detail: "Failed to reach the API" }, { status: 502 });
  }
}
