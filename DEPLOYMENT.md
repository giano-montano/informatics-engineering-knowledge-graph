# Despliegue de InfoKnows en AWS (Learner Lab)

Cómo está desplegado InfoKnows, cómo se apaga, se enciende, se actualiza y se
reconstruye el grafo. El despliegue en sí (servicios, `.env`, `load` y
`reapply`) está en la sección «Desplegar con Docker» de `docs/operacion.md`; aquí va
solo lo propio del servidor de AWS.

Los identificadores concretos (IP, instancia, grupo de seguridad) están en la
nota privada de `internal-notes/`; aquí se usan `<IP>`, `<INSTANCIA>` y `<SG>`.

## 1. Qué hay desplegado

| Recurso | Nombre (etiqueta `Name`) | Detalle |
|---|---|---|
| Instancia EC2 | `infoknows` | `t3.large` (2 vCPU, 8 GiB), Ubuntu 24.04 LTS, `us-east-1` |
| Disco | `infoknows-root` | gp3, 30 GB; se borra si se *termina* la instancia |
| Grupo de seguridad | `infoknows-sg` | 80 y 443/tcp abiertos; 22/tcp solo desde la IP del operador |
| IP elástica | `infoknows-eip` | Fija: no cambia al apagar y encender |
| Par de claves | `infoknows` | La clave pública `id_ed25519` del operador |

Todos llevan además la etiqueta `Project=infoknows`. Para listarlos:

```bash
aws ec2 describe-instances --filters Name=tag:Project,Values=infoknows \
  --query 'Reservations[].Instances[].[InstanceId,State.Name,PublicIpAddress]' --output table
```

En el servidor, todo vive en `/home/ubuntu/infoknows/`:

- el código: `git archive` de la rama desplegada, sin `.git`;
- `.env`, con permisos 600 y solo lo necesario (ver §5);
- `var/`, con los tres almacenes de la corrida final, copiados de
  `var/medicion-r4/` de la copia principal: `operational.sqlite`, `documents/`
  y `facts/`.

  Hay una diferencia con `var/medicion-r4/`, que se deja intacta como
  evidencia de R4: en el `operational.sqlite` desplegado, y en el de
  `var/ensayo/`, la corrida 6 está cerrada a mano. Esa corrida quedó «en
  curso» porque el worker murió leyendo el PDF de 1INF30, antes de llamar al
  modelo y de escribir, y la cadena siguió en la corrida 7. El 2026-11-17 se
  marcó como fallida, con el motivo en su campo de error y como hora de cierre
  el inicio de la corrida 7, que es una cota superior. Así no figura para
  siempre como en curso (ADR-007). La copia de antes del cambio quedó junto a
  cada almacén, como `operational.before-closing-run-6.sqlite`. El despliegue
  local, en `var/despliegue-local/`, tiene el mismo cambio.

Delante del compose, en el propio host, Caddy termina TLS (§4):

```
internet ─443/80─▶ Caddy (host, systemd) ─▶ 127.0.0.1:8080 nginx (web) ─▶ api:8000 ─▶ neo4j
```

- nginx se publica solo en el loopback (`IEKG_WEB_PORT=127.0.0.1:8080`).
- El 80 lo atiende Caddy: redirige a HTTPS (308) y responde los desafíos de
  Let's Encrypt.
- Los puertos 7474 y 7687 de Neo4j se publican solo en el loopback, y el grupo
  de seguridad tampoco los abre.

## 2. Restricciones del Learner Lab (verificadas el 2026-11-17)

- **Regiones:** solo `us-east-1` y `us-west-2`. El par `vockey` existe solo en
  `us-east-1`.
- **Tipos de instancia:** hasta el tamaño `large`. `t3.xlarge` da
  `UnauthorizedOperation`, comprobado con `run-instances --dry-run`.
- **Disco:** gp2/gp3 de hasta 100 GB.
- **Al terminar la sesión del laboratorio**, las instancias pueden quedar
  detenidas, pero los recursos y los datos se conservan. Al empezar otra sesión
  puede hacer falta encenderla a mano (§6). La IP elástica no cambia.
- **Presupuesto:** solo se ve en la página del Learner Lab. El CLI no tiene
  acceso a la API de precios ni a la de facturación. Si se agota, el
  laboratorio puede borrar los recursos.
- **Las credenciales del CLI** (`AWS_SESSION_TOKEN`) vencen con cada sesión: se
  copian de nuevo desde «AWS Details» del Learner Lab a `.env.aws`, en la raíz
  de la copia principal (ignorado por git), tal como las muestra el
  laboratorio: con `[default]` y las claves en minúscula. Para cargarlas en
  Git Bash, desde la raíz de la copia principal:

  ```bash
  while IFS='=' read -r k v || [ -n "$k" ]; do
    k=$(printf '%s' "$k" | tr -d '[:space:]'); v=$(printf '%s' "$v" | sed 's/^[[:space:]]*//; s/[[:space:]]*$//')
    case "$k" in ''|\#*|\[*) continue;; esac
    export "$(printf '%s' "$k" | tr '[:lower:]' '[:upper:]')=$v"
  done < <(tr -d '\r' < .env.aws)
  export AWS_DEFAULT_REGION=us-east-1 AWS_PAGER="" MSYS_NO_PATHCONV=1
  ```

  `RequestExpired` o `InvalidClientTokenId` quieren decir que la sesión venció
  o que no se cargó el token de sesión.

Fuente: *AWS Academy Learner Lab – Foundation Services* (© 2021, copia
publicada por otra universidad: fuente gris), contrastada con el CLI donde se
pudo.

## 3. Costo

| Estado | Costo aproximado |
|---|---|
| Encendida | 0,091 USD/h ≈ 2,2 USD/día (instancia 0,083 + IPv4 0,005 + disco 0,003) |
| Apagada | ≈ 0,2 USD/día (disco más la IPv4 elástica, que se cobra aunque no esté en uso) |

**Lo que más gasta es dejarla encendida.** Apagarla al terminar cada sesión de
trabajo.

## 4. HTTPS: Caddy en el host

- **Certificado:** de Let's Encrypt para la IP misma, sin dominio. Let's Encrypt
  emite certificados para IP desde enero de 2026, solo con el perfil
  `shortlived` (160 h, unos 6 días). Caddy (paquete oficial, v2.11) lo pide y
  lo renueva solo por http-01, por eso el 80 debe seguir abierto.
- **Si la instancia pasa apagada más de 6 días**, el certificado vence. Al
  encenderla, Caddy pide uno nuevo en segundos; no hay que hacer nada.
- **`default_sni`:** los clientes no mandan SNI cuando se conecta a una IP
  (Chrome, Edge y el curl de Windows tampoco). Sin esa opción global, Caddy no
  sabe qué certificado servir y corta el handshake.
- **Configuración:** `/etc/caddy/Caddyfile`, en el servidor y fuera del repo:

  ```
  {
  	default_sni <IP>
  }

  <IP> {
  	tls {
  		issuer acme {
  			profile shortlived
  		}
  	}
  	encode gzip
  	reverse_proxy 127.0.0.1:8080
  }
  ```

  Tras editarla: `caddy validate --config /etc/caddy/Caddyfile && sudo systemctl reload caddy`.
  Los registros están en `sudo journalctl -u caddy`.
- **Por qué en el host y no como un servicio más del compose:** así no cambia
  nada del repositorio (`docker-compose.yml`, `web/nginx.conf` ni la vista de
  despliegue del C4). Es configuración de este servidor, como `.env`.

Fuentes: [anuncio de Let's Encrypt, 2026-01-15](https://letsencrypt.org/2026/01/15/6day-and-ip-general-availability.html);
[directiva `tls` de Caddy, subdirectiva `profile`](https://caddyserver.com/docs/caddyfile/directives/tls).

## 5. Configuración del servidor

El `.env` del servidor se generó allá mismo y no sale de él:

```
NEO4J_PASSWORD=<aleatoria, openssl rand>
IEKG_OPERATOR_TOKEN=<aleatorio, openssl rand>
IEKG_PUBLIC_BASE_URL=https://<IP>
IEKG_WEB_PORT=127.0.0.1:8080
NEO4J_HEAP_INITIAL=1G
NEO4J_HEAP_MAX=2G
NEO4J_PAGECACHE=1G
```

No lleva claves de proveedores de modelos de lenguaje ni de AWS. El servidor
solo sirve el grafo ya construido; **no ingesta**.

Para leer el token del operador: `ssh ubuntu@<IP> 'grep TOKEN ~/infoknows/.env'`.

**Matiz conocido:** los hechos de la corrida final se ingestaron en local, así
que el localizador guardado de cada documento es
`http://localhost:8000/resources/…`. La web abre los documentos por su ruta
(`documentHref` en `web/src/lib/api-client.js`), no por ese localizador, así
que los enlaces funcionan. Los hechos no se reescriben, para que el grafo siga
siendo exactamente el de la corrida final.

### Qué archivo de variables lee quién

| Archivo | Dónde | Lo lee | Para qué |
|---|---|---|---|
| `.env` | raíz de la copia local | `uv run …` (con `settings.py`) y `docker compose` en local | Desarrollo |
| `.env` | `~/infoknows/` del servidor | solo `docker compose` en el servidor | Producción; no sale de allí |
| `.env.aws` | raíz de la copia local | solo el CLI de `aws`, cargado a mano | Encender, apagar y administrar EC2; no tiene que ver con la aplicación |
| `.env.example` | versionado | nadie | Plantilla |

Precedencias:

- En las dos lecturas, **una variable ya puesta en el entorno gana sobre
  `.env`**: tanto en `settings.py` como en la interpolación de compose.
- **Los contenedores no leen `.env`** (`.dockerignore` lo excluye). Compose
  sustituye los `${…}` de `docker-compose.yml` y les pasa solo las variables
  que ese archivo enumera. Además, fija `NEO4J_URI=bolt://neo4j:7687`.
- Los almacenes (`IEKG_OPERATIONAL_DB` y los demás) no se ponen en contenedores:
  quedan en sus valores por omisión bajo `/app/var`, que es la carpeta
  `IEKG_DATA_DIR` del host.

## 6. Operación

### Entrar por SSH

```bash
ssh ubuntu@<IP>
```

Solo entra la máquina que tenga la clave privada `~/.ssh/id_ed25519` que
corresponde al par `infoknows`, y solo desde la IP permitida en el grupo de
seguridad. Para entrar desde otra máquina, ver §8.

### Apagar

```bash
aws ec2 stop-instances --instance-ids <INSTANCIA>
```

O desde la consola de EC2: *Instance state → Stop*. **No usar *Terminate***:
borra el disco con la base y los almacenes.

### Encender

```bash
aws ec2 start-instances --instance-ids <INSTANCIA>
aws ec2 wait instance-running --instance-ids <INSTANCIA>
```

Los contenedores tienen `restart: unless-stopped`, así que Docker los levanta
solos, y Caddy es un servicio de systemd habilitado. En uno o dos minutos,
`https://<IP>/` responde. Para comprobarlo:
`ssh ubuntu@<IP> 'cd ~/infoknows && docker compose ps'`.

### Actualizar el código

Desde la copia principal, en la máquina local, una vez que `dev` está unida a
`main`:

```bash
git archive --format=tar.gz -o infoknows.tar.gz main
scp infoknows.tar.gz ubuntu@<IP>:~
ssh ubuntu@<IP> 'tar -xzf ~/infoknows.tar.gz -C ~/infoknows && rm ~/infoknows.tar.gz \
  && cd ~/infoknows && docker compose up -d --build'
```

`git archive` no lleva `.env` ni `var/`, así que los dos se conservan. Los
archivos que se hayan borrado en la rama sí quedan en el servidor. Si eso
importa, vaciar antes `~/infoknows`, salvo `.env` y `var/`.

Consideraciones:

- **Solo se despliega lo commiteado.** `git archive` toma el commit, no el
  árbol de trabajo. La rama que se despliega es `main`: el trabajo se hace en
  `dev` y se une a `main` antes de desplegar.
- **Si solo cambió `web/`:** `docker compose up -d --build web` reconstruye
  solo la web (un minuto o menos) y no reinicia la API.
- **Si cambió `src/`:** se reconstruye la imagen de la aplicación. La capa de
  dependencias queda en caché mientras `uv.lock` no cambie, y la API se
  reinicia en unos segundos.
- **Si cambió el esquema** (`graph_schema.py`, las reglas, la proyección o la
  ontología): después de desplegar hay que reconstruir el grafo (ver
  «Reconstruir el grafo», abajo). Si cambiaron claves o la T-Box, los hechos
  ya no sirven sin una migración (ADR-004).
- **El servidor no ingesta:** no tiene clave del proveedor del modelo de
  lenguaje. Tampoco hay que correr allí el recorrido del operador (CA-11),
  porque escribe en el grafo.
- **Disco:** cada reconstrucción deja imágenes viejas.
  `docker image prune -f` las borra.

### Modo ensayo del operador

El servidor queda en modo ensayo (`IEKG_REHEARSAL=1` en su `.env`): el panel
del operador funciona completo, pero los envíos no tocan el grafo ni los
almacenes reales. Las corridas de ensayo viven en `~/infoknows/var/ensayo/`.
El panel está en `https://<IP>/?panel=operador`; el token, en el `.env` del
servidor (§5).

Las variables de `.env` se leen solo cuando arranca un contenedor. Por eso,
después de editar el `.env`, `docker compose up -d api` recrea solo el
contenedor de la API con el valor nuevo. Mientras arranca, unos 15 segundos,
el panel y la navegación dan error; Neo4j y la web no se reinician.

```bash
ssh ubuntu@<IP>
cd ~/infoknows
sed -i 's/^IEKG_REHEARSAL=.*/IEKG_REHEARSAL=0/' .env && docker compose up -d api   # apagarlo
sed -i 's/^IEKG_REHEARSAL=.*/IEKG_REHEARSAL=1/' .env && docker compose up -d api   # encenderlo
docker compose stop api && sudo rm -rf var/ensayo && docker compose start api   # borrar el historial de ensayo
```

Al encenderlo por primera vez, o tras borrar `var/ensayo/`, el historial de
ensayo empieza como copia del real.

El modo ensayo prueba el flujo del panel, no la ingesta. Para una ingesta de
ensayo completa, con Docling y un proveedor simulado, en local: `web/README.md`,
«CA-11 con una ingesta completa y un proveedor simulado».

### Reconstruir el grafo

Con la API detenida y Neo4j encendido (ADR-007):

```bash
cd ~/infoknows
docker compose stop api
docker compose run --rm build load && docker compose run --rm build reapply   # los dos deben salir con 0
docker compose start api
```

`reapply` se rechaza si la base ya tiene nodos institucionales: siempre va
justo después de `load`.

Para comprobar los conteos, sin exponer la contraseña en la línea de comandos:

```bash
docker exec iekg-neo4j sh -c 'cypher-shell -u neo4j -p "$HEALTHCHECK_PASSWORD" \
  "MATCH (n) WITH count(n) AS nodos MATCH ()-[r]->() RETURN nodos, count(r) AS aristas"'
```

Con la corrida final, el resultado debe ser **818 nodos y 2 898 aristas**.

### Ver el Neo4j Browser

Por túnel SSH, no desde internet:

```bash
ssh -L 7474:localhost:7474 -L 7687:localhost:7687 ubuntu@<IP>
# luego, en el navegador local: http://localhost:7474
```

## 7. Cómo se hizo el despliegue inicial

1. Se verificaron las restricciones del §2 con el CLI y la documentación.
2. Se importó la clave pública del operador como par `infoknows`, y se crearon
   el grupo de seguridad, la instancia y la IP elástica, todos etiquetados.
3. Al arrancar, el *user data* de la instancia agregó 2 GB de swap e instaló
   Docker Engine y el plugin de compose desde el repositorio oficial de Docker.
4. Se subieron al servidor la rama `r6-web` (`git archive` + `scp`) y los tres
   almacenes de `var/medicion-r4/`.
5. Se generó el `.env` del §5 en el servidor y se construyeron las imágenes
   allá (`docker compose build`).
6. Se levantó Neo4j y se ejecutaron `load` y `reapply` con la API detenida.
   Después se levantó todo.
7. Se agregó HTTPS (§4): se abrió el 443, se instaló Caddy desde su
   repositorio oficial y se pasó nginx al loopback.
8. Se comprobó desde fuera, sobre HTTPS:
   - la web responde;
   - `/api/overview` trae los 13 cursos;
   - un PDF de `/resources` abre;
   - las rutas de operación dan 401 sin token;
   - 7474, 7687, 8000 y 8080 no responden;
   - `http://` redirige a `https://`.

## 8. Problemas frecuentes

- **El SSH no conecta (timeout):** probablemente cambió la IP pública del
  operador. Hay que actualizar la regla del 22:

  ```bash
  MI_IP=$(curl -s https://checkip.amazonaws.com)
  aws ec2 authorize-security-group-ingress --group-id <SG> \
    --ip-permissions "IpProtocol=tcp,FromPort=22,ToPort=22,IpRanges=[{CidrIp=$MI_IP/32,Description=ssh-operador}]"
  # y revocar la regla vieja con revoke-security-group-ingress
  ```

- **Entrar desde otra máquina:** se agrega la clave pública de esa máquina a
  `~/.ssh/authorized_keys` del servidor, entrando desde una máquina que ya
  tenga acceso, y se permite su IP en el 22 como en el punto anterior. No hace
  falta copiar la clave privada.
- **`aws` falla con `ExpiredToken`:** la sesión del laboratorio venció. Hay
  que copiar las credenciales nuevas a `.env.aws`.
- **El navegador dice «tardó demasiado en responder» en `https://`:** el 443
  está cerrado en el grupo de seguridad, o Caddy está caído
  (`systemctl status caddy`).
- **Error de handshake TLS** (`SEC_E_ILLEGAL_MESSAGE`, `ERR_SSL_PROTOCOL_ERROR`):
  falta `default_sni` en el Caddyfile.
- **El curl de Windows con `-o` y `-w` da `(43) bad argument` sobre HTTPS:**
  es un problema de ese curl, no del servidor. Para ver el estado se usa
  `curl -s -D - -o NUL <url>`.
- **La web da 502 justo después de encender:** la API todavía está
  arrancando. Esperar a que `docker compose ps` la muestre `(healthy)`.
