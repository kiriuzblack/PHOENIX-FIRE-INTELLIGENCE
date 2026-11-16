import { useEffect, useRef, useState } from "react";
import { ArrowDown, ArrowUpRight, Flame, X } from "lucide-react";
import gsap from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import Scene3D from "./components/Scene3D";
import "./App.css";
import AIChat from "./components/AIChat";
import DataDashboard from "./components/DataDashboard";
import ExperimentCharts from "./components/ExperimentCharts";
import LabEntrance from "./components/LabEntrance";


gsap.registerPlugin(ScrollTrigger);

const experiments = [
  {
    id: "BASS",
    name: "Burning and Suppression of Solids",
    category: "COMBUSTIBLES SÓLIDOS",
    description:
      "Investigaciones sobre propagación y extinción de llamas en materiales sólidos bajo microgravedad.",
    source: "https://ntrs.nasa.gov/",
  },
  {
    id: "FLEX",
    name: "Flame Extinguishment Experiment",
    category: "COMBUSTIÓN DE GOTAS",
    description:
      "Experimentos que estudian la combustión y extinción de gotas de combustible y fenómenos como las llamas frías.",
    source: "https://psi.nasa.gov/",
  },
  {
    id: "SAFFIRE",
    name: "Spacecraft Fire Safety",
    category: "SEGURIDAD ESPACIAL",
    description:
      "Investigaciones de propagación de incendios a mayor escala en vehículos espaciales no tripulados.",
    source: "https://ntrs.nasa.gov/",
  },
];

const sections = [
  ["intro", "01"],
  ["archive", "02"],
  ["research", "03"],
  ["corridor", "04"],
  ["finale", "05"],
] as const;

export default function App() {
  const root = useRef<HTMLDivElement>(null);
  const progress = useRef(0);
  const labZoom = useRef({ value: 0 });
  const entryTimeline = useRef<gsap.core.Timeline | null>(null);

  const [active, setActive] = useState(0);
  const [selected, setSelected] = useState(0);
  const [labOpen, setLabOpen] = useState(false);
  const [enteringLab, setEnteringLab] = useState(false);
  const [doorsPlaying, setDoorsPlaying] = useState(false);
  const [search, setSearch] = useState("");
  const [compareA, setCompareA] = useState("BASS");
  const [compareB, setCompareB] = useState("SAFFIRE");

  useEffect(() => {
    if (!root.current) return;

    const context = gsap.context(() => {
      ScrollTrigger.create({
        trigger: root.current,
        start: "top top",
        end: "bottom bottom",
        onUpdate: (self) => {
          progress.current = self.progress;

          const index = Math.min(
            4,
            Math.floor(self.progress * 4 + 0.5)
          );

          setActive((previous) =>
            previous === index ? previous : index
          );
        },
      });

      gsap.utils.toArray<HTMLElement>(".animate-in").forEach((element) => {
        gsap.fromTo(
          element,
          { autoAlpha: 0, y: 65 },
          {
            autoAlpha: 1,
            y: 0,
            duration: 1.15,
            ease: "power3.out",
            scrollTrigger: {
              trigger: element,
              start: "top 85%",
              toggleActions: "play none none reverse",
            },
          }
        );
      });
    }, root);

    return () => context.revert();
  }, []);

  useEffect(() => {
    document.body.style.overflow = labOpen || enteringLab ? "hidden" : "";
    return () => {
      document.body.style.overflow = "";
    };
  }, [labOpen, enteringLab]);

  useEffect(() => {
    function onKeyDown(e: KeyboardEvent) {
      if (e.key === "Escape") closeLab();
    }

    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, []);


  function enterLab() {
    if (labOpen || enteringLab) return;

    const reducedMotion = window.matchMedia(
      "(prefers-reduced-motion: reduce)"
    ).matches;

    if (reducedMotion) {
      setLabOpen(true);
      return;
    }

    // Todos los accesos parten de la escena final.
    const finale = document.getElementById("finale");

    if (finale) {
      const top =
        window.scrollY +
        finale.getBoundingClientRect().top;

      window.scrollTo({ top, behavior: "auto" });
      progress.current = 1;
      ScrollTrigger.update();
    }

    labZoom.current.value = 0;
    setEnteringLab(true);

    const disappearing = gsap.utils.toArray<HTMLElement>(
      ".top-navigation, .chapter-indicator, " +
      ".finale-content, .finale-footer"
    );

    entryTimeline.current?.kill();

    entryTimeline.current = gsap.timeline({
      onComplete: () => {
        setEnteringLab(false);
        setLabOpen(true);
        setDoorsPlaying(true);
      },
    });

    entryTimeline.current
      .to(
        disappearing,
        {
          autoAlpha: 0,
          y: -35,
          duration: 0.65,
          stagger: 0.035,
          ease: "power2.in",
          overwrite: true,
        },
        0
      )
      
        .to(
         labZoom.current,
          {
           value: 1,
          duration: 3.1,
           ease: "none",
           overwrite: true,
           },
           0
          );

  }

  function closeLab() {
    entryTimeline.current?.kill();

    setLabOpen(false);
    setDoorsPlaying(false);
    setEnteringLab(false);

    labZoom.current.value = 0;

    gsap.to(
      ".top-navigation, .chapter-indicator, " +
      ".finale-content, .finale-footer",
      {
        autoAlpha: 1,
        y: 0,
        duration: 0.5,
        ease: "power2.out",
        overwrite: true,
      }
    );
  }

  function goTo(id: string) {
    document.getElementById(id)?.scrollIntoView({
      behavior: "smooth",
      block: "start",
    });
  }

  function exportComparison() {
    const a = experiments.find((item) => item.id === compareA);
    const b = experiments.find((item) => item.id === compareB);

    const report = {
      project: "PHOENIX FIRE INTELLIGENCE",
      version: "0.1-demo",
      type: "Descriptive comparison",
      scientific_validation: false,
      experiments: [a, b],
    };

    const blob = new Blob([JSON.stringify(report, null, 2)], {
      type: "application/json",
    });

    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = "phoenix-comparison.json";
    link.click();
    URL.revokeObjectURL(url);
  }

  const current = experiments[selected];
  const results = experiments.filter((item) =>
    `${item.id} ${item.name} ${item.description}`
      .toLowerCase()
      .includes(search.toLowerCase())
  );

  return (
    <div className="experience" ref={root}>
      <div className="webgl-layer" aria-hidden="true">

      {enteringLab && (
          <div
          className="lab-portal-transition"
        aria-hidden="true"
         >
           <div className="lab-portal-glow" />
         </div>
        )}

        <Scene3D progress={progress} selected={selected} labZoom={labZoom} />
      </div>

      <header className="top-navigation">
        <button className="wordmark" onClick={() => goTo("intro")}>
          PHOENIX<span>.</span>
          <small>FIRE INTELLIGENCE</small>
        </button>

        <nav className="top-links" aria-label="Navegación principal">
          <button onClick={() => goTo("intro")}>INICIO</button>
          <button onClick={() => goTo("research")}>EXPERIMENTOS</button>
          <button className="nav-cta" onClick={enterLab}>
            LABORATORIO ↗
          </button>
        </nav>
      </header>

      <aside className="chapter-indicator" aria-label="Capítulos">
        {sections.map(([id, number], index) => (
          <button
            key={id}
            className={active === index ? "selected" : ""}
            onClick={() => goTo(id)}
            aria-label={`Ir al capítulo ${number}`}
            title={`Capítulo ${number}`}
          />
        ))}
      </aside>

      <section id="intro" className="chapter hero-section">
        <div className="hero-copy animate-in">
          <p className="eyebrow">NASA SPACE APPS CHALLENGE / 2026</p>
          <h1>
            BEYOND
            <br />
            THE <em>FLAME.</em>
          </h1>
          <p className="description">
            La gravedad cambia las reglas del fuego.
            La ciencia nos permite comprenderlas.
          </p>
          <button
            className="text-button"
            onClick={() => goTo("archive")}
          >
            EXPLORAR LA EXPERIENCIA <ArrowUpRight size={17} />
          </button>
        </div>

        <div className="scene-footer">
          <span>01 / 05 — FLAME IN FREEFALL</span>
          <span>SCROLL TO EXPLORE</span>
          <button onClick={() => goTo("archive")} aria-label="Continuar">
            <ArrowDown size={20} />
          </button>
        </div>
      </section>

      <section id="archive" className="chapter archive-section">
        <div className="archive-index animate-in">
          <span>02 — SCIENTIFIC KNOWLEDGE</span>
          <span>NASA RESEARCH ARCHIVE</span>
        </div>

        <div className="archive-headline animate-in">
          <h2>
            DECADES
            <br />
            OF SCIENCE.
            <br />
            <em>ONE VISION.</em>
          </h2>
        </div>

        <div className="archive-card animate-in">
          <div className="archive-card-top">
            <span>MICROGRAVITY / 2026</span>
            <span>PHX — 002</span>
          </div>
          <div className="archive-art">
            <span className="archive-art-ring" />
            <span className="archive-art-core" />
            <span className="archive-art-ring second" />
          </div>
          <h3>MAKE SCIENCE VISIBLE.</h3>
          <p>
            Convertimos investigación experimental en información
            accesible para la exploración humana del espacio.
          </p>
        </div>

        <p className="archive-bottom">
          DEL EXPERIMENTO AL CONOCIMIENTO
        </p>
      </section>

      <section id="research" className="chapter research-section">
        <div className="research-copy animate-in">
          <span className="eyebrow">03 — EXPERIMENT EXPLORER</span>
          <h2>
            EXPLORE
            <br />
            THE
            <br />
            <em>UNKNOWN.</em>
          </h2>

          <p className="research-category">{current.category}</p>
          <p className="research-description">{current.description}</p>

          <div className="experiment-selector">
            {experiments.map((item, index) => (
              <button
                key={item.id}
                className={selected === index ? "active" : ""}
                onClick={() => setSelected(index)}
              >
                <span>0{index + 1}</span>
                {item.id}
              </button>
            ))}
          </div>

          <button
            className="text-button"
            onClick={enterLab}
          >
            EXAMINAR INVESTIGACIÓN <ArrowUpRight size={17} />
          </button>
        </div>

        <div className="research-number">
          {current.id} / SELECTED RESEARCH
        </div>
      </section>

      <section id="corridor" className="chapter corridor-section">
        <div className="corridor-content animate-in">
          <p className="eyebrow">04 — INTO THE UNKNOWN</p>
          <h2>
            EVERY DATA
            <br />
            POINT
            <br />
            <em>MATTERS.</em>
          </h2>
          <p>
            Analizamos la evidencia para comprender
            cómo evoluciona el fuego más allá de la Tierra.
          </p>
        </div>
        <span className="corridor-caption">
          CINEMATIC CAMERA / DEEP SPACE RESEARCH
        </span>
      </section>

      <section id="finale" className="chapter finale-section">
        <div className="finale-glow" />

        <div className="finale-content animate-in">
          <p className="eyebrow">05 — PHOENIX FIRE INTELLIGENCE</p>
          <h2>
            TURN DATA
            <br />
            INTO
            <br />
            <em>IMPACT.</em>
          </h2>

          <p>
            Una nueva forma de explorar, comparar
            e interpretar la investigación de la NASA.
          </p>

          <button
            className="launch-button"
            onClick={enterLab}
          >
            ENTRAR AL LABORATORIO
            <ArrowUpRight size={20} />
          </button>
        </div>

        <div className="finale-footer">
          <span>PHOENIX ORBIT</span>
          <span>BUILT FOR HUMAN SPACE EXPLORATION</span>
          <span>2026</span>
        </div>
      </section>

      {labOpen && (
        <div className="laboratory-overlay" role="dialog" aria-modal="true"
             aria-label="Laboratorio científico PHOENIX">
            {doorsPlaying && (
              <LabEntrance
                onComplete={() => setDoorsPlaying(false)}
              />
            )}
          <div className="lab-header">
            <div className="lab-brand">
              <Flame size={21} color="#ff9258" />
              <strong>PHOENIX LAB</strong>
              <span>SCIENTIFIC EXPLORER / V0.1</span>
            </div>

            <button
              className="close-lab"
              onClick={closeLab}
              aria-label="Cerrar laboratorio"
            >
              <X size={23} />
            </button>
          </div>

          <main className="lab-content">
            <p className="eyebrow">RESEARCH INTELLIGENCE PLATFORM</p>
            <h2>EXPLORE THE EVIDENCE.</h2>
            <p className="lab-intro">
              Consulta y compara programas de investigación sobre
              combustión en microgravedad.
            </p>

            <div className="lab-notice">
              MODO DEMOSTRACIÓN — Estas fichas son descripciones de
              programas. Aún no incluyen mediciones experimentales
              completas ni inteligencia artificial integrada.
            </div>

            <div className="lab-grid">
              <div className="lab-panel">
                <div className="lab-panel-head">
                  <h3>INVESTIGACIONES</h3>
                  <span>NASA / ARCHIVE</span>
                </div>

                <input
                  className="lab-search"
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  placeholder="Buscar programa o tema..."
                  aria-label="Buscar investigaciones"
                />

                <div className="lab-results">
                  {results.map((item) => (
                    <article key={item.id} className="lab-item">
                      <div>
                        <strong>{item.id}</strong>
                        <small>{item.name}</small>
                        <p>{item.description}</p>
                      </div>
                      <a
                        href={item.source}
                        target="_blank"
                        rel="noopener noreferrer"
                      >
                        NASA ↗
                      </a>
                    </article>
                  ))}

                  {results.length === 0 && (
                    <p>No hay coincidencias en las fichas disponibles.</p>
                  )}
                </div>
              </div>

              <div className="lab-panel">
                <div className="lab-panel-head">
                  <h3>COMPARACIÓN</h3>
                  <span>ANALYSIS / DEMO</span>
                </div>

                <div className="lab-select-row">
                  <label>
                    INVESTIGACIÓN A
                    <select
                      value={compareA}
                      onChange={(e) => setCompareA(e.target.value)}
                    >
                      {experiments.map((item) => (
                        <option key={item.id}>{item.id}</option>
                      ))}
                    </select>
                  </label>

                  <label>
                    INVESTIGACIÓN B
                    <select
                      value={compareB}
                      onChange={(e) => setCompareB(e.target.value)}
                    >
                      {experiments.map((item) => (
                        <option key={item.id}>{item.id}</option>
                      ))}
                    </select>
                  </label>
                </div>

                <div className="lab-compare">
                  {experiments
                    .filter((item) =>
                      [compareA, compareB].includes(item.id)
                    )
                    .map((item) => (
                      <div key={item.id}>
                        <strong>{item.id}</strong>
                        <span>{item.category}</span>
                        <p>{item.description}</p>
                      </div>
                    ))}
                </div>

                <button
                  className="lab-export"
                  onClick={exportComparison}
                >
                  EXPORTAR COMPARACIÓN JSON ↗
                </button>
              </div>
            </div>
           <DataDashboard />
           <ExperimentCharts />
           <AIChat experimentIds={[compareA, compareB]} />
          </main>
        </div>
      )}
    </div>
  );
}
