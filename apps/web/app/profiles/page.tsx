import Link from "next/link";
import type { ApiProfile } from "@job-hunter/shared-types";

async function getProfiles(): Promise<ApiProfile[]> {
  try {
    const res = await fetch(
      `${process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"}/api/v1/profiles`,
      { cache: "no-store" }
    );
    if (!res.ok) return [];
    return res.json();
  } catch {
    return [];
  }
}

export default async function ProfilesPage() {
  const profiles = await getProfiles();

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Your Profiles</h1>
        <Link
          href="/"
          className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 transition-colors"
        >
          + Upload new CV
        </Link>
      </div>

      {profiles.length === 0 ? (
        <div className="rounded-2xl border border-dashed border-gray-300 bg-white px-8 py-16 text-center">
          <p className="text-4xl mb-3">📭</p>
          <p className="text-gray-600 font-medium">No profiles yet</p>
          <p className="text-sm text-gray-400 mt-1">
            Upload a PDF CV to extract your first developer profile.
          </p>
          <Link
            href="/"
            className="inline-block mt-4 text-blue-600 hover:underline text-sm"
          >
            Upload a CV →
          </Link>
        </div>
      ) : (
        <div className="grid gap-3">
          {profiles.map((profile) => (
            <Link
              key={profile.id}
              href={`/profiles/${profile.id}`}
              className="flex items-center justify-between rounded-xl bg-white border border-gray-200 px-5 py-4 hover:border-blue-300 hover:shadow-sm transition-all"
            >
              <div>
                <p className="font-medium text-gray-900">
                  {profile.name ?? "Unknown Name"}
                </p>
                <p className="text-sm text-gray-500 mt-0.5">
                  {profile.email ?? profile.source_filename}
                </p>
              </div>
              <div className="text-right">
                <p className="text-xs text-gray-400">
                  {new Date(profile.created_at).toLocaleDateString()}
                </p>
                <p className="text-sm text-blue-600 mt-0.5">View →</p>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
