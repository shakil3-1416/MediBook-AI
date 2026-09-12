import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "MediBook",
  description: "AI hospital appointment assistant",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="m-0 min-h-screen bg-white text-slate-950 antialiased">
        {children}

      </body>
    </html>
  );
}
