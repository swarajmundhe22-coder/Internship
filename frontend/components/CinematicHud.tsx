import Link from "next/link";
import { ReactNode } from "react";

type HudTone = "primary" | "support" | "alert";

type ChapterHeaderProps = {
  eyebrow: string;
  title: string;
  description?: string;
};

type HudBadgeProps = {
  label: string;
  tone?: HudTone;
};

type TelemetryCardProps = {
  label: string;
  value: string | number;
  detail?: string;
  tone?: HudTone;
};

type TacticalButtonProps = {
  children: ReactNode;
  tone?: HudTone;
  href?: string;
  onClick?: () => void;
  type?: "button" | "submit";
  disabled?: boolean;
};

function toneClass(tone: HudTone): string {
  if (tone === "alert") {
    return "hud-tone-alert";
  }

  if (tone === "support") {
    return "hud-tone-support";
  }

  return "hud-tone-primary";
}

export function ChapterHeader({ eyebrow, title, description }: ChapterHeaderProps) {
  return (
    <header className="chapter-header rhythm-stack" data-cinematic-reveal="true">
      <p className="type-kicker hud-label">{eyebrow}</p>
      <h2 className="type-title text-softwhite">{title}</h2>
      {description && <p className="type-body text-softwhite/75">{description}</p>}
    </header>
  );
}

export function HudBadge({ label, tone = "primary" }: HudBadgeProps) {
  return <span className={`hud-badge ${toneClass(tone)}`}>{label}</span>;
}

export function TelemetryCard({ label, value, detail, tone = "primary" }: TelemetryCardProps) {
  return (
    <article className={`telemetry-card panel-density-tight ${toneClass(tone)}`}>
      <p className="type-kicker hud-label">{label}</p>
      <p className="type-metric text-softwhite">{value}</p>
      {detail && <p className="type-caption text-softwhite/75">{detail}</p>}
    </article>
  );
}

export function TacticalButton({ children, tone = "primary", href, onClick, type = "button", disabled = false }: TacticalButtonProps) {
  const className = `tactical-btn ${toneClass(tone)}`;

  if (href) {
    return (
      <Link href={href} className={className}>
        {children}
      </Link>
    );
  }

  return (
    <button type={type} className={className} onClick={onClick} disabled={disabled}>
      {children}
    </button>
  );
}
