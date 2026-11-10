
import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Background Studio | AI Video Background Remover",
  description:
    "Remove video backgrounds using open-source AI and replace them with your own custom images.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
