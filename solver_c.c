/*
 * Sliding Puzzle Solver - C implementation
 * A* with Manhattan + Linear Conflict heuristic
 * Supports up to 5x5 (25 tiles)
 *
 * Compile: gcc -O2 -shared -fPIC -o libsolver.so solver_c.c
 */

#include <stdlib.h>
#include <string.h>
#include <stdint.h>

#define MAX_N 5
#define MAX_TILES 25
#define HASH_SIZE (1 << 22)  /* 4M buckets */
#define MAX_STATES (1 << 24) /* 16M states max */

/* State encoding: tiles stored as bytes, hash computed inline */

typedef struct {
    uint8_t tiles[MAX_TILES];  /* board state, row-major */
    uint8_t empty_pos;         /* index of empty tile */
    int32_t g;                 /* cost so far */
    int32_t f;                 /* g + h */
    int32_t parent;            /* index of parent state (-1 for root) */
    uint8_t move_dir;          /* direction taken from parent: 0=up,1=down,2=left,3=right */
} State;

typedef struct {
    uint8_t tiles[MAX_TILES];
    int32_t best_g;  /* best g value seen for this state */
} HashEntry;

static int g_size = 3;
static int g_n_tiles = 9;
static uint8_t g_goal[MAX_TILES];
static int8_t g_goal_row[MAX_TILES];  /* goal_pos[val] = row */
static int8_t g_goal_col[MAX_TILES];  /* goal_pos[val] = col */

/* Hash table for duplicate detection */
static HashEntry *g_hash_table = NULL;
static int g_hash_size = HASH_SIZE;

/* State pool */
static State *g_states = NULL;
static int g_state_count = 0;
static int g_max_states = MAX_STATES;

/* Open list (binary heap) */
static int32_t *g_open = NULL;  /* indices into g_states */
static int g_open_size = 0;
static int g_open_cap = MAX_STATES;

/* Direction deltas */
static const int dx[] = {-1, 1, 0, 0};  /* up, down, left, right */
static const int dy[] = {0, 0, -1, 1};

/* Result buffer */
static int g_result_moves[MAX_TILES * MAX_TILES];
static int g_result_count = 0;

static uint32_t hash_tiles(const uint8_t *tiles, int n) {
    uint32_t h = 5381;
    for (int i = 0; i < n; i++) {
        h = ((h << 5) + h) + tiles[i];
    }
    return h & (g_hash_size - 1);
}

static int tiles_equal(const uint8_t *a, const uint8_t *b, int n) {
    return memcmp(a, b, n) == 0;
}

/* Look up state in hash table. Returns pointer to entry, or NULL if not found.
   If found, sets *existing_g to the stored best_g. */
static HashEntry* hash_lookup(const uint8_t *tiles) {
    uint32_t h = hash_tiles(tiles, g_n_tiles);
    int probes = 0;
    while (probes < 8) {
        HashEntry *e = &g_hash_table[h];
        if (e->best_g < 0) {
            return e;  /* empty slot */
        }
        if (tiles_equal(e->tiles, tiles, g_n_tiles)) {
            return e;  /* found */
        }
        h = (h + 1) & (g_hash_size - 1);
        probes++;
    }
    return NULL;  /* table full or too many probes */
}

static int manhattan_lc(const uint8_t *tiles, int *out_empty_pos) {
    int md = 0;
    int lc = 0;
    int empty_pos = -1;
    int n = g_size;

    /* Row conflict tracking: for each row, collect (cur_col, goal_col) of tiles whose goal is in this row */
    int8_t row_c[MAX_N][MAX_N], row_g[MAX_N][MAX_N];
    int row_count[MAX_N] = {0};
    int8_t col_c[MAX_N][MAX_N], col_g[MAX_N][MAX_N];
    int col_count[MAX_N] = {0};

    for (int idx = 0; idx < g_n_tiles; idx++) {
        int val = tiles[idx];
        if (val == 0) {
            empty_pos = idx;
            continue;
        }
        int gr = g_goal_row[val];
        int gc = g_goal_col[val];
        int cr = idx / n;
        int cc = idx % n;
        int dr = cr - gr; if (dr < 0) dr = -dr;
        int dc = cc - gc; if (dc < 0) dc = -dc;
        md += dr + dc;

        if (cr == gr) {
            int cnt = row_count[cr];
            row_c[cr][cnt] = cc;
            row_g[cr][cnt] = gc;
            row_count[cr] = cnt + 1;
        }
        if (cc == gc) {
            int cnt = col_count[cc];
            col_c[cc][cnt] = cr;
            col_g[cc][cnt] = gr;
            col_count[cc] = cnt + 1;
        }
    }

    *out_empty_pos = empty_pos;

    /* Row linear conflicts */
    for (int r = 0; r < n; r++) {
        int cnt = row_count[r];
        for (int i = 0; i < cnt; i++) {
            for (int j = i + 1; j < cnt; j++) {
                if (row_c[r][i] < row_c[r][j] && row_g[r][i] > row_g[r][j]) {
                    lc += 2;
                }
            }
        }
    }

    /* Column linear conflicts */
    for (int c = 0; c < n; c++) {
        int cnt = col_count[c];
        for (int i = 0; i < cnt; i++) {
            for (int j = i + 1; j < cnt; j++) {
                if (col_c[c][i] < col_c[c][j] && col_g[c][i] > col_g[c][j]) {
                    lc += 2;
                }
            }
        }
    }

    return md + lc;
}

static void heap_push(int32_t state_idx) {
    g_open[g_open_size] = state_idx;
    int i = g_open_size;
    g_open_size++;

    /* sift up */
    while (i > 0) {
        int parent = (i - 1) / 2;
        if (g_states[g_open[i]].f < g_states[g_open[parent]].f) {
            int32_t tmp = g_open[i];
            g_open[i] = g_open[parent];
            g_open[parent] = tmp;
            i = parent;
        } else {
            break;
        }
    }
}

static int32_t heap_pop(void) {
    if (g_open_size == 0) return -1;
    int32_t result = g_open[0];
    g_open_size--;
    g_open[0] = g_open[g_open_size];

    /* sift down */
    int i = 0;
    while (1) {
        int left = 2 * i + 1;
        int right = 2 * i + 2;
        int smallest = i;
        if (left < g_open_size && g_states[g_open[left]].f < g_states[g_open[smallest]].f)
            smallest = left;
        if (right < g_open_size && g_states[g_open[right]].f < g_states[g_open[smallest]].f)
            smallest = right;
        if (smallest != i) {
            int32_t tmp = g_open[i];
            g_open[i] = g_open[smallest];
            g_open[smallest] = tmp;
            i = smallest;
        } else {
            break;
        }
    }
    return result;
}

/*
 * Main solve function.
 * board: flat array of size*size, 0 = empty
 * size: board dimension (3-5)
 * result_moves: output array of direction strings (0=up,1=down,2=left,3=right)
 * Returns: number of moves, or -1 if no solution, -2 if out of memory
 */
int solve_puzzle(const int *board, int size, int *result_moves) {
    g_size = size;
    g_n_tiles = size * size;
    g_state_count = 0;
    g_open_size = 0;

    /* Setup goal state */
    for (int i = 0; i < g_n_tiles; i++) {
        if (i < g_n_tiles - 1) {
            g_goal[i] = i + 1;
        } else {
            g_goal[i] = 0;
        }
    }
    for (int i = 0; i < g_n_tiles; i++) {
        int val = g_goal[i];
        g_goal_row[val] = i / size;
        g_goal_col[val] = i % size;
    }

    /* Allocate if needed */
    if (!g_states) g_states = (State*)malloc(sizeof(State) * MAX_STATES);
    if (!g_open) g_open = (int32_t*)malloc(sizeof(int32_t) * MAX_STATES);
    if (!g_hash_table) {
        g_hash_table = (HashEntry*)malloc(sizeof(HashEntry) * HASH_SIZE);
        for (int i = 0; i < HASH_SIZE; i++) g_hash_table[i].best_g = -1;
    } else {
        memset(g_hash_table, -1, sizeof(HashEntry) * HASH_SIZE);
    }

    if (!g_states || !g_open || !g_hash_table) return -2;

    /* Check if already solved */
    int is_goal = 1;
    for (int i = 0; i < g_n_tiles; i++) {
        if (board[i] != g_goal[i]) { is_goal = 0; break; }
    }
    if (is_goal) return 0;

    /* Initialize start state */
    State *start = &g_states[0];
    for (int i = 0; i < g_n_tiles; i++) start->tiles[i] = (uint8_t)board[i];
    int empty_pos;
    int h = manhattan_lc(start->tiles, &empty_pos);
    start->empty_pos = (uint8_t)empty_pos;
    start->g = 0;
    start->f = h;
    start->parent = -1;
    start->move_dir = 0;
    g_state_count = 1;

    /* Insert into hash */
    HashEntry *he = hash_lookup(start->tiles);
    if (he) {
        memcpy(he->tiles, start->tiles, g_n_tiles);
        he->best_g = 0;
    }

    heap_push(0);

    while (g_open_size > 0) {
        int32_t cur_idx = heap_pop();
        State *cur = &g_states[cur_idx];

        /* Check goal */
        if (memcmp(cur->tiles, g_goal, g_n_tiles) == 0) {
            /* Reconstruct path */
            g_result_count = 0;
            int32_t idx = cur_idx;
            while (g_states[idx].parent >= 0) {
                g_result_moves[g_result_count++] = g_states[idx].move_dir;
                idx = g_states[idx].parent;
            }
            /* Reverse */
            for (int i = 0; i < g_result_count / 2; i++) {
                int tmp = g_result_moves[i];
                g_result_moves[i] = g_result_moves[g_result_count - 1 - i];
                g_result_moves[g_result_count - 1 - i] = tmp;
            }
            /* Copy to output */
            for (int i = 0; i < g_result_count; i++) {
                result_moves[i] = g_result_moves[i];
            }
            return g_result_count;
        }

        int ex = cur->empty_pos / size;
        int ey = cur->empty_pos % size;

        for (int d = 0; d < 4; d++) {
            int nx = ex + dx[d];
            int ny = ey + dy[d];
            if (nx < 0 || nx >= size || ny < 0 || ny >= size) continue;

            /* Create new state */
            if (g_state_count >= MAX_STATES) return -2;

            State *ns = &g_states[g_state_count];
            memcpy(ns->tiles, cur->tiles, g_n_tiles);
            int old_idx = ex * size + ey;
            int new_idx = nx * size + ny;
            ns->tiles[old_idx] = ns->tiles[new_idx];
            ns->tiles[new_idx] = 0;
            ns->empty_pos = (uint8_t)new_idx;
            ns->g = cur->g + 1;
            ns->parent = cur_idx;
            ns->move_dir = d;

            /* Hash lookup */
            HashEntry *he = hash_lookup(ns->tiles);
            if (!he) continue;  /* table full */

            if (he->best_g >= 0 && he->best_g <= ns->g) continue;  /* already visited cheaper */

            memcpy(he->tiles, ns->tiles, g_n_tiles);
            he->best_g = ns->g;

            int h = manhattan_lc(ns->tiles, &empty_pos);
            ns->f = ns->g + h;

            g_state_count++;
            heap_push(g_state_count - 1);
        }
    }

    return -1;  /* no solution */
}

/* Helper to get the size needed for result buffer */
int get_max_moves(void) {
    return MAX_TILES * MAX_TILES;
}
