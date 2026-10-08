'use client';

import React from 'react';
import { useVehicleStore } from '@/store/vehicle-store';
import { TRACKS, mmss } from '../hyperos/shared';
import * as Ic from './icons';
import { useHa, STATUS_H, BAR_H } from './theme';
import { useHaLocal } from './shared';

/**
 * Radio and Music, the two sound apps behind the dock's note: the FM tuner as the
 * car draws it (a big tile with the frequency, red ticks, a control row) and a
 * player over the same demo playlist the desktop's media card shows.
 */
export function MediaPage() {
  const { val, setVal } = useHaLocal();
  const t = useHa();
  const radio = val.media === 1;
  const [menu, setMenu] = React.useState(false);

  return (
    <div className="absolute inset-0" style={{ background: t.bg, color: t.text, paddingTop: STATUS_H, paddingBottom: BAR_H }}>
      <div className="relative flex h-full flex-col">
        <div className="relative flex h-[76px] shrink-0 items-center px-[40px]">
          <button
            type="button"
            onClick={() => setMenu((m) => !m)}
            className="flex items-center gap-3 text-[20px] outline-none"
            aria-haspopup="listbox"
            aria-expanded={menu}
          >
            <span className="flex h-[40px] w-[40px] items-center justify-center rounded-full text-white" style={{ background: radio ? '#e8322d' : 'linear-gradient(160deg,#6a7bff,#ff6bd5)' }}>
              {radio ? <Ic.Signal size={20} /> : <Ic.Music size={20} />}
            </span>
            {radio ? 'Radio' : 'Music'}
            <Ic.Chev dir="d" size={13} />
          </button>
          {menu && (
            <ul role="listbox" className="absolute left-[34px] top-[66px] z-10 w-[220px] rounded-[22px] p-2 text-[19px]" style={{ background: t.panel, backdropFilter: 'blur(24px)' }}>
              {[['Music', 0], ['Radio', 1]].map(([l, v]) => (
                <li key={l as string} role="option" aria-selected={val.media === v}>
                  <button type="button" onClick={() => { setVal('media', v as number); setMenu(false); }} className="h-[50px] w-full rounded-[14px] px-4 text-left outline-none" style={{ background: val.media === v ? t.seg : 'transparent' }}>{l}</button>
                </li>
              ))}
            </ul>
          )}
          <div className="absolute left-1/2 flex -translate-x-1/2 gap-[84px] text-[20px]">
            {(radio ? ['FM broadcast', 'Online radio', 'Mine'] : ['Now playing', 'Playlist', 'Mine']).map((l, i) => (
              <span key={l} className="relative pb-2" style={{ color: i === 0 ? (radio ? '#e8322d' : t.text) : t.text2 }}>
                {l}
                {i === 0 && <span className="absolute inset-x-0 bottom-0 h-[3px] rounded-full" style={{ background: radio ? '#e8322d' : t.text }} />}
              </span>
            ))}
          </div>
          <span className="ml-auto" style={{ color: t.text }}><Ic.Search size={30} /></span>
        </div>
        {radio ? <Radio /> : <Player />}
      </div>
    </div>
  );
}

/* --------------------------------------------------------------------- radio */

const STATIONS = [87.5, 90.0, 93.6, 96.0, 99.4, 101.7, 104.3, 107.0];

function Radio() {
  const t = useHa();
  const { media, patchMedia } = useVehicleStore();
  const { val, setVal } = useHaLocal();
  const [fav, setFav] = React.useState(false);
  const idx = Math.min(STATIONS.length - 1, Math.max(0, val.station));
  const f = STATIONS[idx];
  const go = (d: number) => setVal('station', (idx + d + STATIONS.length) % STATIONS.length);

  return (
    <div className="relative flex min-h-0 flex-1 flex-col items-center">
      <div className="mt-[34px] text-[30px] font-medium tracking-wide">{f.toFixed(1)} MHz</div>
      <div className="mt-[16px] h-[56px] w-[3px] rounded-full" style={{ background: '#e8322d' }} />
      <div className="my-[6px] flex h-[170px] w-[170px] flex-col items-center justify-center rounded-[34px]" style={{ background: t.card }}>
        <div className="flex items-baseline gap-2"><span className="text-[34px] font-extrabold">FM</span><span className="text-[17px] font-semibold tracking-wide">RADIO</span></div>
        <div className="tnum text-[56px] font-light leading-none" style={{ color: '#3d6fb0' }}>{f.toFixed(1)}</div>
      </div>
      <div className="h-[56px] w-[3px] rounded-full" style={{ background: '#e8322d', opacity: 0.5 }} />
      <div className="mt-auto flex items-center justify-center gap-[56px] pb-[38px]">
        <span className="flex items-center gap-1 text-[20px]" style={{ color: t.text2 }}>FM <Ic.Chev dir="d" size={11} /></span>
        <button type="button" aria-label="Favourite" aria-pressed={fav} onClick={() => setFav(!fav)} className="outline-none" style={{ color: fav ? '#e8322d' : t.text }}><Ic.Heart size={34} /></button>
        <button type="button" aria-label="Previous station" onClick={() => go(-1)} className="outline-none"><Ic.Prev size={36} /></button>
        <button type="button" aria-label={media.playing ? 'Pause' : 'Play'} onClick={() => patchMedia({ playing: !media.playing })} className="flex h-[76px] w-[76px] items-center justify-center rounded-full text-white outline-none" style={{ background: '#e8322d' }}>
          {media.playing ? <Ic.Pause size={34} /> : <Ic.Play size={34} />}
        </button>
        <button type="button" aria-label="Next station" onClick={() => go(1)} className="outline-none"><Ic.Next size={36} /></button>
        <span style={{ color: t.text }}><Ic.Timer size={34} /></span>
        <span style={{ color: t.text }}><Ic.MoreV size={28} /></span>
      </div>
    </div>
  );
}

/* -------------------------------------------------------------------- player */

function Player() {
  const t = useHa();
  const { media, patchMedia } = useVehicleStore();
  const track = TRACKS[media.trackIndex % TRACKS.length];
  const [pos, setPos] = React.useState(0);
  React.useEffect(() => {
    setPos(0);
  }, [media.trackIndex]);
  React.useEffect(() => {
    if (!media.playing) return;
    const id = window.setInterval(() => setPos((p) => (p + 1 >= track.duration ? 0 : p + 1)), 1000);
    return () => window.clearInterval(id);
  }, [media.playing, track.duration]);
  const prev = () => patchMedia({ trackIndex: (media.trackIndex + TRACKS.length - 1) % TRACKS.length });
  const next = () => patchMedia({ trackIndex: (media.trackIndex + 1) % TRACKS.length });

  return (
    <div className="relative flex min-h-0 flex-1 items-center gap-[56px] px-[110px]">
      <div className="h-[330px] w-[330px] shrink-0 rounded-[40px] shadow-2xl" style={{ background: track.art, boxShadow: `0 30px 70px ${track.tint}88` }} aria-hidden />
      <div className="min-w-0 flex-1">
        <div className="truncate text-[38px] font-semibold leading-tight">{track.title}</div>
        <div className="mt-1 text-[22px]" style={{ color: t.text2 }}>{track.artist}</div>
        <div className="mt-[34px] h-[6px] overflow-hidden rounded-full" style={{ background: t.seg }}>
          <div className="h-full rounded-full" style={{ width: `${(pos / track.duration) * 100}%`, background: t.text }} />
        </div>
        <div className="tnum mt-2 flex justify-between text-[15px]" style={{ color: t.text2 }}>
          <span>{mmss(pos)}</span>
          <span>{mmss(track.duration)}</span>
        </div>
        <div className="mt-[26px] flex items-center justify-between">
          <Ic.Shuffle size={30} style={{ color: t.text2 }} />
          <button type="button" aria-label="Previous" onClick={prev} className="outline-none"><Ic.Prev size={38} /></button>
          <button type="button" aria-label={media.playing ? 'Pause' : 'Play'} onClick={() => patchMedia({ playing: !media.playing })} className="flex h-[84px] w-[84px] items-center justify-center rounded-full outline-none" style={{ background: t.text, color: t.bg }}>
            {media.playing ? <Ic.Pause size={38} /> : <Ic.Play size={38} />}
          </button>
          <button type="button" aria-label="Next" onClick={next} className="outline-none"><Ic.Next size={38} /></button>
          <Ic.Repeat size={30} style={{ color: t.text2 }} />
        </div>
      </div>
    </div>
  );
}
