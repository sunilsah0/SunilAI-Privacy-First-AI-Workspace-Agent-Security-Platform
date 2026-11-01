export type IconName = "chat" | "file" | "building" | "agent" | "data" | "shield";

const PATHS: Record<IconName, string> = {
  chat: "M4 5h16v11H9l-5 4V5z",
  file: "M7 3h7l5 5v13H7V3zM14 3v5h5",
  building: "M4 21V5l8-2 8 2v16M9 9h2M13 9h2M9 13h2M13 13h2M10 21v-4h4v4",
  agent: "M12 3v3M7 8h10a3 3 0 013 3v5a3 3 0 01-3 3H7a3 3 0 01-3-3v-5a3 3 0 013-3zM9 13h.01M15 13h.01M9 17h6",
  data: "M4 6c0-1.7 3.6-3 8-3s8 1.3 8 3-3.6 3-8 3-8-1.3-8-3zM4 6v12c0 1.7 3.6 3 8 3s8-1.3 8-3V6M4 12c0 1.7 3.6 3 8 3s8-1.3 8-3",
  shield: "M12 3l8 3v5c0 5-3.4 8.6-8 10-4.6-1.4-8-5-8-10V6l8-3zM9 12l2 2 4-4",
};

export function Icon({ name, size = 20 }: { name: IconName; size?: number }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={1.8}
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      focusable="false"
    >
      <path d={PATHS[name]} />
    </svg>
  );
}
