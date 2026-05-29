import type { Metadata } from "next";
import { Cormorant_Garamond, EB_Garamond, Hanken_Grotesk } from "next/font/google";
import "./globals.css";

const cormorant = Cormorant_Garamond({
  weight: ["500", "600", "700"],
  style: ["normal", "italic"],
  subsets: ["latin"],
  display: "swap",
  variable: "--font-cormorant",
});

const ebGaramond = EB_Garamond({
  weight: ["400", "500"],
  style: ["normal", "italic"],
  subsets: ["latin"],
  display: "swap",
  variable: "--font-eb-garamond",
});

const hanken = Hanken_Grotesk({
  weight: ["400", "500", "600", "700"],
  subsets: ["latin"],
  display: "swap",
  variable: "--font-hanken",
});

export const metadata: Metadata = {
  title: "Lectio — Scripture Companion",
  description:
    "Scripture-grounded Christian AI assistant. Denomination-aware, hallucination-resistant, citation-verified.",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html
      lang="en"
      data-theme="light"
      data-denom="protestant"
      className={`${cormorant.variable} ${ebGaramond.variable} ${hanken.variable}`}
    >
      <body>{children}</body>
    </html>
  );
}
