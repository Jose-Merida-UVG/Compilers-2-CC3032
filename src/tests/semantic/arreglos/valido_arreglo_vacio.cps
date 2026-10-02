// `[]` no tiene de dónde inferir su elemento (ArrayType(unknown)), así que
// debe entrar en cualquier arreglo, con o sin anotación y a cualquier
// profundidad de anidamiento (ver _element_fits en semantic/types.py).
let vacio: integer[] = [];
let luego = [];
luego = [1, 2];
let anidado: integer[][] = [];
let interno: integer[][] = [[]];
let parcial: integer[][] = [[], [1]];
let profundo: integer[][][] = [[[]]];
