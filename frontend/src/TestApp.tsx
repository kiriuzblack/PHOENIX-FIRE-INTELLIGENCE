
export default function TestApp() {
  return (
    <main
      style={{
        background: "#060a12",
        color: "white",
        minHeight: "100vh",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        textAlign: "center",
        fontFamily: "Arial, sans-serif",
        padding: "20px"
      }}
    >
      <div style={{ fontSize: "70px" }}>🔥</div>

      <h1 style={{ fontSize: "50px", color: "#ff853b" }}>
        PHOENIX ORBIT
      </h1>

      <h2>FIRE INTELLIGENCE</h2>

      <p>NASA Space Apps Challenge 2026</p>

      <h3 style={{ color: "#44df99" }}>
        ✓ REACT FUNCIONANDO CORRECTAMENTE
      </h3>

      <button
        onClick={() => alert("¡PHOENIX Orbit está funcionando!")}
        style={{
          padding: "15px 25px",
          marginTop: "20px",
          background: "#ff853b",
          color: "#111",
          border: "none",
          borderRadius: "8px",
          cursor: "pointer",
          fontWeight: "bold"
        }}
      >
        PROBAR INTERACTIVIDAD 🚀
      </button>
    </main>
  );
}
