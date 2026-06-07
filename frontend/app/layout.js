import "./globals.css";

export const metadata = {
  title: "Indian MSME Consulting — Powered by AI",
  description: "AI consulting & operating system for Indian MSMEs — diagnosis, due diligence, compliance, finance, growth and ERP, India-aware (₹ · GST · DPIIT · Udyam).",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
