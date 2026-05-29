import React from "react";

interface IconProps {
  size?: number;
  sw?: number;
  fill?: string;
  className?: string;
}

const I = ({
  size = 18,
  sw = 1.6,
  fill = "none",
  className,
  children,
}: React.PropsWithChildren<IconProps>) => (
  <svg
    width={size}
    height={size}
    viewBox="0 0 24 24"
    fill={fill}
    stroke="currentColor"
    strokeWidth={sw}
    strokeLinecap="round"
    strokeLinejoin="round"
    className={className}
  >
    {children}
  </svg>
);

// Denomination crosses
export const CrossLatin = (p: IconProps) => (
  <I {...p}><path d="M12 3v18M7 8h10" /></I>
);
export const CrossCrucifix = (p: IconProps) => (
  <I {...p}><path d="M12 3v18M7 9h10M10 5.5h4" /></I>
);
export const CrossOrthodox = (p: IconProps) => (
  <I {...p}><path d="M12 3v18M9.5 6h5M7 9.5h10M9 16l6-3" /></I>
);

export const DENOM_ICON: Record<string, (p: IconProps) => React.ReactElement> = {
  protestant: CrossLatin,
  catholic: CrossCrucifix,
  orthodox: CrossOrthodox,
};

// UI glyphs
export const IcSend = (p: IconProps) => (
  <I {...p}><path d="M5 12h14M13 6l6 6-6 6" /></I>
);
export const IcSun = (p: IconProps) => (
  <I {...p}>
    <circle cx="12" cy="12" r="4.2" />
    <path d="M12 2v2.5M12 19.5V22M2 12h2.5M19.5 12H22M4.9 4.9l1.8 1.8M17.3 17.3l1.8 1.8M19.1 4.9l-1.8 1.8M6.7 17.3l-1.8 1.8" />
  </I>
);
export const IcMoon = (p: IconProps) => (
  <I {...p}><path d="M20 13.5A8 8 0 1 1 10.5 4a6.3 6.3 0 0 0 9.5 9.5z" /></I>
);
export const IcPlus = (p: IconProps) => (
  <I {...p}><path d="M12 5v14M5 12h14" /></I>
);
export const IcCheck = (p: IconProps) => (
  <I {...p}><path d="M4 12.5l5 5L20 6" /></I>
);
export const IcCheckSeal = (p: IconProps) => (
  <I {...p}>
    <path d="M12 2.5l2.4 1.5 2.8-.3 1.1 2.6 2.3 1.7-.8 2.7.8 2.7-2.3 1.7-1.1 2.6-2.8-.3L12 21.5 9.6 20l-2.8.3-1.1-2.6L3.4 16l.8-2.7L3.4 10.6 5.7 8.9l1.1-2.6 2.8.3z" />
    <path d="M8.5 12l2.3 2.3 4.7-4.6" />
  </I>
);
export const IcChevron = (p: IconProps) => (
  <I {...p}><path d="M6 9l6 6 6-6" /></I>
);
export const IcImage = (p: IconProps) => (
  <I {...p}>
    <rect x="3.5" y="4.5" width="17" height="15" rx="2.5" />
    <circle cx="8.5" cy="9.5" r="1.6" />
    <path d="M5 17l4.5-4.5L13 16l3-3 3 3" />
  </I>
);
export const IcBook = (p: IconProps) => (
  <I {...p}>
    <path d="M12 5.5C10.5 4.3 8 4 5 4.5v13c3-.5 5.5-.2 7 1 1.5-1.2 4-1.5 7-1v-13c-3-.5-5.5-.2-7 1z" />
    <path d="M12 5.5v13" />
  </I>
);
export const IcColumns = (p: IconProps) => (
  <I {...p}>
    <path d="M5 5v14M19 5v14M12 6v12" />
    <path d="M5 5h14M5 19h14" />
  </I>
);
export const IcDove = (p: IconProps) => (
  <I {...p}>
    <path d="M5 14c3 0 5-2 6-5 .8 2 2 3 4 3 0-3-2-7-6-7-3 0-5 2.5-5 5.5 0 .9-.5 1.8-2 2.5 1 1 2 1 3 1z" />
    <path d="M11 9c2 2 5 3 8 2" />
  </I>
);
export const IcShieldSlash = (p: IconProps) => (
  <I {...p}>
    <path d="M12 3l7 2.5v5c0 4.5-3 8-7 9.5-4-1.5-7-5-7-9.5v-5z" />
    <path d="M9 12.5h6" />
  </I>
);
export const IcSlash = (p: IconProps) => (
  <I {...p}>
    <circle cx="12" cy="12" r="8.5" />
    <path d="M6 6l12 12" />
  </I>
);
export const IcFlame = (p: IconProps) => (
  <I {...p}>
    <path d="M12 3c0 3-4 4-4 8a4 4 0 0 0 8 0c0-1.5-1-2.5-1-4 1.5 1 2 2.5 2 4a5 5 0 0 1-10 0c0-4 4-5 5-8z" />
  </I>
);
