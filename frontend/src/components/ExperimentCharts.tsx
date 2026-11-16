

import {
  useEffect,
  useLayoutEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import gsap from "gsap";

import "./ExperimentCharts.css";

const API =
  import.meta.env.VITE_API_URL ||
  "http://127.0.0.1:8000";

type RecordRow = {
  test_id: string;
  experiment: string;
  material: string;
  oxygen_percent: string;
  pressure_kpa: string;
  burn_time_s: string;
  original_result: string;
  source_file: string;
};

type QualityFlag = {
  test_id: string;
  review_status: string;
};

type Axis = "oxygen_percent" | "pressure_kpa";

type Point = {
  x: number;
  y: number;
  row: RecordRow;
};

function numeric(value: string): number | null {
  if (!value || !value.trim()) return null;

  const result = Number(value);

  return Number.isFinite(result) ? result : null;
}

function pointColor(result: string) {
  const text = result.toLowerCase();

  if (text.includes("extinc")) return "#68c9ff";
  if (text.includes("disrupt")) return "#ff975f";

  return "#acb5cc";
}

export default function ExperimentCharts() {
  
  const chartRef = useRef<SVGSVGElement>(null);

  const previousPositions = useRef(
  new Map<string, { cx: number; cy: number }>()
    );
  const [records, setRecords] = useState<RecordRow[]>([]);
  const [flags, setFlags] = useState<QualityFlag[]>([]);
  const [program, setProgram] = useState("ALL");
  const [material, setMaterial] = useState("ALL");
  const [axis, setAxis] = useState<Axis>("oxygen_percent");
  const [includeFlagged, setIncludeFlagged] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const controller = new AbortController();

    async function load() {
      try {
        const [recordsResponse, flagsResponse] =
          await Promise.all([
            fetch(`${API}/api/data/experiments?limit=500`, {
              signal: controller.signal,
            }),
            fetch(`${API}/api/data/quality-flags`, {
              signal: controller.signal,
            }),
          ]);

        if (!recordsResponse.ok || !flagsResponse.ok) {
          throw new Error("No se pudieron consultar los datos.");
        }

        const recordsData = await recordsResponse.json();
        const flagsData = await flagsResponse.json();

        if (controller.signal.aborted) return;

        setRecords(recordsData.items ?? []);
        setFlags(flagsData.items ?? []);
      } catch (err) {
        if (!controller.signal.aborted) {
          setError(
            err instanceof Error ? err.message : "Error de conexión"
          );
        }
      } finally {
        if (!controller.signal.aborted) setLoading(false);
      }
    }

    void load();

    return () => controller.abort();
  }, []);

  const programs = useMemo(
    () =>
      [...new Set(records.map((r) => r.experiment))]
        .filter(Boolean)
        .sort(),
    [records]
  );

  const materials = useMemo(
    () =>
      [...new Set(
        records
          .filter(
            (r) => program === "ALL" || r.experiment === program
          )
          .map((r) => r.material)
      )]
        .filter(Boolean)
        .sort(),
    [records, program]
  );

  const flaggedIds = useMemo(
    () => new Set(flags.map((flag) => flag.test_id)),
    [flags]
  );

  const filtered = useMemo(
    () =>
      records.filter(
        (r) =>
          (program === "ALL" || r.experiment === program) &&
          (material === "ALL" || r.material === material)
      ),
    [records, program, material]
  );

  const excludedFlags = filtered.filter(
    (r) => flaggedIds.has(r.test_id)
  ).length;

  const eligible = filtered.filter(
    (r) => includeFlagged || !flaggedIds.has(r.test_id)
  );

  const points: Point[] = eligible.flatMap((row) => {
    const x = numeric(row[axis]);
    const y = numeric(row.burn_time_s);

    if (
      x === null ||
      y === null ||
      x < 0 ||
      y <= 0 ||
      (axis === "pressure_kpa" && x <= 0) ||
      (axis === "oxygen_percent" && x > 100)
    ) {
      return [];
    }

    return [{ x, y, row }];
  });

  const unavailable = eligible.length - points.length;

  const maxX = Math.max(1, ...points.map((p) => p.x));
  const maxY = Math.max(1, ...points.map((p) => p.y));

  const left = 70;
  const bottom = 322;
  const plotWidth = 855;
  const plotHeight = 280;

  const xPosition = (x: number) =>
    left + (x / maxX) * plotWidth;

  const yPosition = (y: number) =>
    bottom - (y / maxY) * plotHeight;

  const axisLabel =
    axis === "oxygen_percent"
      ? "Concentración de oxígeno (%)"
      : "Presión ambiental (kPa)";


useLayoutEffect(() => {
  const svg = chartRef.current;

  if (!svg) return;

  const circles = svg.querySelectorAll<SVGCircleElement>(
    "circle[data-point-id]"
  );

  const nextPositions = new Map<
    string,
    { cx: number; cy: number }
  >();

  const animations: gsap.core.Tween[] = [];

  const reduceMotion = window.matchMedia(
    "(prefers-reduced-motion: reduce)"
  ).matches;

  circles.forEach((circle, index) => {
    const id = circle.dataset.pointId;

    if (!id) return;

    const cx = Number(circle.getAttribute("cx"));
    const cy = Number(circle.getAttribute("cy"));

    const previous = previousPositions.current.get(id);

    nextPositions.set(id, { cx, cy });

    gsap.killTweensOf(circle);

    if (reduceMotion) {
      gsap.set(circle, { opacity: 1 });
      return;
    }

    const animation = gsap.fromTo(
      circle,
      {
        attr: {
          cx: previous?.cx ?? cx,
          cy: previous?.cy ?? bottom,
        },
        opacity: previous ? 1 : 0,
      },
      {
        attr: { cx, cy },
        opacity: 1,
        duration: 0.9,
        delay: previous
          ? 0
          : Math.min(index * 0.003, 0.35),
        ease: "power3.out",
        overwrite: true,
      }
    );

    animations.push(animation);
  })  ;

  previousPositions.current = nextPositions;

    return () => {
        animations.forEach((animation) => animation.kill());
    };
    }, [
    axis,
    program,
    material,
    includeFlagged,
    records,
    flags,
    loading,
    ]);

  return (
    <section className="ec-panel">
      <header className="ec-header">
        <div>
          <span className="ec-eyebrow">
            EXPERIMENTAL DATA / INTERACTIVE ANALYSIS
          </span>
          <h3>COMBUSTION INSIGHTS.</h3>
          <p>
            Explora relaciones entre condiciones experimentales
            y duración de combustión.
          </p>
        </div>
        <span className="ec-version">PHOENIX / RESEARCH</span>
      </header>

      <div className="ec-controls">
        <label>
          PROGRAMA
          <select
            value={program}
            onChange={(event) => {
              setProgram(event.target.value);
              setMaterial("ALL");
            }}
          >
            <option value="ALL">TODOS</option>
            {programs.map((name) => (
              <option key={name} value={name}>
                {name}
              </option>
            ))}
          </select>
        </label>

        <label>
          MATERIAL
          <select
            value={material}
            onChange={(event) => setMaterial(event.target.value)}
          >
            <option value="ALL">TODOS</option>
            {materials.map((name) => (
              <option key={name} value={name}>
                {name}
              </option>
            ))}
          </select>
        </label>

        <label>
          EJE HORIZONTAL
          <select
            value={axis}
            onChange={(event) =>
              setAxis(event.target.value as Axis)
            }
          >
            <option value="oxygen_percent">OXÍGENO (%)</option>
            <option value="pressure_kpa">PRESIÓN (kPa)</option>
          </select>
        </label>

        <label className="ec-check">
          <input
            type="checkbox"
            checked={includeFlagged}
            onChange={(event) =>
              setIncludeFlagged(event.target.checked)
            }
          />
          Incluir registros con alertas de calidad
        </label>
      </div>

      {loading && <p>Cargando registros...</p>}
      {error && <p className="ec-error">{error}</p>}

      {!loading && !error && (
        <>
          <div className="ec-chart-header">
            <div>
              <h4>{axisLabel} vs. duración de combustión</h4>
              <p>
                {points.length} ensayos representados de{" "}
                {filtered.length} registros filtrados.
              </p>
            </div>

            <div className="ec-legend">
              <span>
                <i className="ec-dot extinction" />
                Extinction
              </span>
              <span>
                <i className="ec-dot disruption" />
                Disruption
              </span>
              <span>
                <i className="ec-dot other" />
                Otro resultado
              </span>
            </div>
          </div>

          {points.length > 0 ? (
            <div className="ec-chart">
              <svg
                ref={chartRef}
                viewBox="0 0 960 370"
                role="img"
                aria-label={`Gráfico de dispersión: ${axisLabel} frente a duración de combustión, con ${points.length} puntos`}
              >
                {[0, 0.25, 0.5, 0.75, 1].map((t) => {
                  const y = bottom - t * plotHeight;
                  const x = left + t * plotWidth;

                  return (
                    <g key={t}>
                      <line
                        x1={left}
                        x2={left + plotWidth}
                        y1={y}
                        y2={y}
                        stroke="#31445e"
                        strokeWidth="1"
                      />
                      <line
                        x1={x}
                        x2={x}
                        y1={bottom - plotHeight}
                        y2={bottom}
                        stroke="#243850"
                        strokeWidth="1"
                      />
                      <text
                        x={left - 12}
                        y={y + 4}
                        textAnchor="end"
                        fill="#9eb8d1"
                        fontSize="11"
                      >
                        {(t * maxY).toFixed(1)}
                      </text>
                      <text
                        x={x}
                        y={bottom + 23}
                        textAnchor="middle"
                        fill="#9eb8d1"
                        fontSize="11"
                      >
                        {(t * maxX).toFixed(
                          axis === "oxygen_percent" ? 1 : 0
                        )}
                      </text>
                    </g>
                  );
                })}

                {points.map((point, index) => (
                  <circle
                    key={`${point.row.test_id}-${index}`}
                    data-point-id={point.row.test_id}
                    cx={xPosition(point.x)}
                    cy={yPosition(point.y)}
                    r="5"
                    fill={pointColor(point.row.original_result)}
                    fillOpacity="0.78"
                    stroke="#07111e"
                    strokeWidth="1"
                    tabIndex={0}
                  >
                    <title>
                      {[
                        `Ensayo: ${point.row.test_id}`,
                        `Programa: ${point.row.experiment}`,
                        `Material: ${point.row.material || "No informado"}`,
                        `${axisLabel}: ${point.x}`,
                        `Duración: ${point.y} s`,
                        `Resultado: ${point.row.original_result || "No informado"}`,
                        `Fuente: ${point.row.source_file || "No informada"}`,
                      ].join("\n")}
                    </title>
                  </circle>
                ))}
              </svg>
            </div>
          ) : (
            <div className="ec-empty">
              No hay pares de mediciones válidos para los filtros
              seleccionados.
            </div>
          )}

          <div className="ec-axis-label">{axisLabel}</div>
          <p className="ec-y-label">
            Eje vertical: tiempo de combustión (s).
            Sitúa el cursor sobre un punto para ver su registro.
          </p>

          <div className="ec-quality">
            <span>
              <strong>{excludedFlags}</strong> registros con
              alertas de calidad
              {includeFlagged ? " incluidos" : " excluidos"}
            </span>
            <span>
              <strong>{unavailable}</strong> registros sin
              un par numérico utilizable
            </span>
          </div>

          <p className="ec-disclaimer">
            Visualización exploratoria de datos procesados por
            PHOENIX Data Analytics. La correlación visual no
            demuestra causalidad ni implica una clasificación
            de riesgo. Comparar ensayos requiere controlar
            material, geometría, atmósfera y otras condiciones.
            Las alertas de calidad no equivalen a incendios.
          </p>
        </>
      )}
    </section>
  );
}
