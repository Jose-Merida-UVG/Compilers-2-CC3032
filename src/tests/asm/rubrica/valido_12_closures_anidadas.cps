function contador(): integer {
  let n: integer = 0;
  function inc(): integer { n = n + 1; return n; }
  inc(); inc();
  return inc() * 10 + n;
}
print(contador());
function outer(x: integer): integer {
  let acc: integer = x;
  function mid(y: integer): integer {
    function leaf(z: integer): integer { acc = acc + z; return acc; }
    return leaf(y) + leaf(y);
  }
  return mid(3) + acc;
}
print(outer(1));
print(contador() + contador());
