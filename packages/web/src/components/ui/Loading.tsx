/**
 * Skeleton Component
 * Loading state placeholder
 */

import { type HTMLAttributes } from "react";

type SkeletonProps = HTMLAttributes<HTMLDivElement> & {
  width?: string;
  height?: string;
  count?: number;
};

export function Skeleton({
  width = "100%",
  height = "1rem",
  count = 1,
  className = "",
  ...props
}: SkeletonProps) {
  return (
    <>
      {Array.from({ length: count }).map((_, i) => (
        <div
          key={i}
          className={`ltc-skeleton ${className}`.trim()}
          style={{ width, height }}
          {...props}
        />
      ))}
    </>
  );
}
