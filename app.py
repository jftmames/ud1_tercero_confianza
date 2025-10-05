# -*- coding: utf-8 -*-
import io
import json
import hashlib
from datetime import datetime, timezone
from dateutil import tz
from typing import List, Dict, Any

import pandas as pd
import streamlit as st


# ========= Configuración general =========
st.set_page_config(
    page_title="UD1 — El tercero de confianza",
    page_icon="🧭",
    layout="wide"
)

if "ledger" not in st.session_state:
    # "Libro mayor" didáctico: lista de entradas (append-only a efectos de clase)
    st.session_state.ledger: List[Dict[str, Any]] = []

if "raci_rows" not in st.session_state:
    st.session_state.raci_rows = []  # se rellena al entrar a la pestaña RACI por primera vez


# ========= Utilidades =========
ROLES = [
    "Notaría",
    "Registro",
    "Auditoría",
    "Peritaje",
    "PSC (Prestador Confianza)",
    "TSA (Sellado de tiempo)",
    "Blockchain (nodos/red)",
    "Parte A",
    "Parte B"
]

TAREAS = [
    "Identidad de partes",
    "Capacidad y consentimiento",
    "Integridad del documento",
    "Datación (timestamp)",
    "Publicidad / Oponibilidad",
    "Conservación / Archivo",
    "Trazabilidad / Verificabilidad",
    "Responsabilidad ante terceros"
]

TEST_PREGUNTAS = [
    {
        "enunciado": "¿Qué garantiza siempre un hash criptográfico (p. ej., SHA-256)?",
        "opciones": ["Identidad", "Integridad", "Capacidad", "Consentimiento"],
        "correcta": "Integridad",
        "explicacion": "El hash prueba integridad y existencia previa si está sellado; no prueba identidad/capacidad/consentimiento."
    },
    {
        "enunciado": "¿Qué mecanismo aporta fe pública registral y prioridad en España?",
        "opciones": ["Blockchain pública", "Registro de la Propiedad/Mercantil", "PSC no cualificado", "Auditoría financiera"],
        "correcta": "Registro de la Propiedad/Mercantil",
        "explicacion": "La fe pública registral es una garantía propia del sistema registral, no de la cadena de bloques."
    },
    {
        "enunciado": "El sellado de tiempo cualificado (TSA) está previsto en…",
        "opciones": ["Reglamento eIDAS y Ley 6/2020", "Código Civil", "RGPD", "Ley del Mercado de Valores"],
        "correcta": "Reglamento eIDAS y Ley 6/2020",
        "explicacion": "eIDAS define servicios de confianza (firma, sello, marca de tiempo, etc.) y la Ley 6/2020 complementa en España."
    }
]


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha512_hex(data: bytes) -> str:
    return hashlib.sha512(data).hexdigest()


def now_iso_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def build_evidence_package(file_bytes: bytes, filename: str, notes: str = "") -> Dict[str, Any]:
    return {
        "schema": "edu.unie.ud1.evidence.v1",
        "filename": filename,
        "size_bytes": len(file_bytes),
        "sha256": sha256_hex(file_bytes),
        "sha512": sha512_hex(file_bytes),
        "computed_at_utc": now_iso_utc(),
        "notes": notes,
    }


def ledger_to_jsonl(entries: List[Dict[str, Any]]) -> str:
    return "".join(json.dumps(e, ensure_ascii=False) + "\n" for e in entries)


def parse_jsonl(content: bytes) -> List[Dict[str, Any]]:
    lines = content.decode("utf-8", errors="ignore").splitlines()
    out = []
    for ln in lines:
        ln = ln.strip()
        if not ln:
            continue
        try:
            out.append(json.loads(ln))
        except json.JSONDecodeError:
            pass
    return out


def init_raci_state():
    if st.session_state.raci_rows:
        return
    # Estado por defecto: sin asignaciones
    for tarea in TAREAS:
        st.session_state.raci_rows.append({
            "Tarea": tarea,
            "R (Responsable)": "",
            "A (Aprobador)": "",
            "C (Consultado)": [],
            "I (Informado)": []
        })


# ========= Encabezado =========
st.title("UD1 — El tercero de confianza")
st.caption("Sesión 2 · De la confianza jurídica al hash · App didáctica")

tabs = st.tabs([
    "📚 Teoría guiada",
    "🧩 Taller comparado",
    "🧪 Trust-Mapper (hash + timeline)",
    "🗂️ Matriz RACI",
    "✅ Autoevaluación",
    "📦 Descargas & Glosario"
])

# ========= Pestaña 1: Teoría guiada =========
with tabs[0]:
    col1, col2 = st.columns([1.1, 1])
    with col1:
        st.subheader("Objetivo de la unidad")
        st.write(
            "- Entender cómo el Derecho delega confianza en terceros (notaría, registro, auditoría, peritaje)\n"
            "- Mapear esas funciones a mecanismos digitales: **PSC, TSA y blockchain**\n"
            "- Distinguir qué cubre cada capa: identidad/capacidad/consentimiento (jurídico) vs integridad/tiempo (cripto)"
        )

        st.subheader("Conceptos clave")
        with st.expander("Notaría, Registro, Auditoría, Peritaje"):
            st.markdown("""
- **Notaría**: da fe de identidad, capacidad, consentimiento y legalidad formal; protocoliza.
- **Registro**: cualifica e inscribe actos con efectos de publicidad y prioridad.
- **Auditoría**: revisa y opina sobre la **imagen fiel** (cuentas, cumplimiento).
- **Peritaje**: aporta criterio técnico y objetivo sobre hechos controvertidos.
            """)

        with st.expander("Servicios electrónicos de confianza (eIDAS / Ley 6/2020)"):
            st.markdown("""
- **PSC**: Prestadores de Servicios de Confianza (cualificados y no cualificados).
- **Firma / Sello / Sellado de tiempo (TSA)**: servicios regulados con valor jurídico.
- **Archivo electrónico** y **entrega certificada**: integridad, evidencias y trazabilidad.
            """)

    with col2:
        st.subheader("Comparativa rápida")
        df = pd.DataFrame({
            "Función de confianza": [
                "Identidad de partes",
                "Capacidad y consentimiento",
                "Integridad del documento",
                "Datación (timestamp)",
                "Publicidad / Oponibilidad",
                "Trazabilidad / Verificabilidad",
                "Responsabilidad regulada"
            ],
            "Mundo jurídico (personas/instituciones)": [
                "Notaría / certificados de identidad",
                "Notaría / control de legalidad",
                "Protocolo / copias autorizadas",
                "Protocolización / diligencias / TSA cualificada",
                "Registro (fe pública registral)",
                "Índices, asientos, libros y expedientes",
                "Estatuto público / supervisión / régimen sancionador"
            ],
            "Mundo técnico (PSC/TSA/Blockchain)": [
                "Certificados (PKI) ↔ identidad digital",
                "Fuera del alcance nativo; requiere capa legal/UX",
                "Hash (p. ej., SHA-256), control de integridad",
                "Marca de tiempo (TSA), anclaje en cadena",
                "Publicidad técnica del ledger (no fe pública civil)",
                "Bloques, Merkle, logs inmutables",
                "Régimen de PSC y políticas de la red"
            ]
        })
        st.dataframe(df, use_container_width=True)
    st.info("Idea clave: **diseños híbridos**. La cadena prueba integridad/tiempo; la fe pública y la capacidad siguen siendo jurídicas.")


# ========= Pestaña 2: Taller comparado =========
with tabs[1]:
    st.subheader("Caso: Contrato privado de licencia de software + anexo técnico")
    st.write("Trabaja en equipos: **A (jurídico)** y **B (técnico)**. Al final fusionáis ambos flujos.")

    colA, colB = st.columns(2)

    with colA:
        st.markdown("### Equipo A · Flujo del fedatario/registro")
        st.markdown("""
1. Verificación de identidad y representación  
2. Capacidad y consentimiento informado  
3. Redacción, lectura y **fe pública**  
4. Protocolo y copias autorizadas  
5. **Inscripción** (si procede) y publicidad
        """)
        st.caption("Entregable: diagrama + qué garantiza cada paso y bajo qué norma.")

    with colB:
        st.markdown("### Equipo B · Flujo técnico (hash/TSA/anclaje)")
        st.markdown("""
1. Cálculo **SHA-256** del contrato y anexos  
2. **Sellado de tiempo (TSA)** o registro en un **ledger** (prueba de existencia)  
3. Verificación independiente: recomputar hash y contrastar  
4. Registro de evidencias (JSONL) con metadatos mínimos
        """)
        st.caption("Entregable: ficha de verificación (hash, timestamp, evidencia).")

    st.divider()
    st.markdown("**Matriz de integración (para la puesta en común):**")
    integ = pd.DataFrame({
        "Paso": ["Identidad", "Capacidad/Consentimiento", "Integridad", "Datación", "Publicidad", "Conservación", "Responsabilidad"],
        "Capa jurídica": ["Notaría", "Notaría", "Protocolo", "Diligencia/TSA cualificada", "Registro", "Archivo/Expediente", "Régimen público"],
        "Capa técnica": ["PKI (certificados)", "—", "Hash (SHA-256)", "TSA / anclaje", "Ledger (difusión técnica)", "Logs / backups", "Políticas PSC / red"]
    })
    st.dataframe(integ, use_container_width=True)


# ========= Pestaña 3: Trust-Mapper =========
with tabs[2]:
    st.subheader("Trust-Mapper: hash + timeline jurídico/cripto")
    st.caption("Demostrador didáctico: genera una evidencia mínima (hash + metadatos) y un 'libro mayor' JSONL local.")

    up = st.file_uploader("Sube el documento (PDF, DOCX, TXT, etc.)", type=None)
    notes = st.text_input("Notas (opcional):", placeholder="p. ej., Contrato v1.3 firmado por las partes...")

    colh1, colh2 = st.columns([1, 1])
    if up is not None:
        file_bytes = up.read()
        sha256 = sha256_hex(file_bytes)
        sha512 = sha512_hex(file_bytes)

        with colh1:
            st.write("**Huella criptográfica**")
            st.code(f"SHA-256: {sha256}", language="text")
            st.code(f"SHA-512: {sha512}", language="text")

        with colh2:
            st.write("**Metadatos**")
            st.json({
                "filename": up.name,
                "size_bytes": len(file_bytes),
                "computed_at_utc": now_iso_utc()
            }, expanded=False)

        st.markdown("**Timeline de garantías**")
        t1, t2 = st.columns(2)
        with t1:
            st.markdown("##### Jurídico")
            st.checkbox("Identidad verificada (notaría / certificado de identidad)", value=False)
            st.checkbox("Capacidad/consentimiento y control de legalidad", value=False)
            st.checkbox("Publicidad/inscripción (si procede)", value=False)
        with t2:
            st.markdown("##### Criptográfico")
            c_hash = st.checkbox("Hash calculado (integridad)", value=True, disabled=True)
            c_time = st.checkbox("Marca de tiempo (TSA) aplicada", value=False)
            c_chain = st.checkbox("Anclaje en cadena (registro técnico)", value=False)

        st.markdown("**Generar paquete de evidencia**")
        if st.button("Crear evidencia (JSON)"):
            pkg = build_evidence_package(file_bytes, up.name, notes=notes)
            st.success("Evidencia generada")
            st.json(pkg, expanded=False)

            # descarga
            b = io.BytesIO(json.dumps(pkg, ensure_ascii=False, indent=2).encode("utf-8"))
            st.download_button("Descargar evidencia (.json)", b, file_name=f"evidence_{up.name}.json", mime="application/json")

            # añadir al "libro mayor" local
            st.session_state.ledger.append(pkg)

    st.divider()
    st.markdown("### Verificación")
    ver_file = st.file_uploader("1) Sube de nuevo el documento a verificar", type=None, key="verify_doc")
    ver_ledger = st.file_uploader("2) (Opcional) Sube un libro mayor JSONL previamente exportado", type=["jsonl"], key="verify_ledger")

    if st.button("Verificar"):
        if ver_file is None:
            st.warning("Sube el documento a verificar.")
        else:
            vbytes = ver_file.read()
            vhash = sha256_hex(vbytes)
            st.code(f"SHA-256 del documento: {vhash}", language="text")

            # Construir universo de evidencias: sesión + (opcional) JSONL subido
            evids = list(st.session_state.ledger)
            if ver_ledger is not None:
                evids += parse_jsonl(ver_ledger.read())

            # Coincidencias por sha256
            matches = [e for e in evids if e.get("sha256") == vhash]
            if matches:
                st.success(f"✅ Coincidencia encontrada: {len(matches)} evidencia(s).")
                st.json(matches[0], expanded=False)
            else:
                st.error("❌ No hay evidencia coincidente. (O bien no se registró, o el archivo cambió)")

    st.divider()
    st.markdown("### Libro mayor (didáctico)")
    colL, colR = st.columns([1, 1])
    with colL:
        if st.session_state.ledger:
            st.json(st.session_state.ledger[-1], expanded=False)
        st.caption("Última evidencia añadida.")

    with colR:
        if st.session_state.ledger:
            jsonl_str = ledger_to_jsonl(st.session_state.ledger)
            st.download_button(
                "Exportar libro mayor (.jsonl)",
                io.BytesIO(jsonl_str.encode("utf-8")),
                file_name="ledger_ud1.jsonl",
                mime="application/jsonl"
            )
        else:
            st.info("Aún no hay entradas en el libro mayor didáctico.")


# ========= Pestaña 4: Matriz RACI =========
with tabs[3]:
    st.subheader("Matriz RACI — Funciones delegadas en terceros")
    st.caption("Asigna R (Responsable), A (Aprobador), C (Consultado), I (Informado) por tarea.")

    init_raci_state()

    # Editor simple
    rows_out = []
    for row in st.session_state.raci_rows:
        st.markdown(f"**{row['Tarea']}**")
        c1, c2 = st.columns(2)
        with c1:
            r = st.selectbox("R (Responsable)", ROLES, index=ROLES.index(row["R (Responsable)"]) if row["R (Responsable)"] in ROLES else 0, key=f"r_{row['Tarea']}")
            a = st.selectbox("A (Aprobador)", ROLES, index=ROLES.index(row["A (Aprobador)"]) if row["A (Aprobador)"] in ROLES else 0, key=f"a_{row['Tarea']}")
        with c2:
            c = st.multiselect("C (Consultado)", ROLES, default=row["C (Consultado)"], key=f"c_{row['Tarea']}")
            i = st.multiselect("I (Informado)", ROLES, default=row["I (Informado)"], key=f"i_{row['Tarea']}")
        rows_out.append({
            "Tarea": row["Tarea"],
            "R (Responsable)": r,
            "A (Aprobador)": a,
            "C (Consultado)": "; ".join(c),
            "I (Informado)": "; ".join(i)
        })
        st.divider()

    df_raci = pd.DataFrame(rows_out)
    st.dataframe(df_raci, use_container_width=True)

    csv_bytes = df_raci.to_csv(index=False).encode("utf-8")
    st.download_button("Descargar RACI (.csv)", io.BytesIO(csv_bytes), file_name="raci_ud1.csv", mime="text/csv")


# ========= Pestaña 5: Autoevaluación =========
with tabs[4]:
    st.subheader("Autoevaluación rápida")
    aciertos = 0
    respuestas = []
    for idx, q in enumerate(TEST_PREGUNTAS, start=1):
        st.markdown(f"**{idx}. {q['enunciado']}**")
        sel = st.radio("Elige una opción:", q["opciones"], key=f"quiz_{idx}", index=0, horizontal=False)
        correcto = (sel == q["correcta"])
        respuestas.append((sel, correcto))

    if st.button("Corregir"):
        for i, (sel, ok) in enumerate(respuestas, start=1):
            if ok:
                st.success(f"{i}) Correcto ✅")
                aciertos += 1
            else:
                exp = TEST_PREGUNTAS[i-1]["explicacion"]
                st.error(f"{i}) Incorrecto ❌ · {exp}")
        st.info(f"Puntuación: **{aciertos}/{len(TEST_PREGUNTAS)}**")


# ========= Pestaña 6: Descargas & Glosario =========
with tabs[5]:
    st.subheader("Materiales de la sesión")
    st.markdown("""
- **Guion del taller** (este propio sitio en pestaña *Taller comparado*).
- **Evidencias**: exporta tu JSON y el **libro mayor** (.jsonl) desde *Trust-Mapper*.
- **Matriz RACI**: exporta el .csv desde su pestaña.
    """)

    st.subheader("Glosario breve")
    glos = pd.DataFrame({
        "Término": ["Fedatario", "Fe pública registral", "PSC", "TSA", "Hash (SHA-256)", "Marca de tiempo", "Anclaje en cadena"],
        "Definición (didáctica)": [
            "Quien da fe de hechos/actos con efectos jurídicos.",
            "Efectos de publicidad/prioridad que protege a quien confía en el registro.",
            "Prestador de servicios de confianza (firma, sello, TSA…).",
            "Autoridad de sellado de tiempo cualificada.",
            "Huella única de datos para verificar integridad.",
            "Prueba de datación electrónica del documento.",
            "Registro del hash en una transacción/bloque de una red blockchain."
        ]
    })
    st.dataframe(glos, use_container_width=True)

    st.caption("Aviso: la app es docente; no reemplaza servicios cualificados ni supone asesoramiento jurídico.")
