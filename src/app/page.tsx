import { Showroom } from '@/components/showroom/Showroom';
import { carMenu, defaultCar } from '@/lib/showroom/cars';

/** The landing page is the showroom, on the first car; the others are one tap away in its car menu. */
export default function HomePage() {
  const vehicle = defaultCar();
  return <Showroom key={vehicle.slug} vehicle={vehicle} cars={carMenu()} />;
}
