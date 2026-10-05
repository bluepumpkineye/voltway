'use client';

import React from 'react';
import type { PaintOption, TrimOption } from '@/data/vehicles/schema';
import type { DimensionFocus } from '@/store/vehicle-store';
import { GLASS } from './Chrome';

const FOCUS =
  'outline-none focus-visible:ring-2 focus-visible:ring-neutral-900/70 focus-visible:ring-offset-1';

function Dot({
  label,
  selected,
  onClick,
  background,
}: {
  label: string;
  selected: boolean;
  onClick: () => void;
  background: string;
}) {
  return (
    <button
      type="button"
      aria-label={label}
      aria-pressed={selected}
      title={label}
      onClick={onClick}
      style={{ background }}
      className={`relative h-7 w-7 shrink-0 rounded-full ring-1 ring-black/15 transition-transform hover:scale-110 ${FOCUS} ${
        selected ? 'outline outline-2 outline-offset-[3px] outline-neutral-900' : ''
      }`}
    />
  );
}

/**
 * A row of dots and the name of the one selected (the maker's name too).
 *
 * The dots stay put: the name hangs off the row's right edge (below it on a
 * narrow screen) instead of sharing the line, because a centred row whose name
 * changes width shifts every dot under the pointer between clicks.
 */
function Row({
  children,
  name,
  nameZh,
}: {
  children: React.ReactNode;
  name: string;
  nameZh?: string;
}) {
  return (
    <div className="pointer-events-auto relative flex max-w-full flex-col items-center gap-2 md:block">
      <div className={`flex w-fit max-w-full items-center gap-3.5 overflow-x-auto rounded-full px-4 py-2.5 ${GLASS}`}>
        {children}
      </div>
      <div
        aria-live="polite"
        className={`whitespace-nowrap rounded-full px-3.5 py-2 text-[12px] font-medium text-neutral-900 md:absolute md:left-full md:top-1/2 md:ml-2 md:-translate-y-1/2 ${GLASS}`}
      >
        {name}
        {nameZh && <span className="ml-2 font-normal text-neutral-500">{nameZh}</span>}
      </div>
    </div>
  );
}

export function PaintSwatches({
  paints,
  selected,
  onSelect,
}: {
  paints: PaintOption[];
  selected: string;
  onSelect: (id: string) => void;
}) {
  const cur = paints.find((p) => p.id === selected) ?? paints[0];
  return (
    <Row name={cur.name} nameZh={cur.nameZh}>
      {paints.map((p) => (
        <Dot
          key={p.id}
          label={p.name}
          selected={p.id === cur.id}
          onClick={() => onSelect(p.id)}
          background={p.swatch}
        />
      ))}
    </Row>
  );
}

export function TrimSwatches({
  trims,
  selected,
  onSelect,
}: {
  trims: TrimOption[];
  selected: string;
  onSelect: (id: string) => void;
}) {
  const cur = trims.find((t) => t.id === selected) ?? trims[0];
  return (
    <Row name={cur.name} nameZh={cur.nameZh}>
      {trims.map((t) => (
        <Dot
          key={t.id}
          label={t.name}
          selected={t.id === cur.id}
          onClick={() => onSelect(t.id)}
          background={`linear-gradient(135deg, ${t.swatch[0]} 50%, ${t.swatch[1]} 50%)`}
        />
      ))}
    </Row>
  );
}

/** Length / Width / Height, each with the published figure. */
export function DimensionChips({
  items,
  selected,
  onSelect,
}: {
  items: { id: DimensionFocus; label: string; value: string }[];
  selected: DimensionFocus;
  onSelect: (id: DimensionFocus) => void;
}) {
  return (
    <div role="group" aria-label="Dimension" className={`pointer-events-auto flex rounded-full p-1 ${GLASS}`}>
      {items.map((i) => (
        <button
          key={i.id}
          type="button"
          aria-pressed={selected === i.id}
          onClick={() => onSelect(i.id)}
          className={`flex items-baseline gap-2 rounded-full px-4 py-1.5 text-[12px] font-medium transition-colors ${FOCUS} ${
            selected === i.id ? 'bg-neutral-900 text-white' : 'text-neutral-600 hover:text-neutral-900'
          }`}
        >
          {i.label}
          <span className={`tnum text-[11px] font-normal ${selected === i.id ? 'text-white/70' : 'text-neutral-400'}`}>
            {i.value}
          </span>
        </button>
      ))}
    </div>
  );
}
