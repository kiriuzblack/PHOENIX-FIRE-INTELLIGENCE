
import { useState } from "react";
import type { FormEvent } from "react";
import { Bot, Send, User } from "lucide-react";
import "./AIChat.css";

type Source = {
  title: string;
  url: string;
  experiment_id?: string | null;
};

type ChatResponse = {
  answer: string;
  sources: Source[];
  grounded: boolean;
  mode?: string;
};

type Message = {
  role: "user" | "assistant";
  text: string;
  sources?: Source[];
  grounded?: boolean;
  mode?: string;
};

type AIChatProps = {
  experimentIds: string[];
};

export default function AIChat({
  experimentIds,
}: AIChatProps) {
  const [question, setQuestion] = useState("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function sendMessage(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    const text = question.trim();

    if (!text || loading) return;

    setMessages((previous) => [
      ...previous,
      { role: "user", text },
    ]);

    setQuestion("");
    setError("");
    setLoading(true);

    try {
      const response = await fetch(
        "http://127.0.0.1:8000/api/ai/chat",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            question: text,
            experiment_ids: [...new Set(experimentIds)],
          }),
        }
      );

      if (!response.ok) {
        throw new Error(
          `El servidor respondió con código ${response.status}`
        );
      }

      const data: ChatResponse = await response.json();

      if (!data.answer) {
        throw new Error("La API no devolvió una respuesta.");
      }

      setMessages((previous) => [
        ...previous,
        {
          role: "assistant",
          text: data.answer,
          sources: data.sources ?? [],
          grounded: data.grounded ?? false,
          mode: data.mode,
        },
      ]);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "No se pudo conectar con PHOENIX AI."
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="phoenix-ai">
      <div className="phoenix-ai-heading">
        <div>
          <span className="phoenix-ai-eyebrow">
            ARTIFICIAL INTELLIGENCE / RESEARCH
          </span>

          <h3>ASK PHOENIX AI.</h3>

          <p>
            Explora la investigación sobre combustión
            en microgravedad mediante preguntas.
          </p>
        </div>

        <div className="phoenix-ai-symbol">
          <Bot size={30} />
        </div>
      </div>

      <div className="phoenix-ai-context">
        Investigaciones seleccionadas:{" "}
        {experimentIds.join(" / ")}
      </div>

      <div className="phoenix-ai-messages" aria-live="polite">
        {messages.length === 0 && (
          <div className="phoenix-ai-welcome">
            <Bot size={25} />

            <strong>PHOENIX AI SYSTEM</strong>

            <p>
              Pregúntame sobre BASS, FLEX, SAFFIRE
              o la combustión en microgravedad.
            </p>
          </div>
        )}

        {messages.map((message, index) => (
          <div
            key={index}
            className={`phoenix-ai-message ${message.role}`}
          >
            <div className="phoenix-ai-avatar">
              {message.role === "user" ? (
                <User size={16} />
              ) : (
                <Bot size={16} />
              )}
            </div>

            <div className="phoenix-ai-bubble">
              <p>{message.text}</p>

              {message.role === "assistant" && (
                <small>
                  {message.grounded
                    ? "Respuesta con fuentes recuperadas"
                    : "Respuesta sin fuentes verificadas"}
                </small>
              )}

              {message.sources &&
                message.sources.length > 0 && (
                  <div className="phoenix-ai-sources">
                    <strong>FUENTES</strong>

                    {message.sources.map((source, i) =>
                      /^https?:\/\//.test(source.url) ? (
                        <a
                          key={i}
                          href={source.url}
                          target="_blank"
                          rel="noopener noreferrer"
                        >
                          {source.title}
                        </a>
                      ) : (
                        <span key={i}>{source.title}</span>
                      )
                    )}
                  </div>
                )}
            </div>
          </div>
        ))}

        {loading && (
          <p className="phoenix-ai-loading">
            PHOENIX está procesando tu pregunta...
          </p>
        )}
      </div>

      {error && (
        <p className="phoenix-ai-error" role="alert">
          {error}
        </p>
      )}

      <form
        className="phoenix-ai-form"
        onSubmit={sendMessage}
      >
        <textarea
          value={question}
          onChange={(event) =>
            setQuestion(event.target.value)
          }
          placeholder="Pregunta sobre la investigación de la NASA..."
          rows={2}
          maxLength={2000}
          aria-label="Pregunta para PHOENIX AI"
        />

        <button
          type="submit"
          disabled={loading || !question.trim()}
          aria-label="Enviar pregunta"
        >
          <Send size={19} />
        </button>
      </form>

      <p className="phoenix-ai-disclaimer">
        El asistente está en integración. Verifica
        la evidencia científica antes de utilizar
        sus respuestas para conclusiones de seguridad.
      </p>
    </section>
  );
}
