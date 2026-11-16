
import { useEffect, useState } from "react";
import {
  Activity,
  AlertTriangle,
  BarChart3,
  Database,
  FileSearch,
} from "lucide-react";
import "./DataDashboard.css";

const API = "http://127.0.0.1:8000";

type Summary = {
  total_experiment_records: number;
  evidence_records: number;
  quality_flags: number;
  saffire_records: number;
  by_experiment: Record<string, number>;
  validation_notice: string;
};

type Experiment = {
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
  experiment: string;
  flagged_variable: string;
  original_value: string;
  description: string;
  review_priority: string;
  review_status: string;
};

function display(value?: string) {
  return value?.trim() ? value : "—";
}

export default function DataDashboard() {
  const [summary, setSummary] = useState<Summary | null>(
    null
  );
  const [records, setRecords] = useState<Experiment[]>([]);
  const [flags, setFlags] = useState<QualityFlag[]>([]);
  const [filter, setFilter] = useState("ALL");
  const [showAllFlags, setShowAllFlags] = useState(false);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const controller = new AbortController();

    async function loadData() {
      setLoading(true);
      setError("");

      try {
        const params = new URLSearchParams({
          limit: "20",
        });

        if (filter !== "ALL") {
          params.set("experiment", filter);
        }

        const [summaryResponse, recordsResponse, flagsResponse] =
          await Promise.all([
            fetch(`${API}/api/data/summary`, {
              signal: controller.signal,
            }),
            fetch(
              `${API}/api/data/experiments?${params}`,
              { signal: controller.signal }
            ),
            fetch(`${API}/api/data/quality-flags`, {
              signal: controller.signal,
            }),
          ]);

        if (
          !summaryResponse.ok ||
          !recordsResponse.ok ||
          !flagsResponse.ok
        ) {
          throw new Error(
            "Una de las rutas de datos no respondió correctamente."
          );
        }

        const summaryData: Summary =
          await summaryResponse.json();

        const recordsData: {
          total: number;
          items: Experiment[];
        } = await recordsResponse.json();

        const flagsData: {
          items: QualityFlag[];
        } = await flagsResponse.json();

        if (controller.signal.aborted) return;

        setSummary(summaryData);
        setRecords(recordsData.items);
        setTotal(recordsData.total);
        setFlags(flagsData.items);
      } catch (err) {
        if (controller.signal.aborted) return;

        setError(
          err instanceof Error
            ? err.message
            : "No se pudieron cargar los datos."
        );
      } finally {
        if (!controller.signal.aborted) {
          setLoading(false);
        }
      }
    }

    void loadData();

    return () => controller.abort();
  }, [filter]);

  const counts = Object.entries(
    summary?.by_experiment ?? {}
  ).sort((a, b) => b[1] - a[1]);

  const maxCount = Math.max(
    1,
    ...counts.map(([, count]) => count)
  );

  const metrics = [
    {
      label: "REGISTROS EXPERIMENTALES",
      value: summary?.total_experiment_records,
      Icon: Database,
    },
    {
      label: "FILAS DE EVIDENCIA",
      value: summary?.evidence_records,
      Icon: FileSearch,
    },
    {
      label: "ALERTAS DE CALIDAD",
      value: summary?.quality_flags,
      Icon: AlertTriangle,
    },
    {
      label: "REGISTROS SAFFIRE",
      value: summary?.saffire_records,
      Icon: Activity,
    },
  ];

  return (
    <section className="pd-section" aria-label="Datos científicos">
      <div className="pd-header">
        <div>
          <p className="pd-eyebrow">
            NASA RESEARCH / DATA ANALYTICS
          </p>
          <h3>SCIENTIFIC DATA.</h3>
          <p>
            Explora los registros experimentales y las
            observaciones de calidad procesadas por el equipo.
          </p>
        </div>

        <BarChart3 size={35} color="#ff965b" />
      </div>

      {error && (
        <div className="pd-error" role="alert">
          Error de conexión: {error}
          <p>
            Verifica que FastAPI siga funcionando en
            el puerto 8000.
          </p>
        </div>
      )}

      {loading && (
        <p className="pd-loading" role="status">
          Cargando datos científicos...
        </p>
      )}

      {summary && (
        <>
          <div className="pd-metrics">
            {metrics.map(({ label, value, Icon }) => (
              <article className="pd-metric" key={label}>
                <Icon size={20} color="#ff965b" />
                <strong>{value ?? "—"}</strong>
                <span>{label}</span>
              </article>
            ))}
          </div>

          <div className="pd-distribution">
            <div className="pd-section-title">
              <h4>DISTRIBUCIÓN POR PROGRAMA</h4>
              <span>REGISTROS / NO NIVEL DE RIESGO</span>
            </div>

            {counts.map(([name, count]) => (
              <div className="pd-bar-row" key={name}>
                <div className="pd-bar-label">
                  <strong>{name}</strong>
                  <span>{count} registros</span>
                </div>

                <div className="pd-bar-track">
                  <div
                    className="pd-bar-fill"
                    style={{
                      width: `${(count / maxCount) * 100}%`,
                    }}
                  />
                </div>
              </div>
            ))}

            <p className="pd-note">
              La cantidad de registros no indica la
              peligrosidad ni la importancia científica
              de un experimento.
            </p>
          </div>
        </>
      )}

      <div className="pd-explorer">
        <div className="pd-section-title">
          <div>
            <h4>EXPERIMENT DATA EXPLORER</h4>
            <p>Filtra y consulta los registros disponibles.</p>
          </div>

          <select
            aria-label="Filtrar programa experimental"
            value={filter}
            onChange={(event) =>
              setFilter(event.target.value)
            }
          >
            <option value="ALL">TODOS</option>

            {counts.map(([name]) => (
              <option key={name} value={name}>
                {name}
              </option>
            ))}
          </select>
        </div>

        <div className="pd-table-scroll">
          <table className="pd-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>PROGRAMA</th>
                <th>MATERIAL</th>
                <th>OXÍGENO (%)</th>
                <th>PRESIÓN (kPa)</th>
                <th>DURACIÓN (s)</th>
                <th>RESULTADO ORIGINAL</th>
                <th>ARCHIVO FUENTE</th>
              </tr>
            </thead>

            <tbody>
              {records.map((row) => (
                <tr key={row.test_id}>
                  <td className="pd-id">
                    {display(row.test_id)}
                  </td>
                  <td>{display(row.experiment)}</td>
                  <td>{display(row.material)}</td>
                  <td>{display(row.oxygen_percent)}</td>
                  <td>{display(row.pressure_kpa)}</td>
                  <td>{display(row.burn_time_s)}</td>
                  <td>{display(row.original_result)}</td>
                  <td title={row.source_file}>
                    {display(row.source_file)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {!loading && records.length === 0 && (
          <p className="pd-note">
            No hay registros para el filtro seleccionado.
          </p>
        )}

        <p className="pd-note">
          Mostrando {records.length} de {total} registros
          para el filtro actual. Los campos vacíos
          indican datos no disponibles.
        </p>
      </div>

      <div className="pd-quality">
        <div className="pd-section-title">
          <h4>DATA QUALITY / REVIEW FLAGS</h4>
          <span>{flags.length} OBSERVACIONES</span>
        </div>

        {flags
          .slice(0, showAllFlags ? undefined : 5)
          .map((flag, index) => (
            <article
              className="pd-flag"
              key={`${flag.test_id}-${flag.flagged_variable}-${index}`}
            >
              <div>
                <strong>
                  {display(flag.test_id)}
                </strong>
                <span>
                  {display(flag.flagged_variable)}
                </span>
                <p>{display(flag.description)}</p>
                <small>
                  Valor original: {display(flag.original_value)}
                </small>
              </div>

              <div className="pd-flag-status">
                <span>
                  {display(flag.review_priority)}
                </span>
                <small>
                  {display(flag.review_status)}
                </small>
              </div>
            </article>
          ))}

        {flags.length > 5 && (
          <button
            className="pd-more"
            onClick={() =>
              setShowAllFlags((previous) => !previous)
            }
          >
            {showAllFlags
              ? "MOSTRAR MENOS"
              : `VER LAS ${flags.length} OBSERVACIONES`}
          </button>
        )}
      </div>

      <p className="pd-disclaimer">
        {summary?.validation_notice ??
          "Los datos requieren validación científica."}
        {" "}Las alertas identifican cuestiones de calidad
        o revisión, no niveles de peligro confirmados.
      </p>
    </section>
  );
}
