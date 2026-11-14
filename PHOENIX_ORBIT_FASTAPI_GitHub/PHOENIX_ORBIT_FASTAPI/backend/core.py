import os, json, re, hashlib
from pathlib import Path
import fitz, numpy as np
from google import genai

BASE = Path(__file__).resolve().parent.parent
DATA = BASE/"data"
INDEX = DATA/"phoenix_index.json"
EMBED_MODEL = "gemini-embedding-001"
CHAT_MODEL = os.getenv("GEMINI_CHAT_MODEL","gemini-2.5-flash")

def client():
    key=os.getenv("GEMINI_API_KEY")
    if not key: raise RuntimeError("Falta configurar GEMINI_API_KEY.")
    return genai.Client(api_key=key)

def chunks(text, size=1100, overlap=180):
    text=re.sub(r"\\s+"," ",text).strip()
    out=[]; start=0
    while start<len(text):
        end=min(start+size,len(text))
        if end<len(text):
            cut=text.rfind(" ",start,end)
            if cut>start+size//2: end=cut
        out.append(text[start:end])
        if end>=len(text): break
        start=max(end-overlap,start+1)
    return out

def load():
    return json.loads(INDEX.read_text(encoding="utf-8")) if INDEX.exists() else []
def save(items):
    DATA.mkdir(parents=True,exist_ok=True)
    INDEX.write_text(json.dumps(items,ensure_ascii=False),encoding="utf-8")
def embed(texts):
    result=client().models.embed_content(model=EMBED_MODEL,contents=texts)
    return [x.values for x in result.embeddings]

def index_pdf_bytes(filename, raw):
    digest=hashlib.sha256(raw).hexdigest()
    old=load()
    if any(x.get("sha256")==digest for x in old): return 0,"Documento ya indexado."
    records=[]
    with fitz.open(stream=raw,filetype="pdf") as pdf:
        for page_no,page in enumerate(pdf,1):
            for part in chunks(page.get_text("text")):
                if part.strip(): records.append({"text":part,"source":Path(filename).name,"page":page_no,"sha256":digest})
    if not records: return 0,"No se extrajo texto; puede ser un PDF escaneado y necesitar OCR."
    vectors=[]
    for i in range(0,len(records),40): vectors.extend(embed([x["text"] for x in records[i:i+40]]))
    for item,vector in zip(records,vectors): item["embedding"]=vector
    old.extend(records); save(old)
    return len(records),f"Indexados {len(records)} fragmentos."

def list_documents():
    grouped={}
    for item in load(): grouped[item["source"]]=grouped.get(item["source"],0)+1
    return [{"name":k,"chunks":v} for k,v in sorted(grouped.items())]

def answer_question(question, top_k=5):
    items=load()
    if not items: return {"answer":"La biblioteca aún no tiene PDF indexados. Carga documentos primero.","sources":[]}
    q=np.asarray(embed([question])[0],dtype=np.float32)
    mat=np.asarray([x["embedding"] for x in items],dtype=np.float32)
    scores=(mat@q)/(np.linalg.norm(mat,axis=1)*np.linalg.norm(q)+1e-10)
    idx=np.argsort(scores)[::-1][:top_k]
    found=[{**items[int(i)],"score":float(scores[int(i)])} for i in idx]
    context="\\n\\n".join(f"[FUENTE {i+1}] {x['source']} | página {x['page']}\\n{x['text']}" for i,x in enumerate(found))
    prompt=f"""Eres PHOENIX AI, asistente científico de PHOENIX Orbit. Responde en español.
Usa el contexto para afirmaciones sobre los documentos. No inventes mediciones ni conclusiones.
Si falta evidencia, dilo. Distingue experimentos de microgravedad de accidentes históricos.
Cita como [Fuente N, p. X].
PREGUNTA: {question}
CONTEXTO:
{context}"""
    response=client().models.generate_content(model=CHAT_MODEL,contents=prompt)
    return {"answer":response.text or "No se obtuvo respuesta.","sources":[{"source":x["source"],"page":x["page"],"relevance":round(x["score"],3)} for x in found]}
