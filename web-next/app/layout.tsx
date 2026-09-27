import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import { SiteNav } from "./components/site/SiteNav";
import { SiteFooter } from "./components/site/SiteFooter";
import { StickyDemoFooter } from "./components/site/StickyDemoFooter";
import { DemoModeProvider } from "./context/DemoModeContext";
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
  title: { default: "TestMind AI", template: "%s · TestMind AI" },
  description: "Test-quality dashboard for the RepoGuard engine",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="en" className={`${geistSans.variable} ${geistMono.variable}`}>
      <body>
        <DemoModeProvider>
          <SiteNav />
          {children}
          <SiteFooter />
          <StickyDemoFooter />
        </DemoModeProvider>
      </body>
    </html>
  );
}

