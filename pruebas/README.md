# Pruebas del Sistema Q&A – Riopaila Castilla

## 1. Descripción general

Esta carpeta contiene el conjunto de pruebas realizadas al sistema de Preguntas y Respuestas (Q&A) desarrollado para Riopaila Castilla.

El objetivo de esta fase es evaluar el desempeño del modelo bajo un escenario controlado, utilizando exclusivamente el contexto cargado desde el archivo `tu_archivo_riopaila.txt`, bajo una arquitectura **NO-RAG basada en Prompt Engineering**.

---

## 2. Metodología de evaluación

Se diseñó un conjunto de **más de 20 preguntas estructuradas**, alineadas con los ejes temáticos definidos en el alcance del sistema:

### 🔹 Categorías evaluadas

- Productos y portafolio empresarial  
- Procesos industriales y generación de energía  
- Historia y fundación de la empresa  
- Estructura organizacional  
- Sostenibilidad y medio ambiente  
- Responsabilidad social corporativa  
- Información financiera y eventos corporativos  
- Validación de conocimiento fuera de dominio  

---

## 3. Conjunto de preguntas utilizadas

### 🟢 Productos y servicios
- ¿Cuáles son los principales productos que comercializa Riopaila Castilla?
- ¿Qué tipos de azúcar produce la compañía?
- ¿Riopaila Castilla produce biocombustibles o alcohol carburante?
- ¿Qué marcas de consumo masivo pertenecen al portafolio?

### 🔵 Procesos industriales y energía
- ¿Cómo genera energía eléctrica la empresa?
- ¿Qué hace la empresa con los excedentes de energía?
- ¿Cómo produce biocombustibles Riopaila Castilla?

### 🟣 Historia y estructura
- ¿En qué año fue fundada Riopaila Castilla?
- ¿Quién fundó la empresa?
- ¿Qué relación existe entre Riopaila y la planta de Castilla?
- ¿Cuál es la misión y visión de la empresa?

### 🟡 Sostenibilidad
- ¿Qué programas ambientales implementa la empresa?
- ¿Cómo maneja el uso del agua en sus cultivos?
- ¿Cuál es el compromiso con la huella de carbono?

### 🟠 Gobernanza y finanzas
- ¿Quiénes conforman la junta directiva?
- ¿Cuándo es la próxima asamblea de accionistas?
- ¿Cuál es el desempeño financiero reciente?

### 🔴 Validación fuera de dominio
- ¿Riopaila fabrica teléfonos celulares?
- ¿La empresa exporta tecnología electrónica?
- ¿Tiene productos de software o hardware?

---

## 4. Resultados obtenidos

### ✔ Comportamiento general del modelo

El sistema demostró los siguientes comportamientos:

- Alta precisión cuando la información está presente en el contexto.
- Respuestas coherentes con tono corporativo estructurado.
- Capacidad de identificar ausencia de información explícita.
- Buen desempeño en preguntas de dominio (productos, energía, sostenibilidad).

---

### Ejemplos representativos

#### Ejemplo 1 – Productos
**Pregunta:** ¿Cuáles son los principales productos de Riopaila Castilla?  
**Resultado:** El modelo identificó correctamente azúcar, biocombustibles, energía verde, fertilizantes y derivados de la caña.

---

#### Ejemplo 2 – Energía
**Pregunta:** ¿Cómo genera energía la empresa?  
**Resultado:** Explicó correctamente el uso del bagazo de caña como fuente de cogeneración energética.

---

#### Ejemplo 3 – Información no disponible
**Pregunta:** ¿Quiénes conforman la junta directiva?  
**Resultado:** El modelo indicó explícitamente que la información no estaba presente en el contexto.

---

#### Ejemplo 4 – Fuera de dominio
**Pregunta:** ¿Riopaila fabrica celulares?  
**Resultado:** Negación correcta, identificando que no pertenece al dominio de la empresa.

---

## 5. Análisis técnico de desempeño

Desde una perspectiva de arquitectura de LLM:

### ✔ Fortalezas observadas
- Buen desempeño del modelo en tareas de **context reasoning**
- Correcta aplicación del principio de **grounding en contexto**
- Estabilidad en inferencia con prompts largos (~18K caracteres)
- Coherencia en respuestas multi-dominio

---

### Limitaciones técnicas

- Dependencia total del contexto embebido (NO-RAG)
- Sensibilidad a la longitud del prompt (context window constraints)
- No existe recuperación dinámica de información
- Repetición del contexto en cada consulta (ineficiencia computacional)

---

## 6. Resultado final

El sistema Q&A implementado demostró ser:

- Funcional en un entorno controlado
- Consistente en respuestas corporativas
- Robusto en pruebas múltiples (20+ preguntas)
- Alineado con la arquitectura NO-RAG definida en el módulo

Sin embargo, su escalabilidad está limitada por la estrategia de **context stuffing**, lo cual justifica su evolución futura hacia arquitecturas tipo RAG.
