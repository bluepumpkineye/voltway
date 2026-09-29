import { notFound } from 'next/navigation';
import { vehicles, getVehicle } from '@/data/vehicles';
import { ViewCapture } from './ViewCapture';

/**
 * Pipeline tool, not a public page: the 3D viewer alone, full window, through
 * a locked camera given in the query string - so a headless browser can
 * screenshot the web render from the same camera as a reference photo or a
 * Blender render (blender/scripts/carkit/qa/web_capture.py).
 *
 *   /capture/view/<slug>?mode=interior&pos=x,y,z&target=x,y,z&fov=deg
 */
export const metadata = { title: 'View capture — Voltway', robots: { index: false } };

export function generateStaticParams() {
  return vehicles.map((v) => ({ slug: v.slug }));
}

export default async function ViewCapturePage({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  const vehicle = getVehicle(slug);
  if (!vehicle) notFound();
  return <ViewCapture vehicle={vehicle} />;
}
