function fact(n: integer): integer { if (n <= 1) { return 1; } return n * fact(n - 1); }
function fib(n: integer): integer { if (n < 2) { return n; } return fib(n - 1) + fib(n - 2); }
function cuenta(n: integer): integer { if (n == 0) { return 0; } return 1 + cuenta(n - 1); }
function ack(m: integer, n: integer): integer { if (m == 0) { return n + 1; } if (n == 0) { return ack(m - 1, 1); } return ack(m - 1, ack(m, n - 1)); }
print(fact(10)); print(fib(15)); print(cuenta(5000)); print(ack(2, 3));
