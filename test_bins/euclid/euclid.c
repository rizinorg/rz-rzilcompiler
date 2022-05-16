#ifndef HEXAGON_BULD
#include <stdio.h>
#endif

typedef unsigned int ut32;
typedef int st32;

void euclid(ut32 a, ut32 b) {

  st32 rk = b, tk = 1, sk = 0, qk = 2;
  st32 rk_2, rk_1 = a;
  st32 sk_2, sk_1 = 1;
  st32 tk_2, tk_1 = 0;
  ut32 k = 2;

  for (; rk > 1; k++) {
    rk_2 = rk_1;
    rk_1 = rk;
    sk_2 = sk_1;
    sk_1 = sk;
    tk_2 = tk_1;
    tk_1 = tk;

    rk = rk_2 % rk_1;
    qk = (int) (rk_2/rk_1); // floor
    sk = sk_2 - (qk * sk_1);
    tk = tk_2 - (qk * tk_1);
  }
#ifndef HEXAGON_BULD
  printf("a = %d b = %d\n", a, b);
  printf("k = %d, qk = %d, sk = %d, tk=%d\n",k, qk, sk, tk);
#endif
}

int main() {
  euclid(63, 22);
  return 0;
}
