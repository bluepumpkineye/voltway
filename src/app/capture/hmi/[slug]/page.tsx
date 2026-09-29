import { notFound } from 'next/navigation';
import { vehicles, getVehicle } from '@/data/vehicles';
import { HmiCapture } from './HmiCapture';

/**
 * Pipeline tool, not a public page: the vehicle's HMI at native size for
 * capturing as a render texture (see blender/scripts/carkit/qa/hmi_capture.py
 * and docs/3d-pipeline.md).
 */
export const metadata = { title: 'HMI capture — Voltway', robots: { index: false } };

export function generateStaticParams() {
  return vehicles.map((v) => ({ slug: v.slug }));
}

export default async function HmiCapturePage({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  const vehicle = getVehicle(slug);
  if (!vehicle) notFound();
  return <HmiCapture vehicle={vehicle} />;
}
