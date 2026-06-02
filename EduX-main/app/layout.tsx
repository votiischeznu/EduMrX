import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import Provider from "@/components/Provider";

import "bootstrap-icons/font/bootstrap-icons.css";

import "leaflet/dist/leaflet.css";


const inter = Inter({
  variable: "--font-inter",
  subsets: ["latin"],
});


export const metadata: Metadata = {
  title: "EduX — O'quv Markaz Boshqaruv Tizimi",
  description:
    "EduX — o'quv markazlari uchun zamonaviy CRM tizimi. O'quvchilar, o'qituvchilar, to'lovlar, davomat va uy vazifalarini bitta platformada boshqaring.",
  keywords: [
    "o'quv markaz CRM",
    "talaba boshqaruvi",
    "davomat tizimi",
    "to'lov tizimi",
    "IELTS markaz",
    "IT akademiya",
    "EduX",
  ],
  openGraph: {
    title: "EduX — O'quv Markaz Boshqaruv Tizimi",
    description:
      "O'quvchilar, guruhlar, to'lovlar va davomatni bitta joyda boshqaring.",
    type: "website",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className={`${inter.variable} antialiased`}>
        <Provider>{children}</Provider>
      </body>
    </html>
  );
}