export default function Palco() {
  return (
    <div className="stage" aria-hidden="true">
      <svg viewBox="0 0 400 420" fill="none" strokeLinecap="round" strokeLinejoin="round">
        <line x1="40" y1="388" x2="360" y2="388" stroke="#3A4766" strokeWidth="3" />
        <g stroke="#7F9BFF" strokeWidth="5">
          <line x1="190" y1="70" x2="196" y2="140" /><line x1="196" y1="140" x2="170" y2="236" />
          <line x1="170" y1="236" x2="250" y2="262" /><line x1="250" y1="262" x2="232" y2="386" />
          <line x1="196" y1="140" x2="238" y2="188" /><line x1="238" y1="188" x2="276" y2="164" />
        </g>
        <circle cx="186" cy="48" r="22" stroke="#7F9BFF" strokeWidth="5" />
        <g fill="#E8ECF7">
          <circle cx="196" cy="140" r="7" /><circle cx="170" cy="236" r="7" />
          <circle cx="250" cy="262" r="9" fill="#FF7A63" /><circle cx="232" cy="386" r="7" />
          <circle cx="238" cy="188" r="6" /><circle cx="276" cy="164" r="6" />
        </g>
        <path d="M232 262 A36 36 0 0 0 214 240" stroke="#FF7A63" strokeWidth="3" />
        <text x="268" y="300" fill="#FF7A63" fontSize="26" fontWeight="800" stroke="none">92°</text>
        <text x="268" y="322" fill="#98A6CC" fontSize="13" stroke="none">joelho</text>
      </svg>
      <div className="cap"></div>
    </div>
  );
}
