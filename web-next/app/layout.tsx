import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import { SiteNav } from "./components/site/SiteNav";
import { SiteFooter } from "./components/site/SiteFooter";
import { StickyDemoFooter } from "./components/site/StickyDemoFooter";
import { DemoModeProvider } from "./context/DemoModeContext";
import { ConfigProvider } from "./context/ConfigContext";
import { ConfigModal } from "./components/ConfigModal";
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

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${geistSans.variable} ${geistMono.variable}`}>
      <body>
        <ConfigProvider>
          <DemoModeProvider>
            <SiteNav />
            {children}
            <SiteFooter />
            <StickyDemoFooter />
            <ConfigModal />
          </DemoModeProvider>
        </ConfigProvider>
      </body>
    </html>
  );
}

