import "./globals.css";

export const metadata = {
  title: "PMGuru — Idea to PM workspace",
  description: "Turn any idea into a fully-planned project. PM Tool, PLM Report, or Interactive Prototype.",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
