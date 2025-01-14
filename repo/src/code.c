#include <stdio.h>
#include <stdlib.h>
#include <time.h>
typedef long long ll;
int LEN = 42, LENDIV2 = 21;
const int MXW = 0xfffffff, SHF = 28;
typedef ll Bighex[100];

void add(Bighex a, Bighex b) {
	int jw = 0;
	for (int i = 0; i < LEN; ++i) {
		a[i] += b[i] + jw;
		jw = a[i] >> SHF;
		a[i] &= MXW;
	}
}

void sub(Bighex a, Bighex b) {
	int jw = 0;
	for (int i = 0; i < LEN; ++i) {
		a[i] -= b[i];
		if (a[i] < 0) {
			a[i] += (MXW + 1);
			--a[i + 1];
		}
	}
}

void sub1(Bighex a) {
	for (int i = 0; i < LEN; ++i) {
		--a[i];
		if (!~a[i]) a[i] = MXW;
		else break;
	}
}

void output(Bighex a) {
    for (int i = 36; ~i; --i) {
        if (i == 36) printf("%04llx", a[i]);
        else printf("%07llx", a[i]);
    }
    puts("");
}

void mul(Bighex a, Bighex b) {
	static Bighex c;
	for (int i = 0; i < LEN; ++i) c[i] = 0;
	for (int i = 0; i < LENDIV2; ++i) for (int j = 0; j < LENDIV2; ++j) c[i + j] += a[i] * b[j];
	for (int i = 0; i < LEN; ++i) a[i] = (c[i] & MXW), c[i + 1] += (c[i] >> SHF);
}

char greater_or_equal(Bighex a, Bighex b, int lst, int len, int low) {
	if (a[lst + len]) return 1;
	for (int i = len - 1; i >= low; --i) {
		if (a[lst + i] > b[i]) return 1;
		if (a[lst + i] < b[i]) return 0;
	}
	return 1;
}

void div2(Bighex a) {
	for (int i = 0; i < LEN - 1; ++i) a[i] = (a[i] >> 1) | ((a[i + 1] & 1) << (SHF - 1));
	a[LEN - 1] >>= 1;
}

void mul2(Bighex a) {
	for (int i = LEN - 1; i; --i) a[i] = ((a[i] << 1) & MXW) | (a[i - 1] >> (SHF - 1));
	a[0] <<= 1; a[0] &= MXW;
}
/*
void mod(Bighex a, Bighex b) {
	for (int i = 0; i < LENDIV2; ++i) b[i + LENDIV2] = b[i], b[i] = 0;
	int nlen = LEN - 1, nlow = LENDIV2 - 1;
	for (int i = 0; i <= LENDIV2 * SHF; ++i) {
		if (!b[nlen]) --nlen;
		if (nlow >= 0 && b[nlow]) --nlow;
		if (greater_or_equal(a, b, 0, nlen + 1, nlow + 1)) {
			for (int j = nlow + 1; j <= nlen; ++j) {
				a[j] -= b[j];
				if (a[j] < 0) {
					a[j] += MXW + 1;
					--a[j + 1];
				}
			}
		}
		if (i != LENDIV2 * SHF) div2(b);
	}
}*/

void divd(Bighex a, Bighex b, Bighex res) {
	for (int i = 0; i < LENDIV2; ++i) b[i + LENDIV2] = b[i], b[i] = 0;
	for (int i = 0; i < LEN; ++i) res[i] = 0;
	for (int i = 0; i <= LENDIV2 * SHF; ++i) {
		if (greater_or_equal(a, b, 0, LEN, 0)) {
			for (int j = 0; j <= LEN; ++j) {
				a[j] -= b[j];
				if (a[j] < 0) {
					a[j] += MXW + 1;
					--a[j + 1];
				}
			}
			res[0] |= 1;
		}
		if (i != LENDIV2 * SHF) div2(b), mul2(res);
	}
}

Bighex birm, re;

// Barrett Reduction algorithm
void mod(Bighex a, Bighex b) {
	// output(a);
	static Bighex q, qq, r1, r2, r3;
	for (int i = 0; i < LEN; ++i) q[i] = r1[i] = r2[i] = r3[i] = qq[i] = 0;
	for (int i = 18; i < LEN; ++i) q[i - 18] = a[i];
	mul(q, birm);
	for (int i = 20; i < LEN; ++i) qq[i - 20] = q[i];
	for (int i = 0; i < 20; ++i) r1[i] = a[i];
	for (int i = 0; i < LEN; ++i) r2[i] = qq[i];
	mul(r2, b);
	for (int i = 0; i < 20; ++i) r3[i] = r2[i];
	sub(r1, r3);
	if (greater_or_equal(r1, b, 0, LEN, 0)) sub(r1, b);
	for (int i = 0; i < LEN; ++i) a[i] = r1[i];
	// printf(":");
	// output(a);
	// printf("!");
	// output(b);
}

char is_odd(Bighex a) {
	return a[0] & 1;
}

char is_0(Bighex a) {
	for (int i = 0; i < LEN; ++i) if (a[i]) return 0;
	return 1;
}

char is_1(Bighex a) {
	if (a[0] != 1) return 0;
	for (int i = 1; i < LEN; ++i) if (a[i]) return 0;
	return 1;
}

char is_n_minus_1(Bighex a, Bighex n) {
	static Bighex na;
	for (int i = 0; i < LEN; ++i) na[i] = n[i];
	sub1(na);
	for (int i = 0; i < LEN; ++i) if (na[i] != a[i]) return 0;
	return 1;
}

void qpow(Bighex a, Bighex b, Bighex m, Bighex res) {
	if (is_0(b)) {
		for (int i = 0; i < LEN; ++i) res[i] = 0;
		res[0] = 1;
		return;
	}
	char odd = is_odd(b);
	div2(b);
	qpow(a, b, m, res);
	mul(res, res);
	mod(res, m);
	if (odd) {
		mul(res, a);
		mod(res, m);
	}
}

int tran(Bighex x) {
	// int val = 0;
	// for (int i = 1; ~i; --i) val = val * (MXW + 1) + x[i];
	// return val;
	return x[0];
}

int randomize() {
	if (RAND_MAX > (1 << 28)) return rand() % (1 << 28);
	else return (rand() * 11451 + rand() + 4) % (1 << 28);
}

char miller_rabin(Bighex n, int times, char debug) {
	for (int i = 0; i < LEN; ++i) re[i] = 0;
	re[38] = 1;
	divd(re, n, birm);
	static Bighex a, aa, v, x;
	char issuc = 1;
	for (int i = 0; i < LEN; ++i) a[i] = n[i];
	sub1(a); int b = 0;
	while (!is_odd(a)) div2(a), ++b;
	for (int i = 0; i < times; ++i) {
		x[0] = randomize();
		// x[0] = randomize() % 60000;
		if (x[0] < 2) x[0] = 2;
		for (int i = 0; i < LEN; ++i) aa[i] = a[i];
		qpow(x, aa, n, v);
		if (is_1(v) || is_n_minus_1(v, n)) {
			if (debug) {
				printf("Success: %d\n", tran(x));
			}
			continue;
		}
		char ok = 0;
		for (int j = 0; j < b; ++j) {
			mul(v, v);
			mod(v, n);
			if (is_n_minus_1(v, n)) {
				ok = 1;
				break;
			}
		}
		if (!ok) {
			if (debug) {
				printf("Failed: %d\n", tran(x));
				issuc = 0;
			}
			else return 0;
		}
		else {
			if (debug) {
				printf("Success: %d\n", tran(x));
			}
		}
	}
	return 1;
}

Bighex a, b;

void genRand(Bighex x) {
	ll vsum = 0;
	vsum = x[0] = (randomize() % (1 << 26)) * 4 + 3;
	for (int i = 1; i <= 17; ++i) x[i] = randomize(), vsum += x[i];
	x[18] = rand() % 64 + 64 * 3;
	while ((x[18] + vsum) % 3 == 0 || (x[18] + vsum) % 5 == 0) x[18] = rand() % 64 + 64 * 3;
}

int main(int argc, char **argv) {
	srand(time(NULL));
	genRand(a);
	while (!miller_rabin(a, 10, 0)) {
		genRand(a);
	}
	genRand(b);
	while (!miller_rabin(b, 10, 0)) {
		genRand(b);
	}
	LEN >>= 1;
    printf("Number A: ");
    output(a);
    printf("Number B: ");
    output(b);
	LEN <<= 1;
	mul(a, b);
	output(a);
	printf("Time used: %.3lfs\n", 1. * clock() / CLOCKS_PER_SEC);
	LEN <<= 1; LENDIV2 <<= 1;
	miller_rabin(a, 20, 1);
	return 0;
}