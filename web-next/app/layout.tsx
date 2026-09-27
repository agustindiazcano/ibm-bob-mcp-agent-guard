import type { Metadata } from "next";
import { Geist, Geist_Mono, Raleway } from "next/font/google";
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

const raleway = Raleway({
  variable: "--font-raleway",
  subsets: ["latin"],
  weight: ["100", "200", "300", "400", "500", "600", "700", "800", "900"],
});

export const metadata: Metadata = {
  title: { default: "TestMind AI", template: "%s · TestMind AI" },
  description: "Test-quality dashboard for the RepoGuard engine",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${geistSans.variable} ${geistMono.variable} ${raleway.variable}`}>
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
