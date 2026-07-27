import type { Metadata } from "next";
import "./globals.css";
import { LenisProvider } from "@/lib/lenis";
import { Navigation } from "@/components/nav/Navigation";
import { Footer } from "@/components/ui/Footer";

export const metadata: Metadata = {
  title: "KILTER — Active MCP Server Drift Detection & Automated Remediation",
  description: "Autonomous multi-layer metrology for Model Context Protocol (MCP) server infrastructures. Preventing silent breaking changes before production fails.",
  icons: {
    icon: "/favicon.svg",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="scroll-smooth">
      <body className="antialiased min-h-screen flex flex-col bg-[#FDFBF7] text-[#1A1B1E]">
        <LenisProvider>
          <Navigation />
          <main className="flex-1 w-full pt-20">
            {children}
          </main>
          <Footer />
        </LenisProvider>
      </body>
    </html>
  );
}
