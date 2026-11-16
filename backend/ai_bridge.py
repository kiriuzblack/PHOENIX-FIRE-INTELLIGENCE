
import os
import httpx

GEMINI_URL = os.getenv(
    "PHOENIX_RAG_URL",
    "http://127.0.0.1:8002"
)


def consultar_ia(
    question: str,
    experiment_ids: list[str]
) -> dict:
    """
    Conecta PHOENIX LAB con Gemini + RAG.

    React -> FastAPI 8000 -> Gemini 8001
    """

    # Añadir contexto de los programas seleccionados.
    # La IA sigue limitada por los documentos indexados.
    consulta = question.strip()

    if experiment_ids:
        programas = ", ".join(experiment_ids)

        consulta = (
            f"Programas de interés: {programas}.\n"
            f"Pregunta del usuario: {question}\n"
            "Responde utilizando la evidencia científica "
            "disponible. Si no hay información suficiente, "
            "indícalo explícitamente."
        )

    try:
        response = httpx.post(
            f"{GEMINI_URL}/chat",
            json={
                "question": consulta,
                "top_k": 5
            },
            timeout=120.0
        )

        response.raise_for_status()
        data = response.json()

    except httpx.ConnectError as exc:
        raise RuntimeError(
            "No se pudo conectar con Gemini. "
            "Verifica el servidor del puerto 8001."
        ) from exc

    except httpx.TimeoutException as exc:
        raise RuntimeError(
            "Gemini tardó demasiado en responder."
        ) from exc

    except httpx.HTTPStatusError as exc:
        try:
            detail = exc.response.json().get(
                "detail",
                "Error desconocido"
            )
        except ValueError:
            detail = "Respuesta no válida del servidor"

        raise RuntimeError(
            f"Gemini devolvió HTTP "
            f"{exc.response.status_code}: {detail}"
        ) from exc

    except (httpx.RequestError, ValueError) as exc:
        raise RuntimeError(
            "No se pudo procesar la respuesta de Gemini."
        ) from exc

    # Adaptar las fuentes al formato del frontend.
    sources = []

    for item in data.get("sources", []):
        filename = item.get("source", "Documento")
        page = item.get("page")

        title = filename

        if page is not None:
            title += f" — página {page}"

        sources.append({
            "title": title,
            "url": "",
            "experiment_id": None
        })

    return {
        "answer": data.get(
            "answer",
            "No se obtuvo una respuesta."
        ),
        "sources": sources,
        "grounded": bool(sources)
    }
