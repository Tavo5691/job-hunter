import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "job-hunter",
  description: "Developer-focused job hunting assistant — upload your CV, track your profile",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-gray-50 antialiased">
        <header className="bg-white border-b border-gray-200 px-6 py-4">
          <div className="max-w-4xl mx-auto flex items-center justify-between">
            <a href="/" className="text-xl font-bold text-gray-900">
              job-hunter
            </a>
            <nav className="flex gap-4 text-sm text-gray-600">
              <a href="/" className="hover:text-gray-900 transition-colors">
                Upload CV
              </a>
              <a href="/profiles" className="hover:text-gray-900 transition-colors">
                Profiles
              </a>
            </nav>
          </div>
        </header>
        <main className="max-w-4xl mx-auto px-6 py-8">{children}</main>
      </body>
    </html>
  );
}
