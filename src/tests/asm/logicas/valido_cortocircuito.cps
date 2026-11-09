function ruido(v: boolean): boolean {
    print("ruido");
    return v;
}
let t: boolean = true;
let f: boolean = false;
print(f && ruido(true));
print(t || ruido(false));
print(t && ruido(true));
print(f || ruido(false));
