/**
 * Next.js API Route: /api/profiles/[id]
 * Proxies GET, PATCH, DELETE to the FastAPI backend.
 */

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export async function GET(
  _request: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params;
  try {
    const response = await fetch(`${API_URL}/api/v1/profiles/${id}`, {
      cache: "no-store",
    });
    const data = await response.json();
    return Response.json(data, { status: response.status });
  } catch {
    return Response.json({ detail: "Failed to reach the API" }, { status: 502 });
  }
}

export async function PATCH(
  request: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params;
  const body = await request.json();
  try {
    const response = await fetch(`${API_URL}/api/v1/profiles/${id}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    const data = await response.json();
    return Response.json(data, { status: response.status });
  } catch {
    return Response.json({ detail: "Failed to reach the API" }, { status: 502 });
  }
}

export async function DELETE(
  _request: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params;
  try {
    const response = await fetch(`${API_URL}/api/v1/profiles/${id}`, {
      method: "DELETE",
    });
    if (response.status === 204) {
      return new Response(null, { status: 204 });
    }
    const data = await response.json();
    return Response.json(data, { status: response.status });
  } catch {
    return Response.json({ detail: "Failed to reach the API" }, { status: 502 });
  }
}
