// Shared TypeScript types for job-hunter
// Profile types will be defined here once the data model is finalized

export type ExtractionStatus = "pending" | "processing" | "completed" | "failed";

/** Legacy type — kept for backwards compatibility. Use ApiProfile for API responses. */
export interface Profile {
  id: string;
  extraction_status: ExtractionStatus;
  structured_data: ProfileData | null;
  created_at: string;
  updated_at: string;
}

/** Legacy nested data shape — use ApiProfile for real API responses. */
export interface ProfileData {
  name?: string;
  email?: string;
  phone?: string;
  summary?: string;
  experience?: WorkExperience[];
  education?: Education[];
  skills?: string[];
}

export interface WorkExperience {
  company: string;
  title: string;
  start_date?: string;
  end_date?: string;
  description?: string;
  technologies?: string[];
}

export interface Education {
  institution: string;
  degree?: string;
  field?: string;
  field_of_study?: string;
  start_date?: string;
  end_date?: string;
}

export interface Certification {
  name: string;
  issuer?: string;
  date?: string;
}

export interface Language {
  language: string;
  proficiency?: string;
}

/**
 * Actual shape returned by the FastAPI backend (GET/POST /api/v1/profiles).
 * Fields are stored as flat columns on the Profile model, not in a JSONB blob.
 */
export interface ApiProfile {
  id: string;
  source_filename: string;
  name: string | null;
  email: string | null;
  phone: string | null;
  summary: string | null;
  skills: string[];
  work_experience: WorkExperience[];
  education: Education[];
  certifications: Certification[];
  languages: Language[];
  created_at: string;
  updated_at: string;
}
