#include <stdlib.h>

static int global;

int main() {
  int *ptr = malloc(sizeof(int));
  assert(global > 0);
  return 0;
}
