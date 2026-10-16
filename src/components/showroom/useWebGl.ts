'use client';

import React from 'react';

/**
 * Whether the browser can draw the showroom: null until it has been asked (the server renders nothing of the canvas),
 * then true or false. A browser with WebGL switched off would otherwise throw out of the canvas and blank the page.
 */
export function useWebGl(): boolean | null {
  const [ok, setOk] = React.useState<boolean | null>(null);
  React.useEffect(() => {
    try {
      const c = document.createElement('canvas');
      setOk(Boolean(c.getContext('webgl2') || c.getContext('webgl')));
    } catch {
      setOk(false);
    }
  }, []);
  return ok;
}
