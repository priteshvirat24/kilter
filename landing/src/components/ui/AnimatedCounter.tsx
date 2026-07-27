'use client';

import React, { useEffect, useState, useRef } from 'react';
import { useInView } from 'framer-motion';

interface AnimatedCounterProps {
  from?: number;
  to: number;
  decimals?: number;
  prefix?: string;
  suffix?: string;
  duration?: number;
}

export const AnimatedCounter: React.FC<AnimatedCounterProps> = ({
  from = 0,
  to,
  decimals = 0,
  prefix = '',
  suffix = '',
  duration = 2.0,
}) => {
  const ref = useRef<HTMLSpanElement>(null);
  const isInView = useInView(ref, { once: true, margin: '-20px' });
  const [value, setValue] = useState(from);

  useEffect(() => {
    if (!isInView) return;

    let start: number | null = null;
    const endValue = to;
    const diff = endValue - from;

    const step = (timestamp: number) => {
      if (!start) start = timestamp;
      const progress = Math.min((timestamp - start) / (duration * 1000), 1);
      // Cubic ease out curve
      const easeProgress = 1 - Math.pow(1 - progress, 3);
      setValue(from + diff * easeProgress);

      if (progress < 1) {
        requestAnimationFrame(step);
      }
    };

    requestAnimationFrame(step);
  }, [isInView, from, to, duration]);

  return (
    <span ref={ref} className="font-mono font-black tracking-tight text-inherit">
      {prefix}
      {value.toFixed(decimals)}
      {suffix}
    </span>
  );
};
