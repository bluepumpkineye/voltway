import { notFound } from 'next/navigation';
import { vehicles, getVehicle, hasModel } from '@/data/vehicles';
import { Showroom } from '@/components/showroom/Showroom';

/** A car opens in the showroom once it has a model and a set of options. */
const showroomCars = () => vehicles.filter((v) => hasModel(v) && v.configurator);

export function generateStaticParams() {
  return showroomCars().map((v) => ({ slug: v.slug }));
}

export async function generateMetadata({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  const v = getVehicle(slug);
  if (!v) return { title: 'Not found — Voltway' };
  return {
    title: `${v.brand} ${v.model} showroom — Voltway`,
    description: `Change the paint and the cabin colour, sit in the driver's seat and check the dimensions of the ${v.brand} ${v.model}.`,
  };
}

export default async function ShowroomPage({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  const vehicle = getVehicle(slug);
  if (!vehicle || !hasModel(vehicle) || !vehicle.configurator) notFound();
  const cars = showroomCars().map((v) => ({ slug: v.slug, label: `${v.brand} ${v.model}` }));
  // keyed on the slug: moving between cars is a fresh mount, a fresh canvas
  return <Showroom key={vehicle.slug} vehicle={vehicle} cars={cars} />;
}
