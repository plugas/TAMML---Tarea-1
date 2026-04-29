# Pruebas del Sistema Q&A – Riopaila Castilla

## Descripción
Esta carpeta contiene las pruebas realizadas al sistema de preguntas y respuestas, con el objetivo de evaluar la calidad, coherencia y precisión del modelo.

---

## ⚙️ Metodología de prueba

Se ejecutaron más de 20 preguntas diseñadas para evaluar:

- Cobertura del conocimiento
- Capacidad de inferencia
- Detección de información ausente
- Consistencia de respuestas

---

## Archivos incluidos

- `langchain_groq_20q.py` → script de pruebas automatizadas
- `respuesta_20q.txt` → resultados generados por el modelo
- `tu_archivo_riopaila.txt` → contexto utilizado

---

## Resultados generales

- Alta precisión cuando la información está en el contexto
- Respuestas coherentes y formales
- Capacidad de negar información inexistente
- Buen desempeño en preguntas de sostenibilidad y productos

---

## Limitaciones observadas

- Dependencia total del contexto cargado
- No existe recuperación dinámica de información (NO-RAG)
- Sensibilidad a longitud del prompt

---

## Resultado

El sistema demostró estabilidad funcional en pruebas extensivas sin degradación significativa del rendimiento.
