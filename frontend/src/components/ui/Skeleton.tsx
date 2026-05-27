import React from "react";

interface SkeletonProps {
  className?: string;
  variant?: "text" | "circular" | "rectangular";
  width?: string | number;
  height?: string | number;
}

const Skeleton: React.FC<SkeletonProps> = ({
  className = "",
  variant = "rectangular",
  width,
  height,
}) => {
  const style: React.CSSProperties = {
    width,
    height,
  };

  const variantClasses = {
    text: "h-4 w-full rounded",
    circular: "rounded-full",
    rectangular: "rounded-xl",
  };

  return (
    <div
      style={style}
      className={`animate-pulse bg-slate-800/60 border border-white/5 ${variantClasses[variant]} ${className}`}
    />
  );
};

export default Skeleton;
