import { useEffect } from "react";
import "./LabEntrance.css";

type LabEntranceProps = {
  onComplete: () => void;
};

export default function LabEntrance({
  onComplete,
}: LabEntranceProps) {
  useEffect(() => {
    if (
      window.matchMedia(
        "(prefers-reduced-motion: reduce)"
      ).matches
    ) {
      onComplete();
    }
  }, [onComplete]);

  return (
    <div
      className="lab-entry"
      aria-hidden="true"
      onAnimationEnd={(event) => {
        if (event.target === event.currentTarget) {
          onComplete();
        }
      }}
    >
      <div className="lab-entry-tunnel">
        <div className="lab-entry-ring ring-1" />
        <div className="lab-entry-ring ring-2" />
        <div className="lab-entry-ring ring-3" />

        <div className="lab-entry-core">
          <span>PHOENIX</span>
          <strong>LAB / ACCESS</strong>
        </div>
      </div>

      <div className="lab-entry-door lab-entry-left" />
      <div className="lab-entry-door lab-entry-right" />

      <div className="lab-entry-caption">
        <span>PHOENIX FIRE INTELLIGENCE</span>
        <strong>ENTERING RESEARCH LAB</strong>
        <small>INITIALIZING SCIENTIFIC INTERFACE</small>
      </div>

      <div className="lab-entry-bottom">
        MICROGRAVITY RESEARCH / 2026
      </div>
    </div>
  );
}
