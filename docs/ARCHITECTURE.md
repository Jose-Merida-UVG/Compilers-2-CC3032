# Arquitectura

Panorama del compilador de Compiscript (Compiladores 2, CC3032). Cada fase tiene
su propio documento; este solo muestra cómo encajan.

| Documento | Contenido |
|---|---|
| [`semantic.md`](semantic.md) | Proyecto 1: sistema de tipos, tabla de símbolos, checker, reglas, errores y pruebas |
| [`tac.md`](tac.md) | Proyecto 2: lenguaje intermedio (TAC), reciclaje de temporales, layout de memoria, generador y pruebas |
| [`enunciados/`](enunciados/) | Texto de los enunciados: definición del lenguaje y requisitos del P1 |
| [`archive/`](archive/) | Material de trabajo ya superado (el contrato de equipo del P2) |

## Pipeline

El compilador se construye por fases acumulativas (Aho et al., 2006): léxico →
sintáctico → semántico → código intermedio (→ futuro: código objeto MIPS). Parte
del analizador léxico/sintáctico de un laboratorio previo, hecho con ANTLR4.

```
código fuente
   │  CompiscriptLexer            caracteres → tokens
   ▼
   │  CompiscriptParser           tokens → árbol de análisis
   ▼
   │  SemanticChecker             árbol → errores + tabla de símbolos
   │                              + anotaciones por nodo (tipo, símbolo, ámbito)
   ▼
errores[]  +  árbol de ámbitos  +  anotaciones
   │  si errores == [] ──────────────────────────────┐
   │                                                 ▼
   │                                      TACGenerator (src/tac/)
   │                                      árbol anotado → TAC (texto)
   │                                                 │
   │  semantic/layout.py  ◄── picos de temporales ───┘
   ▼        tamaños, offsets, direcciones, registros de activación
errores[] + TAC (o None) + tabla de símbolos completa
```

`src/compiler.py` orquesta las etapas y es el único lugar que conoce el pipeline
completo; el CLI (`main.py`) y el servidor (`server.py`) pasan por ahí para no
divergir.

- **El análisis semántico solo corre si no hubo errores léxicos ni
  sintácticos.** ANTLR se recupera de errores de sintaxis inventando y saltando
  tokens, así que recorrer ese árbol dañado produciría una avalancha de errores
  semánticos falsos encima del error real.
- **El TAC solo se genera si no hubo ningún error** (léxico, sintáctico o
  semántico): `analyze()` devuelve `tac = None` en cuanto hay uno.
- La única modificación a la gramática heredada fue agregar `float`
  (`FloatLiteral` y `float` en `baseType`), porque el enunciado exige verificar
  tipos entre `integer` y `float`.

## Archivos

| Archivo | Rol |
|---|---|
| `src/grammar/Compiscript.g4` | Gramática. Fuente de verdad de qué formas existen. |
| `src/generated/` | Lexer, parser y visitor generados por `make generate`. Nunca se editan a mano. |
| `src/error_listener.py` | Errores léxicos y sintácticos en español, con recuperación. |
| `src/semantic/types.py` | Jerarquía de tipos y reglas de asignabilidad. |
| `src/semantic/symbols.py` | `Symbol`, `Scope`, `SymbolTable`. |
| `src/semantic/errors.py` | `SemanticError` y su lista acumulada. |
| `src/semantic/checker.py` | `SemanticChecker`: el recorrido y todas las reglas; anota cada nodo para el generador. |
| `src/semantic/layout.py` | Tamaños, offsets, direcciones, registros de activación y layout de clases. |
| `src/tac/` | Generación de código intermedio: `generator.py`, `gen_core.py`, `gen_control.py`, `gen_functions.py`, `gen_classes.py`, `emitter.py`, `instructions.py`. |
| `src/compiler.py` | Pipeline compartido. |
| `src/server.py` + `frontend/` | IDE: endpoint `/api/run` y paneles de errores, árbol, tabla de símbolos y TAC. |
| `src/tests/` | Pruebas: `semantic/<categoría>/` (P1) y `tac/<área>/` (P2). |
| `workspace/` | Directorio de trabajo del IDE; `input/comp-tac/` tiene los demos del P2. |

## Herramientas

- **ANTLR4 4.13.2**: lexer, parser y clases base Visitor/Listener desde la
  gramática. Se usó el patrón **Visitor** para el recorrido semántico.
- **Python 3.9+** con `antlr4-python3-runtime`, para el checker y el generador.
- **FastAPI + Uvicorn**: el analizador como servicio HTTP local.
- **React + TypeScript + Vite + Monaco Editor**: el IDE web.
- **pytest**: la batería de pruebas (`make test`).

## Reparto del trabajo

Ambos proyectos se repartieron entre las mismas tres personas, con un dueño único
por archivo o por regla para no pisarse. La referencia final es el historial de
commits de cada integrante; el detalle está en la última sección de cada
documento de fase.

| Integrante (usuario de GitHub) | Proyecto 1 (semántico) | Proyecto 2 (código intermedio) |
|---|---|---|
| Camila Richter (`Cami`) | tabla de símbolos y ámbitos | diseño del TAC y reciclaje de temporales (`instructions.py`, `emitter.py`, `generator.py`), anotaciones del checker, integración en `compiler.py`, `main.py` y `server.py`, y la GUI |
| Marinés García (`NESHGP04`) | sistema de tipos y funciones | declaraciones, expresiones, control de flujo y try/catch (`gen_core.py`, `gen_control.py`) |
| Jose Antonio Mérida (`TonitoMC`) | control de flujo, clases, arreglos, IDE | funciones, recursividad, clases y herencia (`gen_functions.py`, `gen_classes.py`), y tabla de símbolos con layout de memoria (`layout.py`, `symbols.py`) |

Detalle: [`semantic.md`](semantic.md) §10 y [`tac.md`](tac.md) §14.

## Conclusiones

1. El sistema de tipos (promoción numérica, `ErrorType` contra las cascadas,
   `UnknownType` para inferencia diferida) junto con una tabla de símbolos como
   árbol permanente de ámbitos cubrió todas las reglas del enunciado del P1 sin
   reescribir la base léxica y sintáctica.
2. Las tres restricciones obligatorias del P1 se cumplen: recuperación de
   errores en las tres fases sin mensajes repetidos o derivados, uso de un
   generador (ANTLR4) y una interfaz gráfica que selecciona el archivo y muestra
   errores, árbol de derivación y tabla de símbolos.
3. `types.py` y `symbols.py` se diseñaron para reutilizarse: el P2 las usó tal
   cual (solo se agregaron anotaciones por nodo y los campos de memoria), y la
   fase de código objeto podrá hacerlo igual.
4. En el P2, el dueño único por regla y las pruebas por área (válidos, inválidos,
   invariantes del TAC y cobertura de la rúbrica) permitieron integrar los
   mixins sin pisarse. Que el TAC sea texto plano
   estilo *Dragon Book*, con temporales reciclados por función y una tabla de
   símbolos que ya guarda tamaños, direcciones y registros de activación, deja la
   fase de código objeto sin necesidad de volver a recorrer el árbol.
