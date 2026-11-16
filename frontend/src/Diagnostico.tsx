
export default function Diagnostico() {
  return (
    <main
      style={{
        minHeight: "100vh",
        background: "#060a12",
        color: "#ffffff",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        flexDirection: "column",
        fontFamily: "Arial, sans-serif",
        textAlign: "center",
        padding: "24px",
      }}
    >
      <div style={{ fontSize: "70px" }}>🔥</div>

      <h1 style={{ fontSize: "clamp(32px, 5vw, 64px)" }}>
        PHOENIX ORBIT
      </h1>

      <p style={{ color: "#ff9258", fontSize: "20px" }}>
        FIRE INTELLIGENCE
      </p>

      <h2 style={{ color: "#56e0a5" }}>
        SISTEMA INICIADO CORRECTAMENTE
      </h2>

      <p>NASA Space Apps Challenge 2026</p>
    </main>
  );
}
