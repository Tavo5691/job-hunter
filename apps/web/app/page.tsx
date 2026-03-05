"use client";

import { useState, useCallback, ChangeEvent } from "react";
import { useRouter } from "next/navigation";

type UploadState =
  | { status: "idle" }
  | { status: "dragging" }
  | { status: "uploading"; filename: string }
  | { status: "error"; message: string };

export default function UploadPage() {
  const [state, setState] = useState<UploadState>({ status: "idle" });
  const router = useRouter();

  const handleFile = useCallback(
    async (file: File) => {
      if (!file.name.toLowerCase().endsWith(".pdf")) {
        setState({ status: "error", message: "Only PDF files are supported." });
        return;
      }
      if (file.size > 10 * 1024 * 1024) {
        setState({ status: "error", message: "File exceeds 10 MB limit." });
        return;
      }

      setState({ status: "uploading", filename: file.name });

      try {
        const formData = new FormData();
        formData.append("file", file);

        const response = await fetch("/api/profiles", {
          method: "POST",
          body: formData,
        });

        if (!response.ok) {
          const err = await response.json().catch(() => ({ detail: "Unknown error" }));
          setState({
            status: "error",
            message: err.detail ?? `Upload failed: HTTP ${response.status}`,
          });
          return;
        }

        const profile = await response.json();
        router.push(`/profiles/${profile.id}`);
      } catch {
        setState({
          status: "error",
          message: "Network error — is the API running?",
        });
      }
    },
    [router]
  );

  const onDrop = useCallback(
    (e: React.DragEvent<HTMLLabelElement>) => {
      e.preventDefault();
      const file = e.dataTransfer.files[0];
      if (file) handleFile(file);
      else setState({ status: "idle" });
    },
    [handleFile]
  );

  const onDragOver = useCallback((e: React.DragEvent<HTMLLabelElement>) => {
    e.preventDefault();
    setState((s) => (s.status === "dragging" ? s : { status: "dragging" }));
  }, []);

  const onDragLeave = useCallback(() => {
    setState((s) => (s.status === "dragging" ? { status: "idle" } : s));
  }, []);

  const onInputChange = useCallback(
    (e: ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (file) handleFile(file);
    },
    [handleFile]
  );

  const isUploading = state.status === "uploading";
  const isDragging = state.status === "dragging";

  return (
    <div className="flex flex-col items-center gap-8 py-12">
      <div className="text-center">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Upload your CV</h1>
        <p className="text-gray-500">
          Upload a PDF and we&apos;ll extract your developer profile automatically.
        </p>
      </div>

      {/* Drop zone */}
      <label
        htmlFor="cv-upload"
        className={`w-full max-w-xl cursor-pointer rounded-2xl border-2 border-dashed transition-colors ${
          isDragging
            ? "border-blue-500 bg-blue-50"
            : "border-gray-300 bg-white hover:border-gray-400"
        } ${isUploading ? "pointer-events-none opacity-60" : ""}`}
        onDrop={onDrop}
        onDragOver={onDragOver}
        onDragLeave={onDragLeave}
      >
        <div className="flex flex-col items-center gap-4 px-8 py-16">
          {isUploading ? (
            <>
              <div className="h-10 w-10 rounded-full border-4 border-blue-500 border-t-transparent animate-spin" />
              <p className="text-gray-600">
                Extracting profile from{" "}
                <span className="font-medium">{(state as { filename: string }).filename}</span>
                …
              </p>
              <p className="text-sm text-gray-400">This may take up to 60 seconds</p>
            </>
          ) : (
            <>
              <div className="text-4xl">📄</div>
              <div className="text-center">
                <p className="font-medium text-gray-700">
                  {isDragging ? "Drop your PDF here" : "Drag & drop your PDF here"}
                </p>
                <p className="text-sm text-gray-400 mt-1">or click to browse</p>
              </div>
              <p className="text-xs text-gray-400">PDF only · Max 10 MB</p>
            </>
          )}
        </div>
        <input
          id="cv-upload"
          type="file"
          accept=".pdf,application/pdf"
          className="hidden"
          onChange={onInputChange}
          disabled={isUploading}
        />
      </label>

      {/* Error message */}
      {state.status === "error" && (
        <div className="w-full max-w-xl rounded-lg bg-red-50 border border-red-200 px-4 py-3 text-sm text-red-700 flex items-start gap-2">
          <span className="mt-0.5">⚠️</span>
          <span>{state.message}</span>
          <button
            onClick={() => setState({ status: "idle" })}
            className="ml-auto text-red-400 hover:text-red-600"
          >
            ✕
          </button>
        </div>
      )}

      <p className="text-sm text-gray-400">
        Already have a profile?{" "}
        <a href="/profiles" className="text-blue-600 hover:underline">
          View all profiles →
        </a>
      </p>
    </div>
  );
}
