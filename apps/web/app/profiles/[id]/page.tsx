import { notFound } from "next/navigation";
import Link from "next/link";
import type { ApiProfile } from "@job-hunter/shared-types";

async function getProfile(id: string): Promise<ApiProfile | null> {
  try {
    const res = await fetch(
      `${process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"}/api/v1/profiles/${id}`,
      { cache: "no-store" }
    );
    if (res.status === 404) return null;
    if (!res.ok) return null;
    return res.json();
  } catch {
    return null;
  }
}

export default async function ProfilePage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const profile = await getProfile(id);
  if (!profile) notFound();

  const dateRange = (start?: string, end?: string) => {
    if (!start && !end) return null;
    if (!end) return start;
    return `${start} – ${end}`;
  };

  return (
    <div className="flex flex-col gap-6">
      {/* Breadcrumb */}
      <div className="flex items-center gap-2 text-sm text-gray-400">
        <Link href="/profiles" className="hover:text-gray-600 transition-colors">
          Profiles
        </Link>
        <span>/</span>
        <span className="text-gray-700">{profile.name ?? "Unknown"}</span>
      </div>

      {/* Header card */}
      <div className="rounded-2xl bg-white border border-gray-200 px-6 py-6">
        <div className="flex items-start justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">
              {profile.name ?? "Unknown Name"}
            </h1>
            <div className="flex flex-wrap gap-4 mt-2 text-sm text-gray-500">
              {profile.email && <span>✉️ {profile.email}</span>}
              {profile.phone && <span>📞 {profile.phone}</span>}
            </div>
          </div>
          <div className="text-right text-xs text-gray-400 shrink-0">
            <p>From: {profile.source_filename}</p>
            <p>Extracted: {new Date(profile.created_at).toLocaleDateString()}</p>
          </div>
        </div>

        {profile.summary && (
          <p className="mt-4 text-gray-600 leading-relaxed text-sm border-t border-gray-100 pt-4">
            {profile.summary}
          </p>
        )}
      </div>

      {/* Skills */}
      {profile.skills && profile.skills.length > 0 && (
        <section>
          <h2 className="text-lg font-semibold text-gray-800 mb-3">Skills</h2>
          <div className="flex flex-wrap gap-2">
            {profile.skills.map((skill) => (
              <span
                key={skill}
                className="rounded-full bg-blue-50 border border-blue-100 px-3 py-1 text-sm text-blue-700"
              >
                {skill}
              </span>
            ))}
          </div>
        </section>
      )}

      {/* Work Experience */}
      {profile.work_experience && profile.work_experience.length > 0 && (
        <section>
          <h2 className="text-lg font-semibold text-gray-800 mb-3">
            Work Experience
          </h2>
          <div className="flex flex-col gap-4">
            {profile.work_experience.map((job, i) => (
              <div
                key={i}
                className="rounded-xl bg-white border border-gray-200 px-5 py-4"
              >
                <div className="flex items-start justify-between gap-2">
                  <div>
                    <p className="font-medium text-gray-900">{job.title}</p>
                    <p className="text-sm text-gray-500">{job.company}</p>
                  </div>
                  {dateRange(job.start_date, job.end_date) && (
                    <span className="text-xs text-gray-400 shrink-0">
                      {dateRange(job.start_date, job.end_date)}
                    </span>
                  )}
                </div>
                {job.description && (
                  <p className="mt-2 text-sm text-gray-600 leading-relaxed">
                    {job.description}
                  </p>
                )}
                {job.technologies && job.technologies.length > 0 && (
                  <div className="mt-2 flex flex-wrap gap-1.5">
                    {job.technologies.map((tech) => (
                      <span
                        key={tech}
                        className="rounded bg-gray-100 px-2 py-0.5 text-xs text-gray-600"
                      >
                        {tech}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        </section>
      )}

      {/* Education */}
      {profile.education && profile.education.length > 0 && (
        <section>
          <h2 className="text-lg font-semibold text-gray-800 mb-3">Education</h2>
          <div className="flex flex-col gap-3">
            {profile.education.map((edu, i) => (
              <div
                key={i}
                className="rounded-xl bg-white border border-gray-200 px-5 py-4"
              >
                <div className="flex items-start justify-between gap-2">
                  <div>
                    <p className="font-medium text-gray-900">{edu.institution}</p>
                    {(edu.degree || edu.field_of_study) && (
                      <p className="text-sm text-gray-500">
                        {[edu.degree, edu.field_of_study].filter(Boolean).join(" · ")}
                      </p>
                    )}
                  </div>
                  {dateRange(edu.start_date, edu.end_date) && (
                    <span className="text-xs text-gray-400 shrink-0">
                      {dateRange(edu.start_date, edu.end_date)}
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* Actions */}
      <div className="flex gap-3 pt-2 border-t border-gray-200">
        <Link
          href="/profiles"
          className="text-sm text-gray-500 hover:text-gray-700 transition-colors"
        >
          ← Back to profiles
        </Link>
        <Link
          href="/"
          className="ml-auto text-sm text-blue-600 hover:underline"
        >
          Upload another CV
        </Link>
      </div>
    </div>
  );
}
