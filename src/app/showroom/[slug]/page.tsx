import { redirect } from 'next/navigation';
import { getVehicle } from '@/data/vehicles';
import { Showroom } from '@/components/showroom/Showroom';
import { carMenu, showroomCars } from '@/lib/showroom/cars';

export function generateStaticParams() {
  return showroomCars().map((v) => ({ slug: v.slug }));
}

export async function generateMetadata({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  const v = getVehicle(slug);
  if (!v) return {};
  return {
    title: `${v.brand} ${v.model} — Voltway`,
    description: `Change the paint and the cabin colour, sit in the driver's seat, see what the technology does and check the specifications of the ${v.brand} ${v.model}.`,
  };
}

export default async function ShowroomPage({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  const vehicle = showroomCars().find((v) => v.slug === slug);
  // a car with no showroom (an old link) lands on the first one
  if (!vehicle) redirect('/');
  // keyed on the slug: moving between cars is a fresh mount, a fresh canvas
  return <Showroom key={vehicle.slug} vehicle={vehicle} cars={carMenu()} />;
}
