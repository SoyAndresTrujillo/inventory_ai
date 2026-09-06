import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import Link from "next/link";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Inventory + AI",
  description: "Inventory management with an AI assistant",
};

const NAV = [
  { href: "/", label: "Products" },
  { href: "/categories", label: "Categories" },
  { href: "/templates", label: "Templates" },
  { href: "/chat", label: "AI" },
];

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col font-sans">
        <header className="border-b border-line bg-surface">
          <nav className="mx-auto flex max-w-5xl items-center gap-1 px-5 py-3">
            <Link href="/" className="mr-4 font-semibold tracking-tight">
              Inventory<span className="text-accent">+AI</span>
            </Link>
            {NAV.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                className="rounded-xl px-3 py-1.5 text-sm text-muted transition hover:bg-background hover:text-foreground"
              >
                {item.label}
              </Link>
            ))}
          </nav>
        </header>
        <main className="mx-auto w-full max-w-5xl flex-1 px-5 py-8">{children}</main>
      </body>
    </html>
  );
}
