import { notFound } from 'next/navigation';
import { vehicles, getVehicle } from '@/data/vehicles';
import { LineupCapture } from './LineupCapture';

/**
 * Pipeline tool, not a public page: one car on a transparent background, from a chosen angle, for the landing page's line-up
 * (scripts/landing-shots.mjs screenshots it and writes public/landing/<slug>.webp).
 *
 *   /capture/lineup/<slug>?yaw=deg&pitch=deg&paint=<paint id>
 *
 * yaw 0 looks at the car's nose; a positive yaw moves the camera round to the car's passenger side (the nose points to the right of
 * the picture), a negative one to the driver's side (to the left).
 */
export const metadata = { title: 'Line-up capture — Voltway', robots: { index: false } };

export function generateStaticParams() {
  return vehicles.map((v) => ({ slug: v.slug }));
}

export default async function LineupCapturePage({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  const vehicle = getVehicle(slug);
  // a tool of the build, not part of the published site
  if (!vehicle || process.env.NODE_ENV === 'production') notFound();
  return <LineupCapture vehicle={vehicle} />;
}
