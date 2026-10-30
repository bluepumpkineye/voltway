import type { Metadata, Viewport } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'Voltway — The Digital Showroom',
  description:
    'Walk round the best Chinese electric vehicles in 3D: change the paint, sit inside, use the real dashboard, see what the technology does and check the specifications.',
};

export const viewport: Viewport = {
  width: 'device-width',
  initialScale: 1,
  themeColor: '#f1f2f4',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-[#f1f2f4] text-neutral-900 antialiased">{children}</body>
    </html>
  );
}
