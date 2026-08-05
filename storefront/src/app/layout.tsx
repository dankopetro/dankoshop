import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import Header from "@/components/header";
import Footer from "@/components/footer";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: {
    default: "DankoShop - Tu tienda online",
    template: "%s | DankoShop",
  },
  description: "Productos de tecnología, hogar, outdoor y más. Envíos a todo el país.",
  keywords: ["ecommerce", "tecnología", "hogar", "outdoor", "Argentina"],
  authors: [{ name: "DankoShop" }],
  creator: "DankoShop",
  publisher: "DankoShop",
  robots: "index, follow",
  openGraph: {
    type: "website",
    locale: "es_AR",
    url: "https://dankoshop.vercel.app",
    siteName: "DankoShop",
    title: "DankoShop - Tu tienda online",
    description: "Productos de tecnología, hogar, outdoor y más. Envíos a todo el país.",
  },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="es" className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}>
      <body className="min-h-full flex flex-col bg-gray-50">
        <Header />
        <main className="flex-1">{children}</main>
        <Footer />
      </body>
    </html>
  );
}