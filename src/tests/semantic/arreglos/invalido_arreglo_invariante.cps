// Los arreglos son invariantes a cualquier profundidad: integer[] no entra
// en float[] aunque un integer suelto sí entre en un float. Ver
// _element_fits en semantic/types.py.
let nums: integer[] = [1, 2];
let flotantes: float[] = nums;
let matriz: integer[][] = [[1]];
let matrizf: float[][] = matriz;
