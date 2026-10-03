import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "OncoJev Observability",
  description: "Read-only observability for an autonomous oncology laboratory.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <div className="shell">
          <header className="topbar">
            <strong>OncoJev</strong>
            <span>observability - read-only - no research logic in the frontend</span>
          </header>
          {children}
        </div>
      </body>
    </html>
  );
}
