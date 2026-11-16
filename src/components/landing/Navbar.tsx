'use client';

import React, { useEffect, useState } from 'react';
import { Wordmark } from './Wordmark';
import styles from './landing.module.css';

const NAV_LINKS = [
  { href: '#top', label: 'Showroom Orbit' },
  { href: '#models', label: 'The Line-Up' },
  { href: '#capabilities', label: 'Capabilities' },
  { href: '#methodology', label: 'Methodology' },
] as const;

export function Navbar({ carCount }: { carCount: number }) {
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 18);
    onScroll();
    window.addEventListener('scroll', onScroll, { passive: true });
    return () => window.removeEventListener('scroll', onScroll);
  }, []);

  return (
    <nav className={`${styles.navbar} ${scrolled ? styles.navbarScrolled : ''}`} aria-label="Primary navigation">
      <div className={styles.navInner}>
        <a href="#top" className={styles.navLogo} aria-label="Voltway — Back to top">
          <Wordmark idPrefix="nav" staticMark className={styles.navWordmark} />
        </a>

        <ul className={styles.navLinks}>
          {NAV_LINKS.map((item) => (
            <li key={item.href}>
              <a href={item.href} className={styles.navLink}>
                {item.label}
              </a>
            </li>
          ))}
        </ul>

        <div className={styles.navRight}>
          <span className={styles.navBadge}>
            <span className={styles.navBadgeDot} aria-hidden />
            <span>{carCount} Interactive 3D Models</span>
          </span>
          <a href="#models" className={styles.navCta}>
            <span>Explore Line-up</span>
            <span className={styles.navCtaArrow} aria-hidden>
              ↓
            </span>
          </a>
        </div>
      </div>
    </nav>
  );
}
