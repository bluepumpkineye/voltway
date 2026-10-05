'use client';

import { usePathname } from 'next/navigation';

/**
 * The site's header and footer frame every page except the showroom, which is
 * a full-bleed stage with its own controls.
 */
export function SiteChrome({ children }: { children: React.ReactNode }) {
  const path = usePathname();
  if (path?.startsWith('/showroom')) return null;
  return <>{children}</>;
}
