import type { Metadata } from 'next';
import { Landing } from '@/components/landing/Landing';

export const metadata: Metadata = {
  title: 'Voltway — The Digital Showroom',
  description: 'Nine Chinese electric cars in 3D. Pick one, change the paint, sit inside, run it down the road and check the specifications.',
};

/** The way in: the whole line-up on one scene. A car opens in its own showroom (src/app/showroom/[slug]). */
export default function HomePage() {
  return <Landing />;
}
