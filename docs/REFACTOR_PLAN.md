# Plan de refactor — ITC Deportes

Documento de arquitectura para la reconstrucción del núcleo del sistema.
Estado: **aprobado en decisiones marco, pendiente de ejecución.**

---

## 1. Objetivo

Convertir un script acoplado a una institución en un **motor genérico de gestión de
competiciones deportivas**, escalable y configurable, donde:

- El organizador registra competidores y el sistema automatiza sorteos de grupos y/o partidos.
- El equipo organizador carga resultados y el sistema deriva puntos, clasificaciones y eliminados.
- El usuario común consulta resultados, tablas y estado de las competiciones.

## 2. Decisiones marco

| Decisión | Elección |
|---|---|
| Alcance | **Motor genérico configurable.** Deportes, categorías, divisiones y formatos son datos, no constantes. ITC queda como configuración precargada. |
| Persistencia | **Esquema nuevo, sin backfill.** El partido deja de ser texto y pasa a ser relacional; los datos anteriores se descartan (revisado, ver §13). |
| Motor de datos | **Supabase se mantiene.** Ver §7. |
| Roles | **Admin, Registrador, Visitante.** El Registrador es una concesión *por competición*, no un rol global. |
| Arquitectura | **Clean Architecture**, con la regla de dependencia impuesta y verificada. |
| Configuración ITC | **Sin plantillas.** El deporte y la puntuación se eligen del catálogo de reglas al crear cada competición (revisado, ver §13). |
| Commits | **Atómicos + Conventional Commits.** Solo se compromete software completo y ejecutable. |

## 3. Diagnóstico del código actual

| # | Problema | Evidencia |
|---|---|---|
| 1 | No existe capa de dominio; las reglas viven entre llamadas HTTP | `data.py` completo |
| 2 | Identidad por string: `"Nombre (Curso) vs Nombre (Curso)"`, re-parseado con regex | `data.py:79-105`, `data.py:449` |
| 3 | Corrupción de datos como consecuencia del punto 2 | `limpiar_equipos_corruptos()`, `data.py:175` |
| 4 | Cableado a una institución (grados 6°–11°, 4 deportes, 3 categorías) | `data.py:16-37` |
| 5 | Reglas fijas: 3/1/0, desempate único, 7 jornadas forzadas, sábado 15:00 | `data.py:382`, `data.py:399`, `data.py:456-468` |
| 6 | Voleibol es inexpresable: se puntúa por goles y empates | `calcular_tabla`, `data.py:431` |
| 7 | Fase eliminatoria escrita pero **no conectada** a la UI | `data.py:487-679`, sin importadores |
| 8 | Autorización cosmética: el rol solo esconde botones | `app.py:350`, `app.py:414` |
| 9 | El dominio importa Streamlit (`st.secrets`, `st.cache_resource`) | `data.py:40-46` |
| 10 | N+1 en consultas y escrituras | `app.py:741`, `_propagar_ganadores` |

## 4. Arquitectura y paradigma

**Clean Architecture.** Cuatro capas concéntricas y una única regla innegociable:

> **Regla de dependencia: el código fuente solo puede apuntar hacia adentro.**
> Nada en una capa interior conoce el nombre de nada en una capa exterior.

| Capa | Contenido | Puede importar |
|---|---|---|
| **Entidades** (`domain/`) | Participante, Competicion, Enfrentamiento, Marcador, reglas | Solo stdlib |
| **Casos de uso** (`aplicacion/`) | Servicios, puertos, permisos | `domain` |
| **Adaptadores** (`infraestructura/`) | Repositorios Supabase y memoria, mapeadores | `domain`, `aplicacion` |
| **Frameworks** (`ui/`) | Streamlit, componentes, view-models | todas |

Consecuencias prácticas, no decorativas:

- `domain/` **no importa** `supabase`, `streamlit`, `bcrypt` ni nada de `infraestructura/`.
- Los casos de uso hablan con `Protocol`s definidos en `aplicacion/puertos.py`;
  las implementaciones concretas se inyectan desde fuera.
- Los datos cruzan hacia adentro como estructuras del dominio, nunca como filas de
  Supabase ni como `dict` crudos de la API.
- **La regla se verifica en CI**, no por disciplina. Ver §11.

Dentro de esas capas, el paradigma es **OOP con estrategias intercambiables;
cálculos como funciones puras.**

- **Objetos** para entidades con identidad y para reglas variables (patrón Strategy).
- **Funciones puras** para clasificación y fixtures: entran partidos, sale una tabla.
- **`typing.Protocol`** para inversión de dependencias sin jerarquías de herencia.

Pago concreto en SOLID:

- **SRP** — dominio, persistencia y presentación separados.
- **OCP** — deporte, sistema de puntos o formato nuevo = una clase nueva, cero ediciones.
- **LSP** — repositorios intercambiables (Supabase / memoria).
- **ISP** — un puerto estrecho por agregado, no un repositorio-dios.
- **DIP** — los servicios dependen de protocolos, nunca de Supabase.

## 5. Estructura objetivo

```
src/itc_deporte/
  domain/                    # cero dependencias externas
    participante.py          # Participante: cubre equipo E individuo
    competicion.py           # Competicion, Fase, Division, Grupo
    enfrentamiento.py        # Enfrentamiento, Marcador (con parciales/sets)
    reglas/
      puntuacion.py          # Protocol + VictoriaDerrota, PorSets, Personalizado
      desempate.py           # Protocol + criterios componibles
      fixture.py             # Protocol + RoundRobin, Eliminacion, Grupos, Suizo
    motor/
      clasificacion.py       # función pura: enfrentamientos -> tabla
      bracket.py             # propagación de ganadores en memoria
  aplicacion/
    puertos.py               # Protocols de repositorios y autenticación
    servicios/               # casos de uso
    permisos.py              # roles y concesiones
  infraestructura/
    supabase/                # adaptadores
    memoria/                 # repositorios en memoria (tests)
  ui/                        # Streamlit: adaptador delgado
  legado/                    # código heredado congelado, muere en la Fase 8
tests/
```

El paquete vive bajo `src/` y se instala en modo editable (`pip install -e .`),
de modo que Streamlit lo resuelve desde la raíz y los tests vía `pythonpath`.

### Decisiones de modelado clave

**`Participante`, no `Equipo`.** Cubre competiciones por equipos e individuales
(atletismo, ajedrez) con un solo tipo. Tiene identidad propia (`id`), no un nombre
compuesto.

**`Division` generaliza "curso".** Jerárquica: la categoría PRIMERA contiene las
divisiones 601, 602… En otra institución podría ser sede, edad o peso.

**`Marcador` con parciales.** Además del total, una lista opcional de parciales.
Voleibol registra sets; fútbol deja la lista vacía. Es lo que hace expresable el
problema 6.

**`Competicion` compone fases.** Una lista ordenada de `FaseDeGrupos` y/o
`FaseEliminatoria`, que es exactamente el "grupos y/o partidos" del requisito.

**`PlantillaDeCompeticion` es un dato del dominio.** Ver §6.

### Seams de extensión (OCP)

```python
class SistemaDePuntuacion(Protocol):
    def puntos(self, marcador: Marcador) -> tuple[int, int]: ...

class GeneradorDeFixture(Protocol):
    def generar(self, participantes: Sequence[Participante],
                cfg: ConfigFixture) -> list[Jornada]: ...
```

Los criterios de desempate se componen como lista ordenada
(`[PorPuntos(), PorDiferencia(), PorEnfrentamientoDirecto()]`). Nota: el
enfrentamiento directo necesita contexto de partidos, por lo que el criterio recibe
la clasificación completa, no solo la fila.

## 6. Plantillas de competición

Una **plantilla** es una descripción serializable de cómo se arma una competición:
deporte, divisiones, sistema de puntuación, criterios de desempate, formato de fases
y calendario por defecto. Instanciarla produce una `Competicion` editable.

Esto es lo que evita que la configuración ITC quede cableada como caso especial:

- ITC es **la primera plantilla del catálogo**, no una rama de código.
- Se carga en el arranque desde `infraestructura/plantillas/itc.json` (semilla
  versionada en el repo), como cualquier otra.
- Un usuario que cree su propia plantilla usa exactamente el mismo mecanismo.

### Plantilla ITC precargada

Reproduce fielmente los datos que el software ya maneja hoy:

| Elemento | Valor |
|---|---|
| Categorías → divisiones | PRIMERA: 601–609, 701–708 · SEGUNDA: 801–808, 901–906 · TERCERA: 1001–1003, 1101–1104 |
| Deportes | Balonmano 🤾, Microfútbol ⚽, Baloncesto 🏀, Voleyball 🏐 |
| Puntuación | 3 / 1 / 0 (Voleyball pasa a puntuación por sets — ver §12) |
| Desempate | Puntos → diferencia → a favor |
| Formato | Round-robin + eliminación directa |
| Calendario | Sábados 15:00, semanal |

### En la UI

Al crear una competición, el diálogo abre con una pestaña **"Plantillas"** donde
aparece ITC junto a las demás. La otra pestaña permite partir de cero. Elegir
plantilla precarga el formulario; todo queda editable antes de confirmar — la
plantilla es un punto de partida, no un candado.

## 7. Modelo de permisos

Tres roles. El Registrador es una **concesión con alcance**:

| Rol | Alcance | Puede |
|---|---|---|
| Visitante | Global | Leer competiciones, tablas, resultados, brackets |
| Registrador | Por competición | Lo anterior + registrar resultados y participantes en las competiciones asignadas |
| Admin | Global | Todo: crear competiciones, ejecutar sorteos, gestionar registradores |

Tabla de concesiones `(usuario_id, competicion_id, rol)`. El Admin añade
registradores por correo — o por `username` si no hay correo — desde un panel de
Registradores.

**La validación ocurre en la capa de servicio**, no escondiendo botones. Un caso de
uso invocado directamente sin permiso falla.

## 8. Por qué se mantiene Supabase

1. **Ya es Postgres.** "Postgres directo" no aporta nada en la capa de datos.
2. **Se perderían gratis:** RLS como segunda línea de defensa, backups gestionados,
   API REST sin mantenimiento.
3. **Encaja con Streamlit.** Cada interacción reejecuta el script; HTTP tolera eso.
   Con `psycopg` habría que resolver pooling de conexiones a través de reruns.

El puerto de repositorio existe para **testear sin red**, no para migrar fuera.

**Decidido y aplicado en la Fase 6:** se sustituye la tabla `usuarios` con
bcrypt propio por **Supabase Auth**, que provee invitación por correo,
recuperación de contraseña y `auth.uid()` para RLS. El procedimiento de
migración de los usuarios existentes está en `docs/MIGRACION_AUTH.md`; se
ejecuta en la Fase 7.

## 9. Esquema objetivo (borrador)

```
deportes(id, nombre, icono, config_default)
competiciones(id, nombre, deporte_id, temporada, estado, reglas_json)
divisiones(id, competicion_id, nombre, padre_id)          -- jerárquico
participantes(id, competicion_id, division_id, nombre)    -- identidad = id
miembros(id, participante_id, nombre, dorsal)             -- antes: jugadores
fases(id, competicion_id, tipo, orden)
grupos(id, fase_id, nombre)
enfrentamientos(id, fase_id, grupo_id, jornada, ronda, slot,
                local_id, visitante_id, fecha, estado)
marcadores(enfrentamiento_id, total_local, total_visitante, parciales_jsonb)
concesiones(usuario_id, competicion_id, rol)
plantillas(id, nombre, descripcion, definicion_jsonb, es_semilla)
logros(id, deporte_id, anio, descripcion)
```

### Backfill

El parser de strings (`parsear_enf`) se usa **una última vez** para resolver los
enfrentamientos legacy a IDs de participante, y luego se elimina del código.

**Requisito del script:** las filas irresolubles (nombres ambiguos, duplicados,
cursos inválidos) se emiten en un **reporte de conflictos** para resolución manual.
No se descartan en silencio. Respaldo obligatorio antes de ejecutar.

## 10. Fases

| Fase | Qué | Entregable verificable |
|---|---|---|
| 0 | Extraer funciones ya casi puras (`_generar_round_robin`, `_gen_seeds`, `calcular_tabla`) y fijar comportamiento actual con tests | `pytest` verde sin BD |
| 1 | Modelo de dominio puro. **Muere el parseo de strings** | Dominio importable sin Streamlit ni Supabase |
| 2 | Reglas como estrategias: puntuación, desempate, fixture | Voleibol correcto sin tocar código previo |
| 2b | `PlantillaDeCompeticion` + semilla ITC en `plantillas/itc.json` | Instanciar la plantilla ITC reproduce la configuración actual |
| 3 | Motor: clasificación y brackets con propagación **en memoria** (una escritura, no N) | Tests de fases completas |
| 4 | Puertos y adaptadores + **DDL del esquema nuevo**. Sale `st.secrets` de la capa de datos | Suite completa contra repositorio en memoria, sin red |
| 5 | Servicios de aplicación (casos de uso) | La UI deja de decidir |
| 6 | Roles, concesiones y autenticación | Permiso denegado aunque se invoque el caso de uso directamente |
| 7 | Migración de esquema + backfill con reporte de conflictos | Datos actuales íntegros en el modelo nuevo |
| 8 | Streamlit como adaptador delgado, pestaña **"Plantillas"** al crear competición. **Se conecta el bracket muerto** | Paridad funcional + fase eliminatoria viva |

Las fases 0–5 no tocan la UI: el sistema sigue operando mientras el núcleo se
reconstruye debajo. El esquema se diseña en la Fase 4 (deriva del dominio ya
estabilizado) y se aplica en la 7.

## 11. Workflow

### Regla del repositorio

> **A `main` solo se compromete software completo y ejecutable.**
> Cada commit deja la aplicación funcionando. Nada de código a medias, imports
> rotos, ni funciones sin conectar esperando "el siguiente commit".

Esto tiene una consecuencia inmediata sobre el plan: **una fase no es un commit.**
Cada fase se descompone en commits atómicos, cada uno de los cuales deja el sistema
verde. Y un antipatrón concreto a evitar, porque este repo ya lo sufre: el bracket
de `data.py:487-679` se comprometió sin conexión a la UI y lleva desde entonces
muerto. Código que se compromete sin usarse es deuda, no progreso.

### Commits atómicos

- **Un cambio conceptual por commit.** Si el mensaje necesita un "y", probablemente
  son dos commits.
- Refactor y cambio de comportamiento **nunca** en el mismo commit. Mezclarlos hace
  ilegible la revisión y el `git bisect`.
- El commit incluye sus tests. No existe "commit de código" seguido de "commit de
  tests".

### Conventional Commits

```
<tipo>(<ámbito>): <descripción en imperativo>
```

Tipos: `feat`, `fix`, `refactor`, `test`, `docs`, `chore`, `perf`, `build`, `ci`.
Ámbitos de este proyecto: `domain`, `reglas`, `motor`, `aplicacion`, `infra`,
`plantillas`, `ui`, `db`.

```
feat(reglas): añadir sistema de puntuación por sets para voleibol
refactor(domain): reemplazar identidad por string con ParticipanteId
test(motor): cubrir propagación de ganadores con byes
feat(db)!: migrar enfrentamientos a IDs relacionales
```

Los cambios que rompen compatibilidad llevan `!` y una nota `BREAKING CHANGE:` en
el cuerpo — la migración de esquema de la Fase 7 califica.

### Testing

Pirámide, con el peso abajo:

| Nivel | Cubre | Dependencias |
|---|---|---|
| **Unitarios** | Reglas de puntuación, desempate, generadores de fixture, clasificación, propagación de brackets | Ninguna. Sin red, sin BD |
| **Integración** | Adaptadores de repositorio contra el contrato del puerto | Repositorio en memoria; Supabase solo en suite marcada |
| **Casos de uso** | Servicios completos con repositorio en memoria, incluidos permisos denegados | Ninguna |

Reglas:

- **Nada de la capa `domain/` se compromete sin tests unitarios.** Es código puro:
  no hay excusa de "difícil de testear".
- Todo `fix` llega con un test que falla sin el arreglo.
- Los casos borde que hoy están implícitos se hacen explícitos en tests: número impar
  de participantes (BYE), byes en bracket, empates en desempate, competición sin
  partidos jugados, participante sin miembros.
- El **contrato del puerto** se prueba una vez y se ejecuta contra ambas
  implementaciones (memoria y Supabase). Así el repositorio en memoria no puede
  divergir del real en silencio.

Herramientas: `pytest`, `pytest-cov`. Fixtures compartidos en `tests/conftest.py`.

### Verificación de la regla de dependencia

La Clean Architecture se erosiona por descuido, no por decisión. Se impone en CI:

- Test que falla si `domain/` importa algo fuera de la stdlib.
- Test que falla si `aplicacion/` importa `infraestructura/` o `ui/`.

Es un test de arquitectura, corre con la suite, y es la diferencia entre tener Clean
Architecture y decir que se tiene.

### Definición de "terminado"

Un commit entra si y solo si:

1. La suite pasa completa.
2. Trae los tests de lo que añade.
3. La app arranca y la funcionalidad tocada opera de punta a punta.
4. No deja código sin conectar.
5. El mensaje sigue Conventional Commits y describe un solo cambio.

## 12. Cambios de comportamiento a confirmar

- **Jornadas.** Hoy `range(7)` fuerza 7 jornadas repitiendo o truncando el
  round-robin. El motor genérico produce n−1 jornadas naturales. Si el ITC necesita
  exactamente 7, pasa a ser configuración explícita, no un número mágico.
- **Fechas de fixture.** Hoy fijas a sábado 15:00. Pasan a ser configurables por
  competición.
- **Tope de bracket.** Hoy top-16 fijo. Pasa a depender del formato configurado.


## 13. Decisiones revisadas durante la ejecución

Dos decisiones marco se cambiaron al ver el alcance real. Quedan aquí y no
borradas de §2, para que el porqué no se pierda.

### Nº2 — Fuera el backfill

**Era:** migrar el esquema arrastrando los datos existentes, resolviendo los
enfrentamientos de texto a IDs con reporte de conflictos.

**Es:** los datos anteriores se descartan y el sistema arranca en limpio.

**Por qué:** el backfill se llegó a escribir y funcionaba —786 líneas con tests
que garantizaban que ninguna fila se perdiera en silencio—, pero migrar datos que
no se quieren conservar es riesgo sin beneficio. Empezar limpio elimina de un
golpe la resolución de conflictos y la corrupción heredada que
`limpiar_equipos_corruptos` venía tapando.

**Coste:** se pierde el histórico de equipos, jugadores, partidos y llaves.

### Nº6 — Fuera las plantillas

**Era:** la configuración del ITC como plantilla precargada, cargada desde
`plantillas/itc.json` como cualquier otra, con una pestaña "Plantillas" al crear
competición.

**Es:** no hay plantillas. Crear una competición es armarla y darla de alta.

**Por qué:** la plantilla existía para que la configuración del ITC no fuera
código privilegiado. Si esa configuración no se precarga, la capa entera sobra:
lo que de verdad mantiene deportes y puntuaciones como dato configurable es
`domain/reglas/catalogo.py`, no la plantilla que se apoyaba en él.

**Consecuencia sobre la Fase 8:** desaparece la pestaña "Plantillas" del
entregable. Crear una competición es un formulario.
