# Nivel Contexto C4 - KMS para el descubrimiento de recursos en Ingeniería Informática
```mermaid
C4Context
title KMS de conocimiento curricular — Nivel 1: Contexto

Person(student, "Estudiante", "Consulta y navega por el conocimiento curricular y sus recursos")
Person(operator, "Operador del grafo", "Incorpora material, observa las corridas y verifica la integridad")

System(kms, "KMS de conocimiento curricular", "Hace explícitas y navegables las relaciones entre áreas, unidades, temas, conceptos, cursos y recursos de Ingeniería Informática")

System_Ext(llm, "Proveedor de modelo de lenguaje", "Recibe texto y devuelve estructura candidata para la extracción de conocimiento")

Rel(student, kms, "Consulta y navega")
Rel(operator, kms, "Incorpora material y verifica integridad")
Rel(kms, llm, "Envía texto y recibe estructura candidata")
```