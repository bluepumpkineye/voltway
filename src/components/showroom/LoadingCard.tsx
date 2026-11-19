/**
 * The showroom's loading card: what is being waited for, and how far along it is when that is known (a number for the files
 * coming over the network, a sweeping bar for the work after them: building the scene, compiling the shaders).
 *
 * Pure markup with no state, so that the route's own loading screen and the viewer's loader can share it. `delayMs` holds the
 * card back so that a wait that ends at once never shows it; the fade is a CSS animation, so it still runs when the page is
 * busy and the card appears on time while the page is blocked.
 */
export function LoadingCardView({
  label,
  detail,
  percent,
  delayMs = 0,
  instant = false,
}: {
  label: string;
  detail?: string;
  /** 0-100 when the wait is measured; the bar sweeps when it is not */
  percent?: number | null;
  delayMs?: number;
  /** no fade: for a card that takes the place of another one */
  instant?: boolean;
}) {
  const measured = typeof percent === 'number';
  return (
    <div
      role="status"
      aria-live="polite"
      className="loading-card pointer-events-none flex w-[min(300px,calc(100vw-48px))] flex-col gap-3 rounded-2xl bg-white/90 px-5 py-4 text-neutral-900 shadow-[0_12px_36px_-12px_rgba(20,24,32,0.32)] ring-1 ring-black/[0.06] backdrop-blur-xl"
      style={instant ? { animation: 'none' } : { animationDelay: `${delayMs}ms` }}
    >
      <div className="flex items-baseline justify-between gap-3">
        <span className="text-[13px] font-medium">{label}</span>
        {measured && <span className="tnum text-[12px] text-neutral-500">{Math.round(percent)}%</span>}
      </div>
      <div className="h-[3px] overflow-hidden rounded-full bg-black/10">
        {measured ? (
          <div className="h-full rounded-full bg-neutral-800 transition-[width] duration-200 ease-out" style={{ width: `${Math.max(3, Math.min(100, percent))}%` }} />
        ) : (
          <div className="h-full w-1/3 rounded-full bg-neutral-800 animate-sweep" />
        )}
      </div>
      {detail && <p className="text-[11px] leading-snug text-neutral-500">{detail}</p>}
    </div>
  );
}
