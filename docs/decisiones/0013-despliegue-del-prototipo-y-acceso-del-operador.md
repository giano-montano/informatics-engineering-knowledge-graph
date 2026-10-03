# ADR-013: Despliegue del prototipo y acceso del operador

**Estado:** Aceptada
**Fecha:** 2026-10
**Atributos:** AC-04 (principal), AC-01, AC-02

## Contexto

El prototipo se despliega en una máquina virtual con Ubuntu que provee la especialidad, con los contenedores que fija ADR-007. Falta decidir dónde persiste cada almacén y cómo se protegen las rutas de operación, que disparan escrituras en el grafo y consumo del proveedor del modelo de lenguaje.

## Decisión

- **Un solo host**, la máquina virtual, con Docker Compose. La corrida de medición se ejecuta en ese host, desde la carga.
- **La base de grafos usa un volumen administrado por Docker**: su contenido se reconstruye con una carga y una reaplicación (ADR-004).
- **Los tres almacenes de archivos —operacional, de documentos y de hechos— son carpetas del host**, montadas en los contenedores de la aplicación y de construcción. Guardan lo que no se puede reconstruir, y se abren, respaldan y copian como carpetas.
- **Las rutas de operación exigen un token fijo**: un secreto en la configuración del servidor, que el panel del operador envía en cada petición y la API compara. No hay cuentas ni roles. Las rutas de navegación son públicas.

## Alternativas consideradas

| Alternativa | Motivo del descarte |
|---|---|
| Todos los almacenes en volúmenes administrados | `docker compose down -v` borraría el historial de corridas, los documentos y los hechos, que no se reconstruyen; además, respaldarlos exigiría pasar por Docker. |
| La base de grafos también en una carpeta del host | No aporta nada: su contenido se reconstruye por completo. |
| Autenticación básica en nginx | La protección dependería de la configuración del proxy y no existiría en desarrollo, donde no hay nginx. Con el token, vive en la API y se prueba con ella. |
| Cuentas de usuario o inicio de sesión institucional | Desproporcionado para un solo operador. |
| Sin protección, confiando en la red de la universidad | Cualquiera en esa red podría subir documentos, gastar la cuota del proveedor y escribir en el grafo. |

## Consecuencias

- Respaldar el sistema es copiar tres carpetas; la base de grafos no se respalda, se reconstruye.
- Sin HTTPS, el token viaja sin cifrar. Si la máquina virtual no ofrece HTTPS, se declara como limitación.
- Quien tenga el token puede escribir en el grafo. Cambiarlo exige reiniciar la API, lo que interrumpe una ingesta en curso (ADR-007).
- El host queda escrito en los localizadores (ADR-009).
